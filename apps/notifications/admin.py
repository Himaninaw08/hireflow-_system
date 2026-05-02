from django.contrib import admin
from .models import (
    Notification, NotificationTemplate, NotificationPreference,
    NotificationChannel, NotificationDelivery
)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'recipient', 'title', 'notification_type', 'priority',
        'is_read', 'is_archived', 'created_at'
    ]
    list_filter = [
        'notification_type', 'priority', 'is_read', 'is_archived',
        'created_at', 'company'
    ]
    search_fields = [
        'recipient__email', 'title', 'message', 'sender__email'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'read_at', 'archived_at', 'email_sent_at', 'push_sent_at',
        'created_at'
    ]

    fieldsets = (
        (None, {
            'fields': ('recipient', 'sender', 'company', 'title', 'message')
        }),
        ('Classification', {
            'fields': ('notification_type', 'priority')
        }),
        ('Linking', {
            'fields': ('link', 'object_type', 'object_id')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'is_archived', 'archived_at')
        }),
        ('Delivery', {
            'fields': ('email_sent', 'email_sent_at', 'push_sent', 'push_sent_at')
        }),
        ('Metadata', {
            'fields': ('metadata', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'notification_type', 'priority', 'company',
        'is_public', 'auto_send_email', 'auto_send_push', 'created_at'
    ]
    list_filter = [
        'notification_type', 'priority', 'is_public', 'auto_send_email',
        'auto_send_push', 'created_at', 'company'
    ]
    search_fields = ['name', 'title_template', 'message_template']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'enable_email', 'enable_push', 'enable_in_app',
        'quiet_hours_enabled', 'daily_email_limit', 'created_at'
    ]
    list_filter = [
        'enable_email', 'enable_push', 'enable_in_app',
        'quiet_hours_enabled', 'created_at'
    ]
    search_fields = ['user__email', 'user__full_name']
    ordering = ['user']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Global Preferences', {
            'fields': ('enable_email', 'enable_push', 'enable_in_app')
        }),
        ('Type Preferences', {
            'fields': (
                'application_notifications', 'interview_notifications',
                'job_notifications', 'pipeline_notifications',
                'message_notifications', 'system_notifications',
                'reminder_notifications', 'alert_notifications'
            )
        }),
        ('Email Priority', {
            'fields': (
                'low_priority_email', 'medium_priority_email',
                'high_priority_email', 'urgent_priority_email'
            )
        }),
        ('Push Priority', {
            'fields': (
                'low_priority_push', 'medium_priority_push',
                'high_priority_push', 'urgent_priority_push'
            )
        }),
        ('Quiet Hours', {
            'fields': (
                'quiet_hours_enabled', 'quiet_hours_start',
                'quiet_hours_end', 'quiet_hours_timezone'
            )
        }),
        ('Limits', {
            'fields': ('daily_email_limit', 'weekly_email_limit')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'channel_type', 'is_active', 'company',
        'is_global', 'created_at'
    ]
    list_filter = [
        'channel_type', 'is_active', 'is_global', 'created_at', 'company'
    ]
    search_fields = ['name', 'company__name']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    list_display = [
        'notification', 'channel', 'status', 'sent_at',
        'delivered_at', 'retry_count', 'created_at'
    ]
    list_filter = [
        'channel', 'status', 'sent_at', 'delivered_at', 'created_at'
    ]
    search_fields = [
        'notification__title', 'channel__name', 'error_message'
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at']

    fieldsets = (
        (None, {
            'fields': ('notification', 'channel', 'status')
        }),
        ('Timing', {
            'fields': ('sent_at', 'delivered_at')
        }),
        ('Response', {
            'fields': ('response_data', 'error_message', 'retry_count')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
