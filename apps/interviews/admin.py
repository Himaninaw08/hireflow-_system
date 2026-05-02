from django.contrib import admin
from .models import Interview, InterviewSlot, InterviewFeedback, InterviewTemplate

@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ['title', 'candidate', 'interviewer', 'job', 'interview_type', 'status', 'scheduled_at', 'duration_minutes']
    list_filter = ['status', 'interview_type', 'scheduled_at', 'created_at', 'job__company']
    search_fields = ['title', 'application__candidate__email', 'interviewer__email', 'job__title']
    ordering = ['-scheduled_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('application', 'interviewer', 'job', 'title', 'interview_type', 'status')
        }),
        ('Scheduling', {
            'fields': ('scheduled_at', 'duration_minutes', 'location', 'meeting_link', 'meeting_password')
        }),
        ('Details', {
            'fields': ('description', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(InterviewSlot)
class InterviewSlotAdmin(admin.ModelAdmin):
    list_display = ['interviewer', 'date', 'start_time', 'end_time', 'duration_minutes', 'max_interviews', 'is_booked', 'is_available']
    list_filter = ['date', 'is_booked', 'created_at']
    search_fields = ['interviewer__email', 'interviewer__full_name']
    ordering = ['date', 'start_time']
    readonly_fields = ['created_at']
    
    fieldsets = (
        (None, {
            'fields': ('interviewer', 'date', 'start_time', 'end_time')
        }),
        ('Settings', {
            'fields': ('duration_minutes', 'max_interviews', 'is_booked')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(InterviewFeedback)
class InterviewFeedbackAdmin(admin.ModelAdmin):
    list_display = ['interview', 'interviewer', 'overall_rating', 'recommendation', 'would_hire', 'created_at']
    list_filter = ['overall_rating', 'recommendation', 'would_hire', 'created_at']
    search_fields = ['interview__title', 'interviewer__email', 'strengths', 'weaknesses']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'average_rating']
    
    fieldsets = (
        (None, {
            'fields': ('interview', 'interviewer', 'overall_rating', 'recommendation')
        }),
        ('Ratings', {
            'fields': ('technical_skills', 'communication', 'problem_solving', 'cultural_fit')
        }),
        ('Feedback', {
            'fields': ('strengths', 'weaknesses', 'additional_notes')
        }),
        ('Decision', {
            'fields': ('would_hire', 'next_steps')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(InterviewTemplate)
class InterviewTemplateAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'interview_type', 'duration_minutes', 'is_public', 'created_at']
    list_filter = ['interview_type', 'is_public', 'created_at', 'company']
    search_fields = ['title', 'description', 'company__name']
    ordering = ['title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'company', 'interview_type', 'duration_minutes', 'is_public')
        }),
        ('Content', {
            'fields': ('questions', 'evaluation_criteria')
        }),
        ('Timestamps', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
