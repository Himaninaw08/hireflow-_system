from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.db import models
from apps.accounts.permissions import IsEmployer, IsRecruiter
from .models import Interview, InterviewSlot, InterviewFeedback, InterviewTemplate
from .serializers import (
    InterviewSerializer, InterviewCreateSerializer, InterviewDetailSerializer,
    InterviewSlotSerializer, InterviewSlotCreateSerializer,
    InterviewFeedbackSerializer, InterviewFeedbackCreateSerializer,
    InterviewTemplateSerializer, InterviewTemplateCreateSerializer
)

class InterviewViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsRecruiter]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'interview_type', 'application', 'interviewer', 'job']
    search_fields = ['title', 'application__candidate__email', 'job__title']
    ordering_fields = ['scheduled_at', 'created_at', 'status']
    ordering = ['scheduled_at']

    def get_queryset(self):
        user = self.request.user
        from apps.companies.models import Company
        user_companies = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role__in=['owner', 'recruiter'])
        ).distinct()
        
        # Filter interviews for user's company jobs
        return Interview.objects.filter(
            job__company__in=user_companies
        ).select_related('application', 'application__candidate', 'interviewer', 'job')

    def get_serializer_class(self):
        if self.action == 'create':
            return InterviewCreateSerializer
        elif self.action == 'retrieve':
            return InterviewDetailSerializer
        return InterviewSerializer

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm an interview"""
        interview = self.get_object()
        
        if interview.status != 'scheduled':
            return Response(
                {'error': 'Only scheduled interviews can be confirmed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        interview.status = 'confirmed'
        interview.save()
        
        # Create notification for candidate
        from apps.notifications.models import Notification
        Notification.objects.create(
            recipient=interview.application.candidate,
            title='Interview Confirmed',
            message=f'Your interview for {interview.job.title} has been confirmed',
            notification_type='interview',
            link=f'/candidate/interviews/{interview.id}'
        )
        
        serializer = self.get_serializer(interview)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark interview as completed"""
        interview = self.get_object()
        
        if interview.status not in ['scheduled', 'confirmed']:
            return Response(
                {'error': 'Interview must be scheduled or confirmed to be completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        interview.status = 'completed'
        interview.save()
        
        serializer = self.get_serializer(interview)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        """Reschedule an interview"""
        interview = self.get_object()
        new_datetime = request.data.get('scheduled_at')
        reason = request.data.get('reason', '')
        
        if not new_datetime:
            return Response(
                {'error': 'New scheduled_at time is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_datetime = interview.scheduled_at
        interview.scheduled_at = new_datetime
        interview.status = 'rescheduled'
        interview.save()
        
        # Create notification for candidate
        from apps.notifications.models import Notification
        Notification.objects.create(
            recipient=interview.application.candidate,
            title='Interview Rescheduled',
            message=f'Your interview for {interview.job.title} has been rescheduled',
            notification_type='interview',
            link=f'/candidate/interviews/{interview.id}'
        )
        
        serializer = self.get_serializer(interview)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an interview"""
        interview = self.get_object()
        reason = request.data.get('reason', '')
        
        if interview.status in ['completed', 'cancelled']:
            return Response(
                {'error': 'Cannot cancel completed or cancelled interviews'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        interview.status = 'cancelled'
        interview.save()
        
        # Create notification for candidate
        from apps.notifications.models import Notification
        Notification.objects.create(
            recipient=interview.application.candidate,
            title='Interview Cancelled',
            message=f'Your interview for {interview.job.title} has been cancelled',
            notification_type='interview',
            link=f'/candidate/interviews/{interview.id}'
        )
        
        serializer = self.get_serializer(interview)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get interviews scheduled for today"""
        today = timezone.now().date()
        interviews = self.get_queryset().filter(scheduled_at__date=today)
        serializer = self.get_serializer(interviews, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming interviews"""
        now = timezone.now()
        interviews = self.get_queryset().filter(scheduled_at__gt=now, status__in=['scheduled', 'confirmed'])
        serializer = self.get_serializer(interviews, many=True)
        return Response(serializer.data)

class InterviewSlotViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsRecruiter]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['interviewer', 'date', 'is_booked']
    search_fields = ['interviewer__email', 'interviewer__full_name']
    ordering_fields = ['date', 'start_time', 'created_at']
    ordering = ['date', 'start_time']

    def get_queryset(self):
        user = self.request.user
        from apps.companies.models import Company
        user_companies = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role__in=['owner', 'recruiter'])
        ).distinct()
        
        # Filter slots for interviewers in user's company
        return InterviewSlot.objects.filter(
            interviewer__in=CustomUser.objects.filter(
                models.Q(companies__in=user_companies) |
                models.Q(company_memberships__company__in=user_companies)
            ).distinct()
        )

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return InterviewSlotCreateSerializer
        return InterviewSlotSerializer

    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get available interview slots"""
        date_param = request.query_params.get('date')
        interviewer_id = request.query_params.get('interviewer')
        
        queryset = self.get_queryset().filter(is_available=True)
        
        if date_param:
            queryset = queryset.filter(date=date_param)
        
        if interviewer_id:
            queryset = queryset.filter(interviewer_id=interviewer_id)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class InterviewFeedbackViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsRecruiter]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['interview', 'interviewer', 'recommendation', 'would_hire']
    search_fields = ['interview__title', 'interviewer__email', 'strengths', 'weaknesses']
    ordering_fields = ['created_at', 'overall_rating']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        from apps.companies.models import Company
        user_companies = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role__in=['owner', 'recruiter'])
        ).distinct()
        
        # Filter feedback for interviews in user's company
        return InterviewFeedback.objects.filter(
            interview__job__company__in=user_companies
        ).select_related('interview', 'interviewer')

    def get_serializer_class(self):
        if self.action == 'create':
            return InterviewFeedbackCreateSerializer
        return InterviewFeedbackSerializer

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(interviewer=user)

class InterviewTemplateViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsRecruiter]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['interview_type', 'company', 'is_public']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'created_at']
    ordering = ['title']

    def get_queryset(self):
        user = self.request.user
        from apps.companies.models import Company
        user_companies = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role__in=['owner', 'recruiter'])
        ).distinct()
        
        return InterviewTemplate.objects.filter(
            models.Q(company__in=user_companies) | models.Q(is_public=True)
        ).distinct()

    def get_serializer_class(self):
        if self.action == 'create':
            return InterviewTemplateCreateSerializer
        return InterviewTemplateSerializer

    def perform_create(self, serializer):
        user = self.request.user
        from apps.companies.models import Company
        user_company = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role='owner')
        ).first()
        
        if not user_company:
            raise permissions.PermissionDenied("You must have a company to create templates")
        
        serializer.save(created_by=user, company=user_company)
