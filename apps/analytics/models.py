from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.companies.models import Company

User = get_user_model()

class AnalyticsData(models.Model):
    """Stores aggregated analytics data for fast dashboard loading"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='analytics_data')
    metric_type = models.CharField(max_length=50)  # 'jobs', 'applications', 'interviews', etc.
    metric_name = models.CharField(max_length=100)  # 'total_jobs', 'active_jobs', etc.
    value = models.JSONField()  # Can be number, object, or array
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['company', 'metric_type', 'metric_name', 'date']
        ordering = ['-date', 'metric_type', 'metric_name']
        indexes = [
            models.Index(fields=['company', 'metric_type', 'date']),
            models.Index(fields=['metric_type', 'date']),
        ]

    def __str__(self):
        return f"{self.company.name} - {self.metric_type}.{self.metric_name} ({self.date})"

class DashboardWidget(models.Model):
    """Customizable dashboard widgets"""
    WIDGET_TYPES = [
        ('metric_card', 'Metric Card'),
        ('line_chart', 'Line Chart'),
        ('bar_chart', 'Bar Chart'),
        ('pie_chart', 'Pie Chart'),
        ('table', 'Table'),
        ('list', 'List'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='dashboard_widgets')
    name = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    position_x = models.PositiveIntegerField(default=0)
    position_y = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(default=4)  # Grid units (1-12)
    height = models.PositiveIntegerField(default=3)
    
    # Widget configuration
    config = models.JSONField(default=dict)  # Chart settings, colors, etc.
    data_source = models.CharField(max_length=100)  # API endpoint or metric name
    refresh_interval = models.PositiveIntegerField(default=300)  # seconds
    
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position_y', 'position_x']
        unique_together = ['company', 'name']

    def __str__(self):
        return f"{self.company.name} - {self.name}"

class Report(models.Model):
    """Generated reports and report templates"""
    REPORT_TYPES = [
        ('jobs', 'Jobs Report'),
        ('applications', 'Applications Report'),
        ('interviews', 'Interviews Report'),
        ('candidates', 'Candidates Report'),
        ('pipeline', 'Pipeline Report'),
        ('custom', 'Custom Report'),
    ]

    FORMATS = [
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('pdf', 'PDF'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='reports')
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField(blank=True)
    
    # Report parameters
    filters = models.JSONField(default=dict)  # Date range, status filters, etc.
    columns = models.JSONField(default=list)  # Which columns to include
    group_by = models.CharField(max_length=100, blank=True)
    sort_by = models.CharField(max_length=100, blank=True)
    
    # Generated report data
    data = models.JSONField(default=dict)  # Actual report data
    file_path = models.CharField(max_length=500, blank=True)  # For file-based reports
    format = models.CharField(max_length=10, choices=FORMATS, default='json')
    
    is_template = models.BooleanField(default=False)
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(max_length=20, blank=True)  # daily, weekly, monthly
    last_generated = models.DateTimeField(null=True, blank=True)
    next_generation = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'report_type']),
            models.Index(fields=['is_scheduled', 'next_generation']),
        ]

    def __str__(self):
        return f"{self.company.name} - {self.name}"

class MetricDefinition(models.Model):
    """Predefined metrics for analytics"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    metric_type = models.CharField(max_length=50)  # count, sum, average, etc.
    data_source = models.CharField(max_length=100)  # Model name or API endpoint
    calculation_config = models.JSONField(default=dict)  # How to calculate the metric
    unit = models.CharField(max_length=20, blank=True)  # %, $, count, etc.
    is_public = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class CompanyMetrics(models.Model):
    """Real-time company metrics cache"""
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='metrics')
    
    # Job metrics
    total_jobs = models.PositiveIntegerField(default=0)
    active_jobs = models.PositiveIntegerField(default=0)
    draft_jobs = models.PositiveIntegerField(default=0)
    closed_jobs = models.PositiveIntegerField(default=0)
    
    # Application metrics
    total_applications = models.PositiveIntegerField(default=0)
    pending_applications = models.PositiveIntegerField(default=0)
    screening_applications = models.PositiveIntegerField(default=0)
    interview_applications = models.PositiveIntegerField(default=0)
    offered_applications = models.PositiveIntegerField(default=0)
    rejected_applications = models.PositiveIntegerField(default=0)
    
    # Interview metrics
    scheduled_interviews = models.PositiveIntegerField(default=0)
    completed_interviews = models.PositiveIntegerField(default=0)
    upcoming_interviews = models.PositiveIntegerField(default=0)
    
    # Candidate metrics
    total_candidates = models.PositiveIntegerField(default=0)
    active_candidates = models.PositiveIntegerField(default=0)
    
    # Performance metrics
    avg_time_to_hire = models.PositiveIntegerField(null=True, blank=True)  # days
    offer_acceptance_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cost_per_hire = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company.name} Metrics"

class UserActivity(models.Model):
    """Track user activity for analytics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='user_activities')
    
    activity_type = models.CharField(max_length=50)  # login, job_view, application_created, etc.
    object_type = models.CharField(max_length=50, blank=True)  # job, application, interview, etc.
    object_id = models.PositiveIntegerField(null=True, blank=True)
    
    metadata = models.JSONField(default=dict)  # Additional activity data
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['company', 'activity_type', 'created_at']),
            models.Index(fields=['activity_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.activity_type} ({self.created_at})"
