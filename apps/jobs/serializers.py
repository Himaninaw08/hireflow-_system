from rest_framework import serializers
from .models import Job, Application, Tag

class JobSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_logo = serializers.ImageField(source='company.logo', read_only=True)
    application_count = serializers.ReadOnlyField()
    salary_range = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = Job
        fields = [
            'id', 'company', 'company_name', 'company_logo', 'created_by',
            'title', 'slug', 'description', 'requirements', 'job_type',
            'experience_level', 'location', 'salary_min', 'salary_max',
            'currency', 'skills_required', 'status', 'is_anonymous_apply',
            'views_count', 'apply_count', 'application_count', 'salary_range',
            'is_expired', 'expires_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'company', 'created_by', 'slug', 'views_count',
            'apply_count', 'application_count', 'created_at', 'updated_at'
        ]

class JobCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [
            'title', 'description', 'requirements', 'job_type',
            'experience_level', 'location', 'salary_min', 'salary_max',
            'currency', 'skills_required', 'is_anonymous_apply', 'expires_at'
        ]

    def validate(self, attrs):
        from apps.companies.models import Company
        from django.db.models import Q
        user = self.context['request'].user
        
        print(f"DEBUG: User {user.email} (role: {user.role}) trying to create job")

        # Try multiple ways to find user's company
        company = None
        
        # First try: User is company owner
        company = Company.objects.filter(owner=user).first()
        if company:
            print(f"DEBUG: Found company as owner: {company.name}")
        
        # Second try: User is company member
        if not company:
            company = Company.objects.filter(members__user=user).first()
            if company:
                print(f"DEBUG: Found company as member: {company.name}")

        if not company:
            print(f"DEBUG: No company found for user {user.email}")
            raise serializers.ValidationError(
                {"company": "You must belong to a company before posting jobs."}
            )

        attrs['company'] = company
        print(f"DEBUG: Company assigned: {company.name}")
        return attrs    

    def create(self, validated_data):
        user = self.context['request'].user
        company = validated_data.pop('company', None)  # Remove company from validated_data
        
        if not company:
            raise serializers.ValidationError("Company is required to create a job")

        job = Job.objects.create(
            company=company,
            created_by=user,
            **validated_data
        )
        return job

class JobDetailSerializer(JobSerializer):
    applications = serializers.SerializerMethodField()
    
    class Meta(JobSerializer.Meta):
        fields = JobSerializer.Meta.fields + ['applications']
    
    def get_applications(self, obj):
        from .views import ApplicationViewSet
        # Get recent applications for this job
        applications = obj.applications.all()[:5]
        return ApplicationSerializer(applications, many=True).data

class ApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.CharField(source='job.company.name', read_only=True)
    candidate_name = serializers.ReadOnlyField()
    candidate_email = serializers.CharField(source='candidate.email', read_only=True)
    
    class Meta:
        model = Application
        fields = [
            'id', 'job', 'job_title', 'company_name', 'candidate',
            'candidate_name', 'candidate_email', 'pipeline_stage',
            'status', 'resume', 'cover_letter', 'rejection_reason',
            'is_anonymous', 'in_talent_pool', 'applied_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'job', 'candidate', 'is_anonymous', 'applied_at', 'updated_at'
        ]

class ApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['resume', 'cover_letter']

    def validate(self, attrs):
        job = self.context['job']
        candidate = self.context['request'].user
        
        # Check for existing application
        if Application.objects.filter(job=job, candidate=candidate).exists():
            raise serializers.ValidationError("You have already applied to this job")
        
        # Check for duplicate applications to same company within last 6 months
        from django.utils import timezone
        from datetime import timedelta
        six_months_ago = timezone.now() - timedelta(days=180)
        
        if Application.objects.filter(
            candidate=candidate,
            job__company=job.company,
            applied_at__gte=six_months_ago
        ).exists():
            attrs['duplicate_warning'] = True
        
        return attrs

    def create(self, validated_data):
        job = self.context['job']
        candidate = self.context['request'].user
        
        application = Application.objects.create(
            job=job,
            candidate=candidate,
            is_anonymous=job.is_anonymous_apply,
            **validated_data
        )
        
        # Increment job application count
        job.increment_applications()
        
        return application

class TagSerializer(serializers.ModelSerializer):
    application_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tag
        fields = ['id', 'company', 'name', 'color', 'application_count', 'created_at']
        read_only_fields = ['id', 'company', 'created_at']
    
    def get_application_count(self, obj):
        return obj.applications.count()
