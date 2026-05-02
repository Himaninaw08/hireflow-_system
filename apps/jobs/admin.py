from django.contrib import admin
from .models import Job, Application, Tag

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'job_type', 'experience_level', 'status', 'views_count', 'apply_count', 'created_at']
    list_filter = ['status', 'job_type', 'experience_level', 'created_at']
    search_fields = ['title', 'description', 'company__name']
    ordering = ['-created_at']
    readonly_fields = ['slug', 'views_count', 'apply_count', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('company', 'created_by', 'title', 'slug')
        }),
        ('Job Details', {
            'fields': ('description', 'requirements', 'job_type', 'experience_level', 'location')
        }),
        ('Compensation', {
            'fields': ('salary_min', 'salary_max', 'currency')
        }),
        ('Settings', {
            'fields': ('skills_required', 'status', 'is_anonymous_apply', 'expires_at')
        }),
        ('Analytics', {
            'fields': ('views_count', 'apply_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'job', 'status', 'is_anonymous', 'applied_at', 'updated_at']
    list_filter = ['status', 'is_anonymous', 'in_talent_pool', 'applied_at']
    search_fields = ['candidate__email', 'job__title', 'job__company__name']
    ordering = ['-applied_at']
    readonly_fields = ['applied_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('job', 'candidate', 'status')
        }),
        ('Application Details', {
            'fields': ('resume', 'cover_letter', 'is_anonymous')
        }),
        ('Pipeline', {
            'fields': ('pipeline_stage', 'rejection_reason', 'in_talent_pool')
        }),
        ('Timestamps', {
            'fields': ('applied_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'color', 'application_count']
    list_filter = ['company', 'created_at']
    search_fields = ['name', 'company__name']
    ordering = ['name']
    readonly_fields = ['created_at']
    
    def application_count(self, obj):
        return obj.applications.count()
    application_count.short_description = 'Applications'
