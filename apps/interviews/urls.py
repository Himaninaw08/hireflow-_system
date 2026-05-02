from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InterviewViewSet, InterviewSlotViewSet, InterviewFeedbackViewSet, InterviewTemplateViewSet

router = DefaultRouter()
router.register(r'interviews', InterviewViewSet, basename='interview')
router.register(r'slots', InterviewSlotViewSet, basename='interviewslot')
router.register(r'feedback', InterviewFeedbackViewSet, basename='interviewfeedback')
router.register(r'templates', InterviewTemplateViewSet, basename='interviewtemplate')

urlpatterns = [
    path('', include(router.urls)),
]
