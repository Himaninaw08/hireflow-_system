from rest_framework import serializers
from .models import Interview, InterviewSlot, InterviewFeedback, InterviewTemplate

class InterviewSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='application.candidate.full_name', read_only=True)
    candidate_email = serializers.CharField(source='application.candidate.email', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    interviewer_name = serializers.CharField(source='interviewer.full_name', read_only=True)
    is_past = serializers.ReadOnlyField()
    is_today = serializers.ReadOnlyField()
    end_time = serializers.ReadOnlyField()
    
    class Meta:
        model = Interview
        fields = [
            'id', 'application', 'candidate_name', 'candidate_email',
            'interviewer', 'interviewer_name', 'job', 'job_title',
            'title', 'interview_type', 'status', 'scheduled_at',
            'duration_minutes', 'location', 'meeting_link', 'meeting_password',
            'description', 'notes', 'created_by', 'is_past', 'is_today',
            'end_time', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

class InterviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interview
        fields = [
            'application', 'interviewer', 'title', 'interview_type',
            'scheduled_at', 'duration_minutes', 'location', 'meeting_link',
            'meeting_password', 'description', 'notes'
        ]

    def validate_scheduled_at(self, value):
        from django.utils import timezone
        if value < timezone.now():
            raise serializers.ValidationError("Interview cannot be scheduled in the past")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        
        # Auto-set job from application
        application = validated_data['application']
        validated_data['job'] = application.job
        
        return super().create(validated_data)

class InterviewSlotSerializer(serializers.ModelSerializer):
    interviewer_name = serializers.CharField(source='interviewer.full_name', read_only=True)
    is_available = serializers.ReadOnlyField()
    time_range = serializers.ReadOnlyField()
    
    class Meta:
        model = InterviewSlot
        fields = [
            'id', 'interviewer', 'interviewer_name', 'date', 'start_time',
            'end_time', 'duration_minutes', 'max_interviews', 'is_booked',
            'is_available', 'time_range', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class InterviewSlotCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewSlot
        fields = [
            'date', 'start_time', 'end_time', 'duration_minutes', 'max_interviews'
        ]

    def validate(self, attrs):
        start_time = attrs['start_time']
        end_time = attrs['end_time']
        
        if end_time <= start_time:
            raise serializers.ValidationError("End time must be after start time")
        
        # Check duration
        from datetime import datetime, time
        start_dt = datetime.combine(attrs['date'], start_time)
        end_dt = datetime.combine(attrs['date'], end_time)
        duration = (end_dt - start_dt).total_seconds() / 60
        
        if duration < attrs['duration_minutes']:
            raise serializers.ValidationError("Slot duration is shorter than interview duration")
        
        return attrs

class InterviewFeedbackSerializer(serializers.ModelSerializer):
    interviewer_name = serializers.CharField(source='interviewer.full_name', read_only=True)
    average_rating = serializers.ReadOnlyField()
    
    class Meta:
        model = InterviewFeedback
        fields = [
            'id', 'interview', 'interviewer', 'interviewer_name',
            'overall_rating', 'recommendation', 'technical_skills',
            'communication', 'problem_solving', 'cultural_fit',
            'strengths', 'weaknesses', 'additional_notes',
            'would_hire', 'next_steps', 'average_rating',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class InterviewFeedbackCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewFeedback
        fields = [
            'overall_rating', 'recommendation', 'technical_skills',
            'communication', 'problem_solving', 'cultural_fit',
            'strengths', 'weaknesses', 'additional_notes',
            'would_hire', 'next_steps'
        ]

    def validate(self, attrs):
        overall_rating = attrs.get('overall_rating')
        if overall_rating and not (1 <= overall_rating <= 5):
            raise serializers.ValidationError("Overall rating must be between 1 and 5")
        
        # Validate other ratings
        rating_fields = ['technical_skills', 'communication', 'problem_solving', 'cultural_fit']
        for field in rating_fields:
            rating = attrs.get(field)
            if rating and not (1 <= rating <= 5):
                raise serializers.ValidationError(f"{field.replace('_', ' ').title()} must be between 1 and 5")
        
        return attrs

class InterviewTemplateSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = InterviewTemplate
        fields = [
            'id', 'title', 'description', 'interview_type', 'duration_minutes',
            'questions', 'evaluation_criteria', 'company', 'company_name',
            'created_by', 'created_by_name', 'is_public',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

class InterviewTemplateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewTemplate
        fields = [
            'title', 'description', 'interview_type', 'duration_minutes',
            'questions', 'evaluation_criteria', 'is_public'
        ]

class InterviewDetailSerializer(InterviewSerializer):
    feedback = InterviewFeedbackSerializer(read_only=True)
    
    class Meta(InterviewSerializer.Meta):
        fields = InterviewSerializer.Meta.fields + ['feedback']
