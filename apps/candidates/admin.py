from django.contrib import admin
from .models import (
    CandidateProfile, CandidateExperience, CandidateEducation,
    CandidateProject, CandidateSkill
)

class CandidateSkillInline(admin.TabularInline):
    model = CandidateSkill
    extra = 0
    fields = ['name', 'level', 'years_of_experience', 'is_primary']

class CandidateExperienceInline(admin.TabularInline):
    model = CandidateExperience
    extra = 0
    fields = ['company', 'position', 'employment_type', 'start_date', 'end_date', 'is_current_position']

class CandidateEducationInline(admin.TabularInline):
    model = CandidateEducation
    extra = 0
    fields = ['institution', 'degree', 'field_of_study', 'education_level', 'start_date', 'end_date']

class CandidateProjectInline(admin.TabularInline):
    model = CandidateProject
    extra = 0
    fields = ['title', 'project_type', 'start_date', 'end_date', 'is_featured']

@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'email', 'headline', 'location', 'experience_level',
        'current_position', 'is_public', 'is_active_job_seeker',
        'profile_completion_percentage', 'created_at'
    ]
    list_filter = [
        'experience_level', 'employment_type', 'work_preference',
        'is_public', 'is_active_job_seeker', 'created_at'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'headline', 'bio', 'location', 'current_position', 'skills'
    ]
    ordering = ['-created_at']
    readonly_fields = ['profile_completion_percentage', 'created_at', 'updated_at']
    inlines = [
        CandidateSkillInline, CandidateExperienceInline,
        CandidateEducationInline, CandidateProjectInline
    ]
    
    fieldsets = (
        (None, {
            'fields': ('user', 'headline', 'bio', 'location')
        }),
        ('Links', {
            'fields': ('portfolio_url', 'github_url', 'linkedin_url', 'website_url')
        }),
        ('Professional', {
            'fields': (
                'experience_level', 'current_position', 'current_company',
                'employment_type', 'work_preference'
            )
        }),
        ('Preferences', {
            'fields': (
                'salary_expectation_min', 'salary_expectation_max', 'salary_currency',
                'available_from', 'open_to_relocation'
            )
        }),
        ('Skills & Info', {
            'fields': ('skills', 'languages', 'certifications')
        }),
        ('Documents', {
            'fields': ('resume_file', 'cover_letter_file')
        }),
        ('Settings', {
            'fields': ('is_public', 'is_active_job_seeker')
        }),
        ('Analytics', {
            'fields': ('profile_completion_percentage',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(CandidateExperience)
class CandidateExperienceAdmin(admin.ModelAdmin):
    list_display = [
        'profile', 'company', 'position', 'employment_type',
        'start_date', 'end_date', 'is_current_position', 'duration_years'
    ]
    list_filter = [
        'employment_type', 'is_current_position', 'start_date', 'created_at'
    ]
    search_fields = [
        'profile__user__email', 'company', 'position', 'description'
    ]
    ordering = ['-start_date']
    readonly_fields = ['created_at', 'updated_at', 'duration_years']

@admin.register(CandidateEducation)
class CandidateEducationAdmin(admin.ModelAdmin):
    list_display = [
        'profile', 'institution', 'degree', 'field_of_study',
        'education_level', 'start_date', 'end_date', 'gpa'
    ]
    list_filter = ['education_level', 'start_date', 'created_at']
    search_fields = [
        'profile__user__email', 'institution', 'degree', 'field_of_study'
    ]
    ordering = ['-start_date']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(CandidateProject)
class CandidateProjectAdmin(admin.ModelAdmin):
    list_display = [
        'profile', 'title', 'project_type', 'start_date',
        'end_date', 'is_featured', 'technologies'
    ]
    list_filter = ['project_type', 'is_featured', 'start_date', 'created_at']
    search_fields = [
        'profile__user__email', 'title', 'description', 'technologies'
    ]
    ordering = ['-is_featured', '-start_date']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(CandidateSkill)
class CandidateSkillAdmin(admin.ModelAdmin):
    list_display = [
        'profile', 'name', 'level', 'years_of_experience', 'is_primary'
    ]
    list_filter = ['level', 'is_primary', 'created_at']
    search_fields = ['profile__user__email', 'name']
    ordering = ['-is_primary', '-years_of_experience', 'name']
    readonly_fields = ['created_at']
