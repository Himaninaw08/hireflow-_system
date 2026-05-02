from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PipelineViewSet, PipelineStageViewSet, StageTransitionViewSet, PipelineTemplateViewSet

router = DefaultRouter()
router.register(r'pipelines', PipelineViewSet, basename='pipeline')
router.register(r'stages', PipelineStageViewSet, basename='pipelinestage')
router.register(r'transitions', StageTransitionViewSet, basename='stagetransition')
router.register(r'templates', PipelineTemplateViewSet, basename='pipelinetemplate')

urlpatterns = [
    path('', include(router.urls)),
]
