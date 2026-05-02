from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.accounts.permissions import IsEmployer, IsCandidate
from apps.companies.models import Company
from .models import (
    Notification, NotificationTemplate, NotificationPreference,
    NotificationChannel, NotificationDelivery
)
from .serializers import (
    NotificationSerializer, NotificationCreateSerializer,
    NotificationTemplateSerializer, NotificationTemplateCreateSerializer,
    NotificationPreferenceSerializer, NotificationChannelSerializer,
    NotificationDeliverySerializer, NotificationBatchCreateSerializer,
    NotificationSearchSerializer, NotificationStatsSerializer,
    NotificationTemplateRenderSerializer, BulkNotificationActionSerializer
)

User = get_user_model()

class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'notification_type', 'priority', 'is_read', 'is_archived', 'object_type'
    ]
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'priority', 'read_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        queryset = Notification.objects.filter(recipient=user)
        
        # Filter out expired notifications
        queryset = queryset.filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
        )
        
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return NotificationCreateSerializer
        return NotificationSerializer

    def perform_create(self, serializer):
        notification = serializer.save()
        
        # Create delivery records based on preferences
        self._create_deliveries(notification)

    def _create_deliveries(self, notification):
        """Create notification delivery records"""
        from .models import NotificationChannel, NotificationPreference
        
        try:
            preferences = NotificationPreference.objects.get(user=notification.recipient)
        except NotificationPreference.DoesNotExist:
            preferences = NotificationPreference.objects.create(user=notification.recipient)
        
        # Get active channels
        channels = NotificationChannel.objects.filter(is_active=True)
        
        for channel in channels:
            should_deliver = False
            
            if channel.channel_type == 'email' and preferences.should_send_email(notification):
                should_deliver = True
            elif channel.channel_type == 'push' and preferences.should_send_push(notification):
                should_deliver = True
            
            if should_deliver:
                NotificationDelivery.objects.create(
                    notification=notification,
                    channel=channel,
                    status='pending'
                )

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications"""
        notifications = self.get_queryset().filter(is_read=False)
        page = self.paginate_queryset(notifications)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def archived(self, request):
        """Get archived notifications"""
        notifications = self.get_queryset().filter(is_archived=True)
        page = self.paginate_queryset(notifications)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'status': 'marked as read', 'read_at': notification.read_at})

    @action(detail=True, methods=['post'])
    def mark_unread(self, request, pk=None):
        """Mark notification as unread"""
        notification = self.get_object()
        notification.mark_as_unread()
        return Response({'status': 'marked as unread'})

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive notification"""
        notification = self.get_object()
        notification.archive()
        return Response({'status': 'archived', 'archived_at': notification.archived_at})

    @action(detail=True, methods=['post'])
    def unarchive(self, request, pk=None):
        """Unarchive notification"""
        notification = self.get_object()
        notification.unarchive()
        return Response({'status': 'unarchived'})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        notifications = self.get_queryset().filter(is_read=False)
        count = notifications.count()
        notifications.update(is_read=True, read_at=timezone.now())
        return Response({'status': 'marked all as read', 'count': count})

    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on notifications"""
        serializer = BulkNotificationActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        notification_ids = serializer.validated_data['notification_ids']
        action = serializer.validated_data['action']
        
        notifications = Notification.objects.filter(
            id__in=notification_ids,
            recipient=request.user
        )
        
        if action == 'mark_read':
            notifications.update(is_read=True, read_at=timezone.now())
        elif action == 'mark_unread':
            notifications.update(is_read=False, read_at=None)
        elif action == 'archive':
            notifications.update(is_archived=True, archived_at=timezone.now())
        elif action == 'unarchive':
            notifications.update(is_archived=False, archived_at=None)
        elif action == 'delete':
            count = notifications.count()
            notifications.delete()
            return Response({'status': 'deleted', 'count': count})
        
        return Response({'status': f'{action} completed', 'count': notifications.count()})

    @action(detail=False, methods=['post'])
    def batch_create(self, request):
        """Create multiple notifications at once"""
        serializer = NotificationBatchCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        created_notifications = []
        
        for recipient_id in serializer.validated_data['recipients']:
            try:
                recipient = User.objects.get(id=recipient_id)
                notification = Notification.objects.create(
                    recipient=recipient,
                    sender=user,
                    title=serializer.validated_data['title'],
                    message=serializer.validated_data['message'],
                    notification_type=serializer.validated_data['notification_type'],
                    priority=serializer.validated_data['priority'],
                    link=serializer.validated_data.get('link', ''),
                    object_type=serializer.validated_data.get('object_type', ''),
                    object_id=serializer.validated_data.get('object_id'),
                    metadata=serializer.validated_data.get('metadata', {}),
                    expires_at=serializer.validated_data.get('expires_at'),
                )
                self._create_deliveries(notification)
                created_notifications.append(notification)
            except User.DoesNotExist:
                continue
        
        return Response({
            'created': len(created_notifications),
            'notifications': NotificationSerializer(created_notifications, many=True).data
        })

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get notification statistics"""
        user = request.user
        queryset = Notification.objects.filter(recipient=user)
        
        stats = {
            'total_notifications': queryset.count(),
            'unread_notifications': queryset.filter(is_read=False).count(),
            'read_notifications': queryset.filter(is_read=True).count(),
            'archived_notifications': queryset.filter(is_archived=True).count(),
            'notifications_by_type': {},
            'notifications_by_priority': {},
            'recent_notifications': []
        }
        
        # Group by type
        for notification_type, _ in Notification.NOTIFICATION_TYPES:
            stats['notifications_by_type'][notification_type] = queryset.filter(
                notification_type=notification_type
            ).count()
        
        # Group by priority
        for priority, _ in Notification.PRIORITY_LEVELS:
            stats['notifications_by_priority'][priority] = queryset.filter(
                priority=priority
            ).count()
        
        # Recent notifications
        recent = queryset.order_by('-created_at')[:5]
        stats['recent_notifications'] = NotificationSerializer(recent, many=True).data
        
        return Response(stats)

class NotificationTemplateViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsEmployer]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['notification_type', 'priority', 'is_public']
    search_fields = ['name', 'title_template', 'message_template']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        user = self.request.user
        user_companies = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role__in=['owner', 'recruiter'])
        ).distinct()
        return NotificationTemplate.objects.filter(
            models.Q(company__in=user_companies) | models.Q(is_public=True)
        ).distinct()

    def get_serializer_class(self):
        if self.action == 'create':
            return NotificationTemplateCreateSerializer
        return NotificationTemplateSerializer

    def perform_create(self, serializer):
        user = self.request.user
        company = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role='owner')
        ).first()
        
        if not company:
            raise permissions.PermissionDenied("You must have a company to create templates")
        
        serializer.save(created_by=user, company=company)

    @action(detail=True, methods=['post'])
    def render(self, request, pk=None):
        """Render template with context"""
        template = self.get_object()
        context = request.data.get('context', {})
        
        try:
            rendered_title = template.render_title(context)
            rendered_message = template.render_message(context)
            
            return Response({
                'rendered_title': rendered_title,
                'rendered_message': rendered_message
            })
        except KeyError as e:
            return Response(
                {'error': f'Missing context variable: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def send_from_template(self, request):
        """Send notification using template"""
        template_id = request.data.get('template_id')
        recipients = request.data.get('recipients', [])
        context = request.data.get('context', {})
        
        if not template_id or not recipients:
            return Response(
                {'error': 'template_id and recipients are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            template = NotificationTemplate.objects.get(id=template_id)
        except NotificationTemplate.DoesNotExist:
            return Response(
                {'error': 'Template not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions
        user = request.user
        if template.company and not Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role__in=['owner', 'recruiter']),
            id=template.company.id
        ).exists():
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        created_notifications = []
        
        for recipient_id in recipients:
            try:
                recipient = User.objects.get(id=recipient_id)
                
                notification = Notification.objects.create(
                    recipient=recipient,
                    sender=user,
                    title=template.render_title(context),
                    message=template.render_message(context),
                    notification_type=template.notification_type,
                    priority=template.priority,
                    link=template.default_link,
                    object_type=template.default_object_type,
                    metadata={'template_id': template.id, 'context': context}
                )
                
                created_notifications.append(notification)
                
            except User.DoesNotExist:
                continue
        
        return Response({
            'created': len(created_notifications),
            'notifications': NotificationSerializer(created_notifications, many=True).data
        })

class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationPreferenceSerializer

    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)

    def get_object(self):
        # Get or create preferences for current user
        preference, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return preference

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class NotificationChannelViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsEmployer]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['channel_type', 'is_active', 'is_global']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        user = self.request.user
        user_companies = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role__in=['owner', 'recruiter'])
        ).distinct()
        return NotificationChannel.objects.filter(
            models.Q(company__in=user_companies) | models.Q(is_global=True)
        ).distinct()

    def perform_create(self, serializer):
        user = self.request.user
        company = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role='owner')
        ).first()
        
        if not company:
            raise permissions.PermissionDenied("You must have a company to create channels")
        
        serializer.save(company=company)

class NotificationDeliveryViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view for notification delivery tracking"""
    permission_classes = [permissions.IsAuthenticated, IsEmployer]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['channel', 'status']
    search_fields = ['notification__title', 'channel__name']
    ordering_fields = ['created_at', 'sent_at', 'delivered_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        user_companies = Company.objects.filter(
            models.Q(owner=user) | 
            models.Q(members__user=user, members__role__in=['owner', 'recruiter'])
        ).distinct()
        return NotificationDelivery.objects.filter(
            notification__recipient__in=User.objects.filter(
                models.Q(companies__in=user_companies) |
                models.Q(company_memberships__company__in=user_companies)
            ).distinct()
        )
