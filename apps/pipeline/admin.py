from django.contrib import admin
from .models import Pipeline, PipelineStage, StageTransition, PipelineTemplate

class PipelineStageInline(admin.TabularInline):
    model = PipelineStage
    extra = 0
    fields = ['name', 'order', 'color', 'description']
    ordering = ['order']

@admin.register(Pipeline)
class PipelineAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'is_default', 'stage_count', 'total_applications', 'created_at']
    list_filter = ['is_default', 'created_at', 'company']
    search_fields = ['name', 'company__name']
    ordering = ['-is_default', 'name']
    readonly_fields = ['slug', 'stage_count', 'total_applications', 'created_at', 'updated_at']
    inlines = [PipelineStageInline]
    
    fieldsets = (
        (None, {
            'fields': ('company', 'name', 'slug', 'is_default')
        }),
        ('Analytics', {
            'fields': ('stage_count', 'total_applications'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PipelineStage)
class PipelineStageAdmin(admin.ModelAdmin):
    list_display = ['name', 'pipeline', 'order', 'color', 'application_count', 'percentage_of_total']
    list_filter = ['pipeline', 'created_at']
    search_fields = ['name', 'pipeline__name']
    ordering = ['pipeline', 'order']
    readonly_fields = ['application_count', 'percentage_of_total', 'created_at']
    
    fieldsets = (
        (None, {
            'fields': ('pipeline', 'name', 'order', 'color')
        }),
        ('Details', {
            'fields': ('description',)
        }),
        ('Analytics', {
            'fields': ('application_count', 'percentage_of_total'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(StageTransition)
class StageTransitionAdmin(admin.ModelAdmin):
    list_display = ['application', 'from_stage', 'to_stage', 'moved_by', 'duration_hours', 'moved_at']
    list_filter = ['to_stage', 'moved_at', 'moved_by']
    search_fields = ['application__candidate__email', 'application__job__title']
    ordering = ['-moved_at']
    readonly_fields = ['moved_at']
    
    fieldsets = (
        (None, {
            'fields': ('application', 'from_stage', 'to_stage', 'moved_by')
        }),
        ('Details', {
            'fields': ('note', 'duration_hours')
        }),
        ('Timestamps', {
            'fields': ('moved_at',)
        }),
    )

@admin.register(PipelineTemplate)
class PipelineTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_public', 'created_at']
    list_filter = ['is_public', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at']
