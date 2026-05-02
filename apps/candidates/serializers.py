from rest_framework import serializers
from .models import (
    CandidateProfile, CandidateExperience, CandidateEducation, 
    CandidateProject, CandidateSkill
)

class CandidateSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateSkill
        fields = [
            'id', 'name', 'level', 'years_of_experience', 'is_primary', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class CandidateProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateProject
        fields = [
            'id', 'title', 'description', 'project_type', 'technologies',
            'live_url', 'github_url', 'start_date', 'end_date', 'is_featured',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class CandidateEducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateEducation
        fields = [
            'id', 'institution', 'degree', 'field_of_study', 'education_level',
            'start_date', 'end_date', 'gpa', 'description', 'achievements',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class CandidateExperienceSerializer(serializers.ModelSerializer):
    duration_years = serializers.ReadOnlyField()
    
    class Meta:
        model = CandidateExperience
        fields = [
            'id', 'company', 'position', 'employment_type', 'location',
            'start_date', 'end_date', 'is_current_position', 'description',
            'achievements', 'technologies_used', 'duration_years',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'duration_years']

class CandidateProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    email = serializers.ReadOnlyField()
    salary_range = serializers.ReadOnlyField()
    skill_details = CandidateSkillSerializer(many=True, read_only=True)
    experiences = CandidateExperienceSerializer(many=True, read_only=True)
    education = CandidateEducationSerializer(many=True, read_only=True)
    projects = CandidateProjectSerializer(many=True, read_only=True)
    
    class Meta:
        model = CandidateProfile
        fields = [
            'id', 'user', 'full_name', 'email', 'headline', 'bio', 'location',
            'portfolio_url', 'github_url', 'linkedin_url', 'website_url',
            'experience_level', 'current_position', 'current_company',
            'employment_type', 'work_preference', 'salary_expectation_min',
            'salary_expectation_max', 'salary_currency', 'salary_range',
            'available_from', 'open_to_relocation', 'skills', 'languages',
            'certifications', 'resume_file', 'cover_letter_file',
            'is_public', 'is_active_job_seeker', 'profile_completion_percentage',
            'skill_details', 'experiences', 'education', 'projects',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'profile_completion_percentage', 'created_at', 'updated_at'
        ]

class CandidateProfileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateProfile
        fields = [
            'headline', 'bio', 'location', 'portfolio_url', 'github_url',
            'linkedin_url', 'website_url', 'experience_level', 'current_position',
            'current_company', 'employment_type', 'work_preference',
            'salary_expectation_min', 'salary_expectation_max', 'salary_currency',
            'available_from', 'open_to_relocation', 'skills', 'languages',
            'certifications', 'is_public', 'is_active_job_seeker'
        ]

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

class CandidateProfilePublicSerializer(serializers.ModelSerializer):
    """Public version of candidate profile with limited information"""
    full_name = serializers.ReadOnlyField()
    salary_range = serializers.ReadOnlyField()
    skill_details = CandidateSkillSerializer(many=True, read_only=True)
    experiences = CandidateExperienceSerializer(many=True, read_only=True)
    education = CandidateEducationSerializer(many=True, read_only=True)
    projects = CandidateProjectSerializer(many=True, read_only=True)
    
    class Meta:
        model = CandidateProfile
        fields = [
            'id', 'full_name', 'headline', 'bio', 'location', 'portfolio_url',
            'github_url', 'linkedin_url', 'website_url', 'experience_level',
            'current_position', 'current_company', 'employment_type',
            'work_preference', 'salary_range', 'available_from',
            'open_to_relocation', 'skills', 'languages', 'certifications',
            'profile_completion_percentage', 'skill_details', 'experiences',
            'education', 'projects'
        ]
        read_only_fields = ['id', 'profile_completion_percentage']

class CandidateExperienceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateExperience
        fields = [
            'company', 'position', 'employment_type', 'location',
            'start_date', 'end_date', 'is_current_position', 'description',
            'achievements', 'technologies_used'
        ]

    def validate(self, attrs):
        if not attrs.get('is_current_position') and not attrs.get('end_date'):
            raise serializers.ValidationError("End date is required when not current position")
        
        if attrs.get('is_current_position') and attrs.get('end_date'):
            raise serializers.ValidationError("End date cannot be set for current position")
        
        return attrs

class CandidateEducationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateEducation
        fields = [
            'institution', 'degree', 'field_of_study', 'education_level',
            'start_date', 'end_date', 'gpa', 'description', 'achievements'
        ]

class CandidateProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateProject
        fields = [
            'title', 'description', 'project_type', 'technologies',
            'live_url', 'github_url', 'start_date', 'end_date', 'is_featured'
        ]

class CandidateSkillCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateSkill
        fields = ['name', 'level', 'years_of_experience', 'is_primary']

class CandidateProfileSearchSerializer(serializers.ModelSerializer):
    """Minimal serializer for search results"""
    full_name = serializers.ReadOnlyField()
    headline = serializers.ReadOnlyField()
    location = serializers.ReadOnlyField()
    experience_level = serializers.ReadOnlyField()
    current_position = serializers.ReadOnlyField()
    skills = serializers.ReadOnlyField()
    profile_completion_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = CandidateProfile
        fields = [
            'id', 'full_name', 'headline', 'location', 'experience_level',
            'current_position', 'skills', 'profile_completion_percentage'
        ]
