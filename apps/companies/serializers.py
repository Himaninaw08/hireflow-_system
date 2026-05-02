from rest_framework import serializers
from .models import Company, CompanyMember

class CompanySerializer(serializers.ModelSerializer):
    job_count = serializers.ReadOnlyField()
    active_job_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Company
        fields = [
            'id', 'owner', 'name', 'slug', 'description', 'logo', 'website',
            'industry', 'company_size', 'location', 'founded_year', 'subscription_tier', 'is_verified',
            'job_count', 'active_job_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'slug', 'job_count', 'active_job_count', 'created_at', 'updated_at']

class CompanyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            'name', 'description', 'logo', 'website', 'industry', 'company_size', 'location', 'founded_year', 'is_verified'
        ]

    def create(self, validated_data):
        user = self.context['request'].user
        # Remove owner from validated_data if it exists to avoid duplicate argument
        validated_data.pop('owner', None)
        company = Company.objects.create(owner=user, **validated_data)
        # Create owner membership
        CompanyMember.objects.create(
            company=company,
            user=user,
            role='owner'
        )
        return company

class CompanyMemberSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    is_owner = serializers.ReadOnlyField()
    can_manage_jobs = serializers.ReadOnlyField()
    can_view_analytics = serializers.ReadOnlyField()

    class Meta:
        model = CompanyMember
        fields = [
            'id', 'company', 'user', 'user_email', 'user_name', 'role',
            'is_owner', 'can_manage_jobs', 'can_view_analytics', 'joined_at'
        ]
        read_only_fields = ['id', 'joined_at']

class CompanyDetailSerializer(CompanySerializer):
    members = CompanyMemberSerializer(many=True, read_only=True)
    
    class Meta(CompanySerializer.Meta):
        fields = CompanySerializer.Meta.fields + ['members']
