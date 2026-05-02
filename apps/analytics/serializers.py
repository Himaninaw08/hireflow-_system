from rest_framework import serializers
from .models import (
    AnalyticsData, DashboardWidget, Report, MetricDefinition,
    CompanyMetrics, UserActivity
)

class AnalyticsDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsData
        fields = [
            'id', 'company', 'metric_type', 'metric_name', 'value',
            'date', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class DashboardWidgetSerializer(serializers.ModelSerializer):
    config = serializers.JSONField()
    
    class Meta:
        model = DashboardWidget
        fields = [
            'id', 'company', 'name', 'widget_type', 'position_x', 'position_y',
            'width', 'height', 'config', 'data_source', 'refresh_interval',
            'is_active', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

class DashboardWidgetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardWidget
        fields = [
            'name', 'widget_type', 'position_x', 'position_y', 'width', 'height',
            'config', 'data_source', 'refresh_interval', 'is_active'
        ]

class ReportSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'company', 'name', 'report_type', 'description',
            'filters', 'columns', 'group_by', 'sort_by', 'data',
            'file_path', 'format', 'is_template', 'is_scheduled',
            'schedule_frequency', 'last_generated', 'next_generation',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'data', 'file_path', 'last_generated', 'next_generation',
            'created_by', 'created_at', 'updated_at'
        ]

class ReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            'name', 'report_type', 'description', 'filters', 'columns',
            'group_by', 'sort_by', 'format', 'is_template', 'is_scheduled',
            'schedule_frequency'
        ]

class MetricDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetricDefinition
        fields = [
            'id', 'name', 'description', 'metric_type', 'data_source',
            'calculation_config', 'unit', 'is_public', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class CompanyMetricsSerializer(serializers.ModelSerializer):
    # Calculate derived metrics
    job_fill_rate = serializers.SerializerMethodField()
    application_conversion_rate = serializers.SerializerMethodField()
    interview_show_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = CompanyMetrics
        fields = [
            'company', 'total_jobs', 'active_jobs', 'draft_jobs', 'closed_jobs',
            'total_applications', 'pending_applications', 'screening_applications',
            'interview_applications', 'offered_applications', 'rejected_applications',
            'scheduled_interviews', 'completed_interviews', 'upcoming_interviews',
            'total_candidates', 'active_candidates', 'avg_time_to_hire',
            'offer_acceptance_rate', 'cost_per_hire', 'job_fill_rate',
            'application_conversion_rate', 'interview_show_rate', 'last_updated'
        ]
        read_only_fields = ['company', 'last_updated']

    def get_job_fill_rate(self, obj):
        if obj.total_jobs == 0:
            return 0
        filled_jobs = obj.closed_jobs  # Assuming closed means filled
        return round((filled_jobs / obj.total_jobs) * 100, 2)

    def get_application_conversion_rate(self, obj):
        if obj.total_applications == 0:
            return 0
        converted = obj.offered_applications + obj.rejected_applications
        return round((converted / obj.total_applications) * 100, 2)

    def get_interview_show_rate(self, obj):
        if obj.interview_applications == 0:
            return 0
        completed = obj.completed_interviews
        return round((completed / obj.interview_applications) * 100, 2)

class UserActivitySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserActivity
        fields = [
            'id', 'user', 'user_name', 'user_email', 'company', 'activity_type',
            'object_type', 'object_id', 'metadata', 'ip_address', 'user_agent',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class AnalyticsOverviewSerializer(serializers.Serializer):
    """Serializer for analytics overview data"""
    jobs_overview = serializers.DictField()
    applications_overview = serializers.DictField()
    interviews_overview = serializers.DictField()
    candidates_overview = serializers.DictField()
    performance_metrics = serializers.DictField()
    recent_activities = UserActivitySerializer(many=True)

class DashboardDataSerializer(serializers.Serializer):
    """Serializer for complete dashboard data"""
    metrics = CompanyMetricsSerializer()
    widgets = DashboardWidgetSerializer(many=True)
    overview = AnalyticsOverviewSerializer()
    recent_activities = UserActivitySerializer(many=True)

class ReportGenerationSerializer(serializers.Serializer):
    """Serializer for report generation requests"""
    report_id = serializers.IntegerField()
    format = serializers.ChoiceField(choices=['json', 'csv', 'excel', 'pdf'])
    filters = serializers.DictField(required=False)
    
    def validate_report_id(self, value):
        try:
            from .models import Report
            if not Report.objects.filter(id=value).exists():
                raise serializers.ValidationError("Report not found")
        except:
            raise serializers.ValidationError("Invalid report ID")
        return value

class MetricCalculationSerializer(serializers.Serializer):
    """Serializer for custom metric calculations"""
    metric_name = serializers.CharField(max_length=100)
    metric_type = serializers.ChoiceField(choices=['count', 'sum', 'average', 'min', 'max'])
    data_source = serializers.CharField(max_length=100)
    filters = serializers.DictField(required=False)
    date_range = serializers.DictField(required=False)
    
    def validate_data_source(self, value):
        valid_sources = ['jobs', 'applications', 'interviews', 'candidates', 'users']
        if value not in valid_sources:
            raise serializers.ValidationError(f"Invalid data source. Must be one of: {valid_sources}")
        return value
