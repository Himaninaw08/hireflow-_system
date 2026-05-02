from django.contrib import admin
from .models import (
    AnalyticsData, DashboardWidget, Report, MetricDefinition,
    CompanyMetrics, UserActivity
)

@admin.register(AnalyticsData)
class AnalyticsDataAdmin(admin.ModelAdmin):
    list_display = ['company', 'metric_type', 'metric_name', 'date', 'created_at']
    list_filter = ['metric_type', 'company', 'date', 'created_at']
    search_fields = ['company__name', 'metric_name']
    ordering = ['-date', 'company', 'metric_type']
    readonly_fields = ['created_at']

@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = [
        'company', 'name', 'widget_type', 'position_x', 'position_y',
        'width', 'height', 'is_active', 'created_at'
    ]
    list_filter = ['widget_type', 'is_active', 'created_at', 'company']
    search_fields = ['name', 'company__name']
    ordering = ['company', 'position_y', 'position_x']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        'company', 'name', 'report_type', 'format', 'is_template',
        'is_scheduled', 'last_generated', 'created_at'
    ]
    list_filter = [
        'report_type', 'format', 'is_template', 'is_scheduled',
        'created_at', 'company'
    ]
    search_fields = ['name', 'description', 'company__name']
    ordering = ['-created_at']
    readonly_fields = [
        'data', 'file_path', 'last_generated', 'next_generation',
        'created_at', 'updated_at'
    ]

@admin.register(MetricDefinition)
class MetricDefinitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'metric_type', 'data_source', 'unit', 'is_public', 'created_at']
    list_filter = ['metric_type', 'data_source', 'is_public', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at']

@admin.register(CompanyMetrics)
class CompanyMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'company', 'total_jobs', 'active_jobs', 'total_applications',
        'scheduled_interviews', 'avg_time_to_hire', 'last_updated'
    ]
    list_filter = ['last_updated', 'company']
    search_fields = ['company__name']
    ordering = ['company']
    readonly_fields = ['last_updated']

    fieldsets = (
        ('Job Metrics', {
            'fields': (
                'total_jobs', 'active_jobs', 'draft_jobs', 'closed_jobs'
            )
        }),
        ('Application Metrics', {
            'fields': (
                'total_applications', 'pending_applications', 'screening_applications',
                'interview_applications', 'offered_applications', 'rejected_applications'
            )
        }),
        ('Interview Metrics', {
            'fields': (
                'scheduled_interviews', 'completed_interviews', 'upcoming_interviews'
            )
        }),
        ('Candidate Metrics', {
            'fields': (
                'total_candidates', 'active_candidates'
            )
        }),
        ('Performance Metrics', {
            'fields': (
                'avg_time_to_hire', 'offer_acceptance_rate', 'cost_per_hire'
            )
        }),
        ('Timestamps', {
            'fields': ('last_updated',),
            'classes': ('collapse',)
        }),
    )

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'company', 'activity_type', 'object_type', 'object_id',
        'created_at'
    ]
    list_filter = [
        'activity_type', 'object_type', 'company', 'created_at'
    ]
    search_fields = [
        'user__email', 'user__full_name', 'company__name', 'metadata'
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at']

    fieldsets = (
        (None, {
            'fields': ('user', 'company', 'activity_type')
        }),
        ('Object Details', {
            'fields': ('object_type', 'object_id')
        }),
        ('Additional Info', {
            'fields': ('metadata', 'ip_address', 'user_agent')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
