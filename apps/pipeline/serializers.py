from rest_framework import serializers
from .models import Pipeline, PipelineStage, StageTransition, PipelineTemplate

class PipelineStageSerializer(serializers.ModelSerializer):
    application_count = serializers.ReadOnlyField()
    percentage_of_total = serializers.ReadOnlyField()
    
    class Meta:
        model = PipelineStage
        fields = [
            'id', 'pipeline', 'name', 'order', 'color', 'description',
            'application_count', 'percentage_of_total', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class PipelineSerializer(serializers.ModelSerializer):
    stages = PipelineStageSerializer(many=True, read_only=True)
    stage_count = serializers.ReadOnlyField()
    total_applications = serializers.ReadOnlyField()
    
    class Meta:
        model = Pipeline
        fields = [
            'id', 'company', 'name', 'slug', 'is_default',
            'stage_count', 'total_applications', 'stages',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'company', 'slug', 'created_at', 'updated_at']

class PipelineCreateSerializer(serializers.ModelSerializer):
    stages = PipelineStageSerializer(many=True, required=False)
    
    class Meta:
        model = Pipeline
        fields = ['name', 'is_default', 'stages']

    def create(self, validated_data):
        stages_data = validated_data.pop('stages', [])
        user = self.context['request'].user
        
        # Get user's company
        from apps.companies.models import Company
        try:
            company = Company.objects.filter(owner=user).first()
            if not company:
                company = Company.objects.filter(members__user=user, members__role='owner').first()
            if not company:
                raise serializers.ValidationError("You must have a company to create pipelines")
        except Company.DoesNotExist:
            raise serializers.ValidationError("Company not found")

        pipeline = Pipeline.objects.create(
            company=company,
            **validated_data
        )
        
        # Create stages
        for i, stage_data in enumerate(stages_data):
            PipelineStage.objects.create(
                pipeline=pipeline,
                order=i,
                **stage_data
            )
        
        return pipeline

class StageTransitionSerializer(serializers.ModelSerializer):
    from_stage_name = serializers.CharField(source='from_stage.name', read_only=True)
    to_stage_name = serializers.CharField(source='to_stage.name', read_only=True)
    moved_by_name = serializers.CharField(source='moved_by.full_name', read_only=True)
    moved_by_email = serializers.CharField(source='moved_by.email', read_only=True)
    
    class Meta:
        model = StageTransition
        fields = [
            'id', 'application', 'from_stage', 'to_stage',
            'from_stage_name', 'to_stage_name', 'moved_by',
            'moved_by_name', 'moved_by_email', 'note',
            'duration_hours', 'moved_at'
        ]
        read_only_fields = ['id', 'moved_at']

class PipelineStageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PipelineStage
        fields = ['name', 'color', 'description']

class PipelineTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PipelineTemplate
        fields = ['id', 'name', 'description', 'stages_data', 'is_public', 'created_at']
        read_only_fields = ['id', 'created_at']

class ApplicationPipelineSerializer(serializers.ModelSerializer):
    """Serializer for applications with pipeline information"""
    pipeline_stage_name = serializers.CharField(source='pipeline_stage.name', read_only=True)
    pipeline_stage_color = serializers.CharField(source='pipeline_stage.color', read_only=True)
    pipeline_stage_order = serializers.IntegerField(source='pipeline_stage.order', read_only=True)
    
    class Meta:
        model = StageTransition
        fields = [
            'application', 'pipeline_stage', 'pipeline_stage_name',
            'pipeline_stage_color', 'pipeline_stage_order'
        ]
