from rest_framework import serializers
from .models import (
    Notification, NotificationTemplate, NotificationPreference,
    NotificationChannel, NotificationDelivery
)

class NotificationSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'sender', 'sender_name', 'company', 'company_name',
            'title', 'message', 'notification_type', 'priority', 'link',
            'object_type', 'object_id', 'is_read', 'read_at', 'is_archived',
            'archived_at', 'email_sent', 'email_sent_at', 'push_sent',
            'push_sent_at', 'metadata', 'created_at', 'expires_at', 'is_expired'
        ]
        read_only_fields = [
            'id', 'sender', 'company', 'read_at', 'archived_at',
            'email_sent_at', 'push_sent_at', 'created_at'
        ]

class NotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'recipient', 'title', 'message', 'notification_type',
            'priority', 'link', 'object_type', 'object_id',
            'metadata', 'expires_at'
        ]

    def validate_recipient(self, value):
        user = self.context['request'].user
        if user.role == 'candidate' and value != user:
            raise serializers.ValidationError("Candidates can only send notifications to themselves")
        return value

class NotificationTemplateSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'notification_type', 'priority', 'title_template',
            'message_template', 'default_link', 'default_object_type',
            'auto_send_email', 'auto_send_push', 'company', 'company_name',
            'is_public', 'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'company', 'created_by', 'created_at', 'updated_at'
        ]

class NotificationTemplateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = [
            'name', 'notification_type', 'priority', 'title_template',
            'message_template', 'default_link', 'default_object_type',
            'auto_send_email', 'auto_send_push', 'is_public'
        ]

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            'user', 'enable_email', 'enable_push', 'enable_in_app',
            'application_notifications', 'interview_notifications',
            'job_notifications', 'pipeline_notifications',
            'message_notifications', 'system_notifications',
            'reminder_notifications', 'alert_notifications',
            'low_priority_email', 'medium_priority_email',
            'high_priority_email', 'urgent_priority_email',
            'low_priority_push', 'medium_priority_push',
            'high_priority_push', 'urgent_priority_push',
            'quiet_hours_enabled', 'quiet_hours_start',
            'quiet_hours_end', 'quiet_hours_timezone',
            'daily_email_limit', 'weekly_email_limit',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

class NotificationChannelSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = NotificationChannel
        fields = [
            'id', 'name', 'channel_type', 'is_active', 'config',
            'company', 'company_name', 'is_global', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'company', 'created_at', 'updated_at']

class NotificationDeliverySerializer(serializers.ModelSerializer):
    channel_name = serializers.CharField(source='channel.name', read_only=True)
    notification_title = serializers.CharField(source='notification.title', read_only=True)
    
    class Meta:
        model = NotificationDelivery
        fields = [
            'id', 'notification', 'channel', 'channel_name',
            'notification_title', 'status', 'sent_at', 'delivered_at',
            'response_data', 'error_message', 'retry_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class NotificationBatchCreateSerializer(serializers.Serializer):
    """Serializer for creating multiple notifications at once"""
    recipients = serializers.ListField(child=serializers.IntegerField())
    title = serializers.CharField(max_length=200)
    message = serializers.CharField()
    notification_type = serializers.ChoiceField(choices=Notification.NOTIFICATION_TYPES)
    priority = serializers.ChoiceField(choices=Notification.PRIORITY_LEVELS, default='medium')
    link = serializers.URLField(required=False)
    object_type = serializers.CharField(max_length=50, required=False)
    object_id = serializers.IntegerField(required=False)
    metadata = serializers.DictField(required=False)
    expires_at = serializers.DateTimeField(required=False)

    def validate_recipients(self, value):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Validate that all recipient IDs exist
        existing_users = User.objects.filter(id__in=value).values_list('id', flat=True)
        missing_ids = set(value) - set(existing_users)
        
        if missing_ids:
            raise serializers.ValidationError(f"Invalid recipient IDs: {list(missing_ids)}")
        
        return value

class NotificationSearchSerializer(serializers.Serializer):
    """Serializer for notification search parameters"""
    query = serializers.CharField(required=False)
    notification_type = serializers.CharField(required=False)
    priority = serializers.CharField(required=False)
    is_read = serializers.BooleanField(required=False)
    is_archived = serializers.BooleanField(required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    limit = serializers.IntegerField(default=20, max_value=100)

class NotificationStatsSerializer(serializers.Serializer):
    """Serializer for notification statistics"""
    total_notifications = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    read_notifications = serializers.IntegerField()
    archived_notifications = serializers.IntegerField()
    notifications_by_type = serializers.DictField()
    notifications_by_priority = serializers.DictField()
    recent_notifications = NotificationSerializer(many=True)

class NotificationTemplateRenderSerializer(serializers.Serializer):
    """Serializer for rendering notification templates"""
    template_id = serializers.IntegerField()
    context = serializers.DictField()

    def validate_template_id(self, value):
        try:
            from .models import NotificationTemplate
            if not NotificationTemplate.objects.filter(id=value).exists():
                raise serializers.ValidationError("Template not found")
        except:
            raise serializers.ValidationError("Invalid template ID")
        return value

class BulkNotificationActionSerializer(serializers.Serializer):
    """Serializer for bulk notification actions"""
    notification_ids = serializers.ListField(child=serializers.IntegerField())
    action = serializers.ChoiceField(choices=['mark_read', 'mark_unread', 'archive', 'unarchive', 'delete'])

    def validate_notification_ids(self, value):
        from .models import Notification
        
        # Validate that all notification IDs exist
        existing_notifications = Notification.objects.filter(id__in=value).values_list('id', flat=True)
        missing_ids = set(value) - set(existing_notifications)
        
        if missing_ids:
            raise serializers.ValidationError(f"Invalid notification IDs: {list(missing_ids)}")
        
        return value
