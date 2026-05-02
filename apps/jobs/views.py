from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.db import models
from apps.accounts.permissions import IsRecruiter, IsOwnerOrReadOnly
from .models import Job, Application, Tag
from .serializers import (
    JobSerializer, JobCreateSerializer, JobDetailSerializer,
    ApplicationSerializer, ApplicationCreateSerializer, TagSerializer
)
from .filters import JobFilter

class JobViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = JobFilter
    search_fields = ['title', 'description', 'location', 'company__name']
    ordering_fields = ['created_at', 'salary_min', 'views_count', 'apply_count']
    ordering = ['-created_at']

    def create(self, request, *args, **kwargs):
        print("USER:", request.user)
        print("ROLE:", request.user.role)  
        print("DATA:", request.data)
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("ERRORS:", serializer.errors)  # ← exact error here
        return super().create(request, *args, **kwargs)
        
    def get_queryset(self):
        queryset = Job.objects.filter(status='published')
        
        # If user is authenticated, show their company's jobs regardless of status
        if self.request.user.is_authenticated:
            from apps.companies.models import Company
            user_companies = Company.objects.filter(
                models.Q(owner=self.request.user) | 
                models.Q(members__user=self.request.user)
            ).distinct()
            queryset = Job.objects.filter(
                models.Q(company__in=user_companies) | 
                models.Q(status='published')
            ).distinct()
        
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return JobCreateSerializer
        elif self.action == 'retrieve':
            return JobDetailSerializer
        return JobSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'publish', 'pause', 'duplicate']:
            return [permissions.IsAuthenticated(), IsRecruiter()]
        return [permission() for permission in self.permission_classes]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment views count for public jobs
        if instance.status == 'published':
            instance.increment_views()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        job = self.get_object()
        if job.status == 'published':
            return Response(
                {'error': 'Job is already published'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job.status = 'published'
        job.save()
        serializer = self.get_serializer(job)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        job = self.get_object()
        if job.status != 'published':
            return Response(
                {'error': 'Only published jobs can be paused'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job.status = 'paused'
        job.save()
        serializer = self.get_serializer(job)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        original_job = self.get_object()
        
        # Create duplicate
        new_job = Job.objects.create(
            company=original_job.company,
            created_by=request.user,
            title=f"{original_job.title} (Copy)",
            description=original_job.description,
            requirements=original_job.requirements,
            job_type=original_job.job_type,
            experience_level=original_job.experience_level,
            location=original_job.location,
            salary_min=original_job.salary_min,
            salary_max=original_job.salary_max,
            currency=original_job.currency,
            skills_required=original_job.skills_required,
            is_anonymous_apply=original_job.is_anonymous_apply,
            status='draft'
        )
        
        serializer = self.get_serializer(new_job)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        job = self.get_object()
        
        if job.status != 'published':
            return Response(
                {'error': 'Job is not accepting applications'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if job.is_expired:
            return Response(
                {'error': 'Job has expired'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ApplicationCreateSerializer(
            data=request.data,
            context={'job': job, 'request': request}
        )
        
        if serializer.is_valid():
            application = serializer.save()
            response_data = ApplicationSerializer(application).data
            
            if serializer.validated_data.get('duplicate_warning'):
                response_data['warning'] = 'You have recently applied to this company'
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.role in ['employer', 'recruiter']:
            # Employers see applications for their company's jobs
            from apps.companies.models import Company
            user_companies = Company.objects.filter(
                models.Q(owner=user) | 
                models.Q(members__user=user, members__role__in=['owner', 'recruiter'])
            ).distinct()
            return Application.objects.filter(job__company__in=user_companies)
        else:
            # Candidates see only their own applications
            return Application.objects.filter(candidate=user)

    @action(detail=False, methods=['get'])
    def mine(self, request):
        """Get current user's applications (candidates only)"""
        if request.user.role != 'candidate':
            return Response(
                {'error': 'This endpoint is for candidates only'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        applications = Application.objects.filter(candidate=request.user)
        serializer = self.get_serializer(applications, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def stage(self, request, pk=None):
        """Move application to a different stage"""
        application = self.get_object()
        new_stage_id = request.data.get('stage_id')
        
        if not new_stage_id:
            return Response(
                {'error': 'stage_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from apps.pipeline.models import PipelineStage
            new_stage = PipelineStage.objects.get(id=new_stage_id)
        except PipelineStage.DoesNotExist:
            return Response(
                {'error': 'Stage not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        old_stage = application.pipeline_stage
        application.pipeline_stage = new_stage
        application.save()
        
        # Create stage transition record
        from apps.pipeline.models import StageTransition
        StageTransition.objects.create(
            application=application,
            from_stage=old_stage,
            to_stage=new_stage,
            moved_by=request.user,
            note=request.data.get('note', '')
        )
        
        # Create notification for candidate
        from apps.notifications.models import Notification
        Notification.objects.create(
            recipient=application.candidate,
            title='Application Status Updated',
            message=f'Your application for {application.job.title} has been moved to {new_stage.name}',
            notification_type='application',
            link=f'/employer/candidates/{application.candidate.id}'
        )
        
        serializer = self.get_serializer(application)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject an application"""
        application = self.get_object()
        reason = request.data.get('rejection_reason', '')
        in_talent_pool = request.data.get('in_talent_pool', False)
        
        application.status = 'rejected'
        application.rejection_reason = reason
        application.in_talent_pool = in_talent_pool
        application.save()
        
        # Create notification for candidate
        from apps.notifications.models import Notification
        Notification.objects.create(
            recipient=application.candidate,
            title='Application Update',
            message=f'Your application for {application.job.title} has been rejected',
            notification_type='application',
            link=f'/candidate/applications'
        )
        
        return Response({'message': 'Application rejected successfully'})

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """Get application timeline"""
        application = self.get_object()
        from apps.pipeline.models import StageTransition
        
        transitions = StageTransition.objects.filter(application=application).order_by('moved_at')
        
        timeline_data = []
        for transition in transitions:
            timeline_data.append({
                'stage': transition.to_stage.name if transition.to_stage else 'Applied',
                'moved_by': transition.moved_by.full_name or transition.moved_by.email,
                'moved_at': transition.moved_at,
                'note': transition.note
            })
        
        return Response(timeline_data)

class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        from apps.companies.models import Company
        user_companies = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user)
        ).distinct()
        return Tag.objects.filter(company__in=user_companies)
