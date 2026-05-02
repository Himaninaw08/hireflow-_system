from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import models
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Min, Max
from datetime import timedelta
import csv
import json
from apps.accounts.permissions import IsEmployer, IsAdmin
from apps.companies.models import Company
from apps.jobs.models import Job, Application
from apps.interviews.models import Interview
from apps.candidates.models import CandidateProfile
from .models import (
    AnalyticsData, DashboardWidget, Report, MetricDefinition,
    CompanyMetrics, UserActivity
)
from .serializers import (
    AnalyticsDataSerializer, DashboardWidgetSerializer, DashboardWidgetCreateSerializer,
    ReportSerializer, ReportCreateSerializer, MetricDefinitionSerializer,
    CompanyMetricsSerializer, UserActivitySerializer, AnalyticsOverviewSerializer,
    DashboardDataSerializer, ReportGenerationSerializer, MetricCalculationSerializer
)

class AnalyticsDataViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsEmployer]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['metric_type', 'date']
    search_fields = ['metric_name']
    ordering_fields = ['date', 'created_at']
    ordering = ['-date']

    def get_queryset(self):
        user = self.request.user
        user_companies = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role__in=['owner', 'recruiter'])
        ).distinct()
        return AnalyticsData.objects.filter(company__in=user_companies)

    def get_serializer_class(self):
        return AnalyticsDataSerializer

    @action(detail=False, methods=['post'])
    def generate_data(self, request):
        """Generate analytics data for a specific date range"""
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        metric_types = request.data.get('metric_types', [])
        
        if not start_date or not end_date:
            return Response(
                {'error': 'start_date and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = self.request.user
        company = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role='owner')
        ).first()
        
        if not company:
            return Response(
                {'error': 'Company not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate analytics data for the specified period
        current_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
        
        generated_data = []
        
        while current_date <= end_date_obj:
            if not metric_types or 'jobs' in metric_types:
                # Generate job metrics
                jobs_data = self._generate_job_metrics(company, current_date)
                for metric_name, value in jobs_data.items():
                    AnalyticsData.objects.update_or_create(
                        company=company,
                        metric_type='jobs',
                        metric_name=metric_name,
                        date=current_date,
                        defaults={'value': value}
                    )
            
            if not metric_types or 'applications' in metric_types:
                # Generate application metrics
                apps_data = self._generate_application_metrics(company, current_date)
                for metric_name, value in apps_data.items():
                    AnalyticsData.objects.update_or_create(
                        company=company,
                        metric_type='applications',
                        metric_name=metric_name,
                        date=current_date,
                        defaults={'value': value}
                    )
            
            current_date += timedelta(days=1)
        
        return Response({'message': 'Analytics data generated successfully'})

    def _generate_job_metrics(self, company, date):
        """Generate job metrics for a specific date"""
        jobs = Job.objects.filter(company=company)
        
        return {
            'total_jobs': jobs.count(),
            'active_jobs': jobs.filter(status='published').count(),
            'draft_jobs': jobs.filter(status='draft').count(),
            'closed_jobs': jobs.filter(status='closed').count(),
            'new_jobs': jobs.filter(created_at__date=date).count(),
        }

    def _generate_application_metrics(self, company, date):
        """Generate application metrics for a specific date"""
        applications = Application.objects.filter(job__company=company)
        
        return {
            'total_applications': applications.count(),
            'new_applications': applications.filter(applied_at__date=date).count(),
            'screening_applications': applications.filter(status='screening').count(),
            'interview_applications': applications.filter(status='interview').count(),
            'offered_applications': applications.filter(status='offered').count(),
            'rejected_applications': applications.filter(status='rejected').count(),
        }

class DashboardWidgetViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsEmployer]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['widget_type', 'is_active']
    search_fields = ['name']
    ordering_fields = ['position_y', 'position_x', 'name']
    ordering = ['position_y', 'position_x']

    def get_queryset(self):
        user = self.request.user
        user_companies = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role__in=['owner', 'recruiter'])
        ).distinct()
        return DashboardWidget.objects.filter(company__in=user_companies)

    def get_serializer_class(self):
        if self.action == 'create':
            return DashboardWidgetCreateSerializer
        return DashboardWidgetSerializer

    def perform_create(self, serializer):
        user = self.request.user
        company = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role='owner')
        ).first()
        
        if not company:
            raise permissions.PermissionDenied("You must have a company to create widgets")
        
        serializer.save(company=company, created_by=user)

    @action(detail=False, methods=['get'])
    def layout(self, request):
        """Get widget layout for dashboard"""
        user = self.request.user
        company = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role__in=['owner', 'recruiter'])
        ).first()
        
        widgets = DashboardWidget.objects.filter(company=company, is_active=True)
        
        layout = []
        for widget in widgets:
            layout.append({
                'id': widget.id,
                'name': widget.name,
                'type': widget.widget_type,
                'position': {'x': widget.position_x, 'y': widget.position_y},
                'size': {'width': widget.width, 'height': widget.height},
                'config': widget.config,
                'data_source': widget.data_source,
                'refresh_interval': widget.refresh_interval
            })
        
        return Response(layout)

    @action(detail=False, methods=['post'])
    def update_layout(self, request):
        """Update widget layout positions"""
        layout_data = request.data.get('layout', [])
        
        user = self.request.user
        company = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role__in=['owner', 'recruiter'])
        ).first()
        
        if not company:
            return Response(
                {'error': 'Company not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        updated_widgets = []
        for widget_data in layout_data:
            try:
                widget = DashboardWidget.objects.get(id=widget_data['id'], company=company)
                widget.position_x = widget_data['position']['x']
                widget.position_y = widget_data['position']['y']
                widget.width = widget_data['size']['width']
                widget.height = widget_data['size']['height']
                widget.save()
                updated_widgets.append(widget.id)
            except DashboardWidget.DoesNotExist:
                continue
        
        return Response({'updated_count': len(updated_widgets)})

class ReportViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsEmployer]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['report_type', 'format', 'is_template', 'is_scheduled']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'last_generated']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        user_companies = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role__in=['owner', 'recruiter'])
        ).distinct()
        return Report.objects.filter(company__in=user_companies)

    def get_serializer_class(self):
        if self.action == 'create':
            return ReportCreateSerializer
        return ReportSerializer

    def perform_create(self, serializer):
        user = self.request.user
        company = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role='owner')
        ).first()
        
        if not company:
            raise permissions.PermissionDenied("You must have a company to create reports")
        
        report = serializer.save(company=company, created_by=user)
        
        # Set next generation time if scheduled
        if report.is_scheduled and report.schedule_frequency:
            from datetime import datetime, timedelta
            if report.schedule_frequency == 'daily':
                report.next_generation = timezone.now() + timedelta(days=1)
            elif report.schedule_frequency == 'weekly':
                report.next_generation = timezone.now() + timedelta(weeks=1)
            elif report.schedule_frequency == 'monthly':
                report.next_generation = timezone.now() + timedelta(days=30)
            report.save()

    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """Generate report data"""
        report = self.get_object()
        
        try:
            data = self._generate_report_data(report)
            report.data = data
            report.last_generated = timezone.now()
            
            # Set next generation time if scheduled
            if report.is_scheduled and report.schedule_frequency:
                from datetime import timedelta
                if report.schedule_frequency == 'daily':
                    report.next_generation = timezone.now() + timedelta(days=1)
                elif report.schedule_frequency == 'weekly':
                    report.next_generation = timezone.now() + timedelta(weeks=1)
                elif report.schedule_frequency == 'monthly':
                    report.next_generation = timezone.now() + timedelta(days=30)
            
            report.save()
            
            return Response({'data': data, 'generated_at': report.last_generated})
        
        except Exception as e:
            return Response(
                {'error': f'Failed to generate report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _generate_report_data(self, report):
        """Generate report data based on report type"""
        company = report.company
        
        if report.report_type == 'jobs':
            return self._generate_jobs_report(company, report.filters)
        elif report.report_type == 'applications':
            return self._generate_applications_report(company, report.filters)
        elif report.report_type == 'interviews':
            return self._generate_interviews_report(company, report.filters)
        elif report.report_type == 'candidates':
            return self._generate_candidates_report(company, report.filters)
        elif report.report_type == 'pipeline':
            return self._generate_pipeline_report(company, report.filters)
        else:
            return {'error': 'Unsupported report type'}

    def _generate_jobs_report(self, company, filters):
        """Generate jobs report data"""
        jobs = Job.objects.filter(company=company)
        
        # Apply filters
        if filters.get('status'):
            jobs = jobs.filter(status=filters['status'])
        if filters.get('date_from'):
            jobs = jobs.filter(created_at__date__gte=filters['date_from'])
        if filters.get('date_to'):
            jobs = jobs.filter(created_at__date__lte=filters['date_to'])
        
        data = []
        for job in jobs:
            data.append({
                'id': job.id,
                'title': job.title,
                'status': job.status,
                'job_type': job.job_type,
                'experience_level': job.experience_level,
                'location': job.location,
                'views_count': job.views_count,
                'apply_count': job.apply_count,
                'created_at': job.created_at,
            })
        
        return {'jobs': data, 'total': len(data)}

    def _generate_applications_report(self, company, filters):
        """Generate applications report data"""
        applications = Application.objects.filter(job__company=company)
        
        # Apply filters
        if filters.get('status'):
            applications = applications.filter(status=filters['status'])
        if filters.get('date_from'):
            applications = applications.filter(applied_at__date__gte=filters['date_from'])
        if filters.get('date_to'):
            applications = applications.filter(applied_at__date__lte=filters['date_to'])
        
        data = []
        for app in applications:
            data.append({
                'id': app.id,
                'candidate': app.candidate.email,
                'job': app.job.title,
                'status': app.status,
                'applied_at': app.applied_at,
                'is_anonymous': app.is_anonymous,
            })
        
        return {'applications': data, 'total': len(data)}

    def _generate_interviews_report(self, company, filters):
        """Generate interviews report data"""
        interviews = Interview.objects.filter(job__company=company)
        
        # Apply filters
        if filters.get('status'):
            interviews = interviews.filter(status=filters['status'])
        if filters.get('date_from'):
            interviews = interviews.filter(scheduled_at__date__gte=filters['date_from'])
        if filters.get('date_to'):
            interviews = interviews.filter(scheduled_at__date__lte=filters['date_to'])
        
        data = []
        for interview in interviews:
            data.append({
                'id': interview.id,
                'candidate': interview.application.candidate.email,
                'job': interview.job.title,
                'interview_type': interview.interview_type,
                'status': interview.status,
                'scheduled_at': interview.scheduled_at,
                'interviewer': interview.interviewer.email,
            })
        
        return {'interviews': data, 'total': len(data)}

    def _generate_candidates_report(self, company, filters):
        """Generate candidates report data"""
        profiles = CandidateProfile.objects.filter(is_public=True)
        
        # Apply filters
        if filters.get('experience_level'):
            profiles = profiles.filter(experience_level=filters['experience_level'])
        if filters.get('location'):
            profiles = profiles.filter(location__icontains=filters['location'])
        
        data = []
        for profile in profiles:
            data.append({
                'id': profile.id,
                'candidate': profile.user.email,
                'headline': profile.headline,
                'experience_level': profile.experience_level,
                'location': profile.location,
                'profile_completion': profile.profile_completion_percentage,
                'skills': profile.skills,
            })
        
        return {'candidates': data, 'total': len(data)}

    def _generate_pipeline_report(self, company, filters):
        """Generate pipeline report data"""
        from apps.pipeline.models import PipelineStage, StageTransition
        
        stages = PipelineStage.objects.filter(pipeline__company=company)
        
        data = []
        for stage in stages:
            applications_count = stage.applications.count()
            avg_duration = StageTransition.objects.filter(
                to_stage=stage
            ).aggregate(Avg('duration_hours'))['duration_hours__avg'] or 0
            
            data.append({
                'stage_name': stage.name,
                'applications_count': applications_count,
                'average_duration_hours': round(avg_duration, 1),
                'color': stage.color,
            })
        
        return {'pipeline_stages': data, 'total': len(data)}

class MetricDefinitionViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view for metric definitions"""
    queryset = MetricDefinition.objects.filter(is_public=True)
    serializer_class = MetricDefinitionSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering = ['name']

class CompanyMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view for company metrics"""
    permission_classes = [permissions.IsAuthenticated, IsEmployer]
    serializer_class = CompanyMetricsSerializer

    def get_queryset(self):
        user = self.request.user
        user_companies = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role__in=['owner', 'recruiter'])
        ).distinct()
        return CompanyMetrics.objects.filter(company__in=user_companies)

    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get comprehensive analytics overview"""
        user = self.request.user
        company = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role__in=['owner', 'recruiter'])
        ).first()
        
        if not company:
            return Response(
                {'error': 'Company not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            metrics = CompanyMetrics.objects.get(company=company)
        except CompanyMetrics.DoesNotExist:
            metrics = CompanyMetrics.objects.create(company=company)
        
        # Get recent activities
        activities = UserActivity.objects.filter(company=company)[:10]
        
        # Generate overview data
        overview_data = {
            'jobs_overview': {
                'total': metrics.total_jobs,
                'active': metrics.active_jobs,
                'draft': metrics.draft_jobs,
                'closed': metrics.closed_jobs,
            },
            'applications_overview': {
                'total': metrics.total_applications,
                'pending': metrics.pending_applications,
                'screening': metrics.screening_applications,
                'interview': metrics.interview_applications,
                'offered': metrics.offered_applications,
                'rejected': metrics.rejected_applications,
            },
            'interviews_overview': {
                'scheduled': metrics.scheduled_interviews,
                'completed': metrics.completed_interviews,
                'upcoming': metrics.upcoming_interviews,
            },
            'candidates_overview': {
                'total': metrics.total_candidates,
                'active': metrics.active_candidates,
            },
            'performance_metrics': {
                'avg_time_to_hire': metrics.avg_time_to_hire,
                'offer_acceptance_rate': metrics.offer_acceptance_rate,
                'cost_per_hire': metrics.cost_per_hire,
            }
        }
        
        serializer = AnalyticsOverviewSerializer({
            'metrics': metrics,
            'overview': overview_data,
            'recent_activities': activities
        })
        
        return Response(serializer.data)

class UserActivityViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsEmployer]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['activity_type', 'object_type']
    search_fields = ['user__email', 'user__full_name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        user_companies = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role__in=['owner', 'recruiter'])
        ).distinct()
        return UserActivity.objects.filter(company__in=user_companies)

    def get_serializer_class(self):
        return UserActivitySerializer

    @action(detail=False, methods=['post'])
    def track(self, request):
        """Track user activity"""
        activity_type = request.data.get('activity_type')
        object_type = request.data.get('object_type')
        object_id = request.data.get('object_id')
        metadata = request.data.get('metadata', {})
        
        if not activity_type:
            return Response(
                {'error': 'activity_type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = self.request.user
        company = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role__in=['owner', 'recruiter'])
        ).first()
        
        if not company:
            return Response(
                {'error': 'Company not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        activity = UserActivity.objects.create(
            user=user,
            company=company,
            activity_type=activity_type,
            object_type=object_type,
            object_id=object_id,
            metadata=metadata,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'id': activity.id, 'tracked_at': activity.created_at})
