from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import models
from apps.accounts.permissions import IsEmployer, IsCompanyMember
from .models import Pipeline, PipelineStage, StageTransition, PipelineTemplate
from .serializers import (
    PipelineSerializer, PipelineCreateSerializer, PipelineStageSerializer,
    PipelineStageCreateSerializer, StageTransitionSerializer,
    PipelineTemplateSerializer
)

class PipelineViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['-is_default', 'name']

    def get_queryset(self):
        user = self.request.user
        from apps.companies.models import Company
        user_companies = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role__in=['owner', 'recruiter'])
        ).distinct()
        return Pipeline.objects.filter(company__in=user_companies)

    def get_serializer_class(self):
        if self.action == 'create':
            return PipelineCreateSerializer
        return PipelineSerializer

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set this pipeline as the default for the company"""
        pipeline = self.get_object()
        
        # Unset all other pipelines for this company
        Pipeline.objects.filter(company=pipeline.company).update(is_default=False)
        
        # Set this one as default
        pipeline.is_default = True
        pipeline.save()
        
        return Response({'message': 'Pipeline set as default'})

    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get pipeline analytics data"""
        pipeline = self.get_object()
        stages = pipeline.stages.all()
        
        analytics_data = []
        for stage in stages:
            # Get average time spent in stage
            transitions_out = StageTransition.objects.filter(from_stage=stage)
            avg_duration = transitions_out.aggregate(
                models.Avg('duration_hours')
            )['duration_hours__avg'] or 0
            
            analytics_data.append({
                'stage_name': stage.name,
                'stage_color': stage.color,
                'application_count': stage.application_count,
                'percentage_of_total': stage.percentage_of_total,
                'average_duration_hours': round(avg_duration, 1),
            })
        
        return Response(analytics_data)

    @action(detail=True, methods=['post'])
    def create_from_template(self, request, pk=None):
        """Create a new pipeline from a template"""
        template_id = request.data.get('template_id')
        new_name = request.data.get('name')
        
        if not template_id:
            return Response(
                {'error': 'template_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            template = PipelineTemplate.objects.get(id=template_id)
            new_pipeline = template.create_pipeline(
                company=self.get_object().company,
                name=new_name
            )
            serializer = self.get_serializer(new_pipeline)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except PipelineTemplate.DoesNotExist:
            return Response(
                {'error': 'Template not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class PipelineStageViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsCompanyMember]
    serializer_class = PipelineStageSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'order', 'created_at']
    ordering = ['order']

    def get_queryset(self):
        user = self.request.user
        from apps.companies.models import Company
        user_companies = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role__in=['owner', 'recruiter'])
        ).distinct()
        return PipelineStage.objects.filter(pipeline__company__in=user_companies)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PipelineStageCreateSerializer
        return PipelineStageSerializer

    def perform_create(self, serializer):
        pipeline_id = serializer.validated_data.get('pipeline')
        if not pipeline_id:
            pipeline_id = self.request.data.get('pipeline')
        
        # Verify user has access to this pipeline
        pipeline = Pipeline.objects.get(id=pipeline_id)
        user = self.request.user
        from apps.companies.models import Company
        user_companies = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role__in=['owner', 'recruiter'])
        ).distinct()
        
        if pipeline.company not in user_companies:
            raise permissions.PermissionDenied("You don't have access to this pipeline")
        
        # Set order to be last
        max_order = PipelineStage.objects.filter(pipeline=pipeline).aggregate(
            models.Max('order')
        )['order__max'] or 0
        
        serializer.save(order=max_order + 1)

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """Reorder stages within a pipeline"""
        pipeline_id = request.data.get('pipeline_id')
        stages_data = request.data.get('stages', [])  # List of {id, order}
        
        if not pipeline_id:
            return Response(
                {'error': 'pipeline_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify user has access to this pipeline
        try:
            pipeline = Pipeline.objects.get(id=pipeline_id)
        except Pipeline.DoesNotExist:
            return Response(
                {'error': 'Pipeline not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        user = self.request.user
        from apps.companies.models import Company
        user_companies = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role__in=['owner', 'recruiter'])
        ).distinct()
        
        if pipeline.company not in user_companies:
            raise permissions.PermissionDenied("You don't have access to this pipeline")
        
        # Update stage orders
        updated_stages = []
        for stage_data in stages_data:
            try:
                stage = PipelineStage.objects.get(
                    id=stage_data['id'],
                    pipeline=pipeline
                )
                stage.order = stage_data['order']
                stage.save()
                updated_stages.append(stage)
            except PipelineStage.DoesNotExist:
                continue
        
        serializer = PipelineStageSerializer(updated_stages, many=True)
        return Response(serializer.data)

class StageTransitionViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view for stage transitions (history)"""
    permission_classes = [permissions.IsAuthenticated, IsEmployer]
    serializer_class = StageTransitionSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['application', 'from_stage', 'to_stage', 'moved_by']
    ordering = ['-moved_at']

    def get_queryset(self):
        user = self.request.user
        from apps.companies.models import Company
        user_companies = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role__in=['owner', 'recruiter'])
        ).distinct()
        
        # Filter transitions for applications to user's company jobs
        from apps.jobs.models import Application
        user_applications = Application.objects.filter(
            job__company__in=user_companies
        )
        
        return StageTransition.objects.filter(
            application__in=user_applications
        )

class PipelineTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view for pipeline templates"""
    queryset = PipelineTemplate.objects.filter(is_public=True)
    serializer_class = PipelineTemplateSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering = ['name']
