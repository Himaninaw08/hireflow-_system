from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationViewSet, NotificationTemplateViewSet,
    NotificationPreferenceViewSet, NotificationChannelViewSet,
    NotificationDeliveryViewSet
)

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'templates', NotificationTemplateViewSet, basename='notificationtemplate')
router.register(r'preferences', NotificationPreferenceViewSet, basename='notificationpreference')
router.register(r'channels', NotificationChannelViewSet, basename='notificationchannel')
router.register(r'deliveries', NotificationDeliveryViewSet, basename='notificationdelivery')

urlpatterns = [
    path('', include(router.urls)),
]
