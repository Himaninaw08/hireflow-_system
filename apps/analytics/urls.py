from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AnalyticsDataViewSet, DashboardWidgetViewSet, ReportViewSet,
    MetricDefinitionViewSet, CompanyMetricsViewSet, UserActivityViewSet
)

router = DefaultRouter()
router.register(r'data', AnalyticsDataViewSet, basename='analyticsdata')
router.register(r'widgets', DashboardWidgetViewSet, basename='dashboardwidget')
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'metrics', MetricDefinitionViewSet, basename='metricdefinition')
router.register(r'company-metrics', CompanyMetricsViewSet, basename='companymetrics')
router.register(r'activities', UserActivityViewSet, basename='useractivity')

urlpatterns = [
    path('', include(router.urls)),
]
