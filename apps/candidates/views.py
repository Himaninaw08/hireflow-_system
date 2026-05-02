from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import models
from apps.accounts.permissions import IsCandidate, IsEmployer
from .models import (
    CandidateProfile, CandidateExperience, CandidateEducation,
    CandidateProject, CandidateSkill
)
from .serializers import (
    CandidateProfileSerializer, CandidateProfileCreateSerializer,
    CandidateProfilePublicSerializer, CandidateProfileSearchSerializer,
    CandidateExperienceSerializer, CandidateExperienceCreateSerializer,
    CandidateEducationSerializer, CandidateEducationCreateSerializer,
    CandidateProjectSerializer, CandidateProjectCreateSerializer,
    CandidateSkillSerializer, CandidateSkillCreateSerializer
)

class CandidateProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'experience_level', 'employment_type', 'work_preference',
        'is_public', 'is_active_job_seeker'
    ]
    search_fields = [
        'headline', 'bio', 'location', 'current_position',
        'current_company', 'skills'
    ]
    ordering_fields = [
        'created_at', 'updated_at', 'profile_completion_percentage'
    ]
    ordering = ['-updated_at']

    @action(detail=False, methods=['get'])
    def test(self, request):
        """Test endpoint to debug issues"""
        try:
            return Response({
                'message': 'Candidates API is working',
                'user_id': request.user.id,
                'user_email': request.user.email,
                'user_role': getattr(request.user, 'role', 'unknown'),
                'is_authenticated': request.user.is_authenticated
            })
        except Exception as e:
            return Response({
                'error': str(e),
                'user_id': getattr(request.user, 'id', 'none'),
                'is_authenticated': getattr(request.user, 'is_authenticated', False)
            }, status=500)

    def get_queryset(self):
        user = self.request.user
        
        # Skip queryset filtering for custom actions
        if self.action in ['me', 'create_profile', 'search', 'test', 'upload_resume', 'update_profile']:
            return CandidateProfile.objects.all()
        
        if user.role == 'candidate':
            # Candidates can only see their own profile
            return CandidateProfile.objects.filter(user=user)
        elif user.role in ['employer', 'recruiter']:
            # Employers can see public profiles
            return CandidateProfile.objects.filter(is_public=True)
        elif user.role == 'admin':
            return CandidateProfile.objects.all()
        
        return CandidateProfile.objects.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return CandidateProfileCreateSerializer
        elif self.action == 'list' and self.request.user.role in ['employer', 'recruiter']:
            return CandidateProfileSearchSerializer
        elif self.action in ['retrieve'] and self.request.user.role in ['employer', 'recruiter']:
            return CandidateProfilePublicSerializer
        return CandidateProfileSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's candidate profile"""
        try:
            # Check if user is a candidate
            if request.user.role != 'candidate':
                return Response(
                    {'error': 'Only candidates can have profiles'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            profile = CandidateProfile.objects.get(user=request.user)
            serializer = CandidateProfileSerializer(profile)
            return Response(serializer.data)
        except CandidateProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'An error occurred: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        """Update current user's candidate profile"""
        try:
            # Check if user is a candidate
            if request.user.role != 'candidate':
                return Response(
                    {'error': 'Only candidates can update profiles'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            try:
                profile = CandidateProfile.objects.get(user=request.user)
            except CandidateProfile.DoesNotExist:
                return Response(
                    {'error': 'Profile not found. Please create a profile first.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = CandidateProfileSerializer(
                profile, 
                data=request.data, 
                partial=True,
                context={'request': request}
            )
            
            if serializer.is_valid():
                updated_profile = serializer.save()
                return Response(
                    CandidateProfileSerializer(updated_profile).data,
                    status=status.HTTP_200_OK
                )
            else:
                print(f"Profile update validation errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print(f"Exception during profile update: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Failed to update profile: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def create_profile(self, request):
        """Create profile for current user"""
        try:
            # Check if user is a candidate
            if request.user.role != 'candidate':
                return Response(
                    {'error': 'Only candidates can create profiles'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            profile = CandidateProfile.objects.get(user=request.user)
            return Response(
                {'error': 'Profile already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except CandidateProfile.DoesNotExist:
            try:
                # Log the incoming data for debugging
                print(f"Creating profile for user: {request.user.id}, data: {request.data}")
                
                serializer = CandidateProfileCreateSerializer(
                    data=request.data,
                    context={'request': request}
                )
                if serializer.is_valid():
                    profile = serializer.save()
                    print(f"Profile created successfully: {profile.id}")
                    return Response(
                        CandidateProfileSerializer(profile).data,
                        status=status.HTTP_201_CREATED
                    )
                else:
                    print(f"Serializer errors: {serializer.errors}")
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(f"Exception during profile creation: {str(e)}")
                import traceback
                traceback.print_exc()
                return Response(
                    {'error': f'Failed to create profile: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            print(f"General exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'An error occurred: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def upload_resume(self, request):
        """Upload resume file"""
        try:
            # Check if user is a candidate
            if request.user.role != 'candidate':
                return Response(
                    {'error': 'Only candidates can upload resumes'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get or create profile
            try:
                profile = CandidateProfile.objects.get(user=request.user)
            except CandidateProfile.DoesNotExist:
                return Response(
                    {'error': 'Profile not found. Please create a profile first.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if resume file is provided
            if 'resume_file' not in request.FILES:
                return Response(
                    {'error': 'No resume file provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update profile with resume file
            profile.resume_file = request.FILES['resume_file']
            profile.save()
            
            serializer = CandidateProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Exception during resume upload: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Failed to upload resume: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search for candidates"""
        queryset = self.get_queryset().filter(is_public=True, is_active_job_seeker=True)
        
        # Custom filters
        skills = request.query_params.getlist('skills')
        if skills:
            queryset = queryset.filter(skills__contains=skills)
        
        min_experience = request.query_params.get('min_experience')
        if min_experience:
            # This would need more complex logic to calculate from experiences
            pass
        
        location = request.query_params.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        salary_min = request.query_params.get('salary_min')
        salary_max = request.query_params.get('salary_max')
        if salary_min:
            queryset = queryset.filter(salary_expectation_min__gte=salary_min)
        if salary_max:
            queryset = queryset.filter(salary_expectation_max__lte=salary_max)
        
        # Sort by profile completion
        queryset = queryset.order_by('-profile_completion_percentage')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = CandidateProfileSearchSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = CandidateProfileSearchSerializer(queryset, many=True)
        return Response(serializer.data)

class CandidateExperienceViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsCandidate]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['employment_type', 'is_current_position']
    search_fields = ['company', 'position', 'description']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-start_date']

    def get_queryset(self):
        user = self.request.user
        try:
            profile = CandidateProfile.objects.get(user=user)
            return CandidateExperience.objects.filter(profile=profile)
        except CandidateProfile.DoesNotExist:
            return CandidateExperience.objects.none()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CandidateExperienceCreateSerializer
        return CandidateExperienceSerializer

    def perform_create(self, serializer):
        user = self.request.user
        profile = CandidateProfile.objects.get(user=user)
        serializer.save(profile=profile)

class CandidateEducationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsCandidate]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['education_level']
    search_fields = ['institution', 'degree', 'field_of_study']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-start_date']

    def get_queryset(self):
        user = self.request.user
        try:
            profile = CandidateProfile.objects.get(user=user)
            return CandidateEducation.objects.filter(profile=profile)
        except CandidateProfile.DoesNotExist:
            return CandidateEducation.objects.none()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CandidateEducationCreateSerializer
        return CandidateEducationSerializer

    def perform_create(self, serializer):
        user = self.request.user
        profile = CandidateProfile.objects.get(user=user)
        serializer.save(profile=profile)

class CandidateProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsCandidate]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['project_type', 'is_featured']
    search_fields = ['title', 'description', 'technologies']
    ordering_fields = ['is_featured', 'start_date', 'created_at']
    ordering = ['-is_featured', '-start_date']

    def get_queryset(self):
        user = self.request.user
        try:
            profile = CandidateProfile.objects.get(user=user)
            return CandidateProject.objects.filter(profile=profile)
        except CandidateProfile.DoesNotExist:
            return CandidateProject.objects.none()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CandidateProjectCreateSerializer
        return CandidateProjectSerializer

    def perform_create(self, serializer):
        user = self.request.user
        profile = CandidateProfile.objects.get(user=user)
        serializer.save(profile=profile)

class CandidateSkillViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsCandidate]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['level', 'is_primary']
    search_fields = ['name']
    ordering_fields = ['is_primary', '-years_of_experience', 'name']
    ordering = ['-is_primary', '-years_of_experience', 'name']

    def get_queryset(self):
        user = self.request.user
        try:
            profile = CandidateProfile.objects.get(user=user)
            return CandidateSkill.objects.filter(profile=profile)
        except CandidateProfile.DoesNotExist:
            return CandidateSkill.objects.none()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CandidateSkillCreateSerializer
        return CandidateSkillSerializer

    def perform_create(self, serializer):
        user = self.request.user
        profile = CandidateProfile.objects.get(user=user)
        serializer.save(profile=profile)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple skills at once"""
        skills_data = request.data.get('skills', [])
        
        if not skills_data:
            return Response(
                {'error': 'skills data is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = self.request.user
        try:
            profile = CandidateProfile.objects.get(user=user)
        except CandidateProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        created_skills = []
        errors = []
        
        for skill_data in skills_data:
            serializer = CandidateSkillCreateSerializer(data=skill_data)
            if serializer.is_valid():
                try:
                    skill = serializer.save(profile=profile)
                    created_skills.append(skill)
                except Exception as e:
                    errors.append({'skill': skill_data.get('name', 'unknown'), 'error': str(e)})
            else:
                errors.append({'skill': skill_data.get('name', 'unknown'), 'error': serializer.errors})
        
        if errors:
            return Response({
                'created': len(created_skills),
                'errors': errors
            }, status=status.HTTP_207_MULTI_STATUS)
        
        serializer = CandidateSkillSerializer(created_skills, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
