from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CandidateProfileViewSet, CandidateExperienceViewSet,
    CandidateEducationViewSet, CandidateProjectViewSet, CandidateSkillViewSet
)

router = DefaultRouter()
router.register(r'profiles', CandidateProfileViewSet, basename='candidateprofile')
router.register(r'experiences', CandidateExperienceViewSet, basename='candidateexperience')
router.register(r'education', CandidateEducationViewSet, basename='candidateeducation')
router.register(r'projects', CandidateProjectViewSet, basename='candidateproject')
router.register(r'skills', CandidateSkillViewSet, basename='candidateskill')

urlpatterns = [
    path('', include(router.urls)),
]
