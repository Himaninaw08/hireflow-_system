from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from apps.accounts.permissions import IsOwnerOrReadOnly, IsEmployer
from .models import Company, CompanyMember
from .serializers import (
    CompanySerializer, CompanyCreateSerializer, CompanyDetailSerializer,
    CompanyMemberSerializer
)

class CompanyViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description', 'industry']
    ordering_fields = ['name', 'created_at']
    filterset_fields = ['industry', 'company_size', 'subscription_tier']

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin']:
            return Company.objects.all()
        else:
            # Users can only see their own companies
            return Company.objects.filter(owner=user) | Company.objects.filter(members__user=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return CompanyCreateSerializer
        elif self.action == 'retrieve':
            return CompanyDetailSerializer
        return CompanySerializer

    @action(detail=False, methods=['get'])
    def my_companies(self, request):
        """Get companies for the current user"""
        user = request.user
        companies = Company.objects.filter(owner=user) | Company.objects.filter(members__user=user)
        companies = companies.distinct()
        
        # Add member count to each company
        for company in companies:
            company.members_count = CompanyMember.objects.filter(company=company).count()
        
        serializer = CompanyDetailSerializer(companies, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        company = self.get_object()
        if company.owner != request.user and not company.members.filter(user=request.user, role='owner').exists():
            return Response(
                {'error': 'Only company owners can add members'},
                status=status.HTTP_403_FORBIDDEN
            )

        email = request.data.get('email')
        role = request.data.get('role')
        
        if not email or not role:
            return Response(
                {'error': 'Email and role are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from apps.accounts.models import CustomUser
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'User with this email does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )

        if CompanyMember.objects.filter(company=company, user=user).exists():
            return Response(
                {'error': 'User is already a member of this company'},
                status=status.HTTP_400_BAD_REQUEST
            )

        member = CompanyMember.objects.create(
            company=company,
            user=user,
            role=role
        )
        
        serializer = CompanyMemberSerializer(member)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'])
    def remove_member(self, request, pk=None):
        company = self.get_object()
        member_id = request.data.get('member_id')
        
        if company.owner != request.user and not company.members.filter(user=request.user, role='owner').exists():
            return Response(
                {'error': 'Only company owners can remove members'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            member = CompanyMember.objects.get(id=member_id, company=company)
            if member.role == 'owner':
                return Response(
                    {'error': 'Cannot remove company owner'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            member.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CompanyMember.DoesNotExist:
            return Response(
                {'error': 'Member not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        company = self.get_object()
        members = company.members.all()
        serializer = CompanyMemberSerializer(members, many=True)
        return Response(serializer.data)
