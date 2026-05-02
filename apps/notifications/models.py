from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.companies.models import Company

User = get_user_model()

class Notification(models.Model):
    """User notifications"""
    NOTIFICATION_TYPES = [
        ('application', 'Application'),
        ('interview', 'Interview'),
        ('job', 'Job'),
        ('pipeline', 'Pipeline'),
        ('message', 'Message'),
        ('system', 'System'),
        ('reminder', 'Reminder'),
        ('alert', 'Alert'),
    ]

    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, 
        related_name='sent_notifications'
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    
    # Optional linking to related objects
    link = models.URLField(blank=True)
    object_type = models.CharField(max_length=50, blank=True)  # job, application, interview, etc.
    object_id = models.PositiveIntegerField(null=True, blank=True)
    
    # Status and tracking
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery tracking
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    push_sent = models.BooleanField(default=False)
    push_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', 'created_at']),
            models.Index(fields=['notification_type', 'created_at']),
            models.Index(fields=['priority', 'created_at']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.recipient.email} - {self.title}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    def mark_as_unread(self):
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save()

    def archive(self):
        if not self.is_archived:
            self.is_archived = True
            self.archived_at = timezone.now()
            self.save()

    def unarchive(self):
        if self.is_archived:
            self.is_archived = False
            self.archived_at = None
            self.save()

    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

class NotificationTemplate(models.Model):
    """Reusable notification templates"""
    name = models.CharField(max_length=100)
    notification_type = models.CharField(max_length=20, choices=Notification.NOTIFICATION_TYPES)
    priority = models.CharField(max_length=10, choices=Notification.PRIORITY_LEVELS, default='medium')
    
    # Template content with placeholders
    title_template = models.CharField(max_length=200)
    message_template = models.TextField()
    
    # Default settings
    default_link = models.URLField(blank=True)
    default_object_type = models.CharField(max_length=50, blank=True)
    auto_send_email = models.BooleanField(default=False)
    auto_send_push = models.BooleanField(default=False)
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    is_public = models.BooleanField(default=False)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['company', 'name']

    def __str__(self):
        return f"{self.name} ({self.company.name if self.company else 'Public'})"

    def render_title(self, context):
        """Render title template with context variables"""
        return self.title_template.format(**context)

    def render_message(self, context):
        """Render message template with context variables"""
        return self.message_template.format(**context)

class NotificationPreference(models.Model):
    """User notification preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Global preferences
    enable_email = models.BooleanField(default=True)
    enable_push = models.BooleanField(default=True)
    enable_in_app = models.BooleanField(default=True)
    
    # Type-specific preferences
    application_notifications = models.BooleanField(default=True)
    interview_notifications = models.BooleanField(default=True)
    job_notifications = models.BooleanField(default=True)
    pipeline_notifications = models.BooleanField(default=True)
    message_notifications = models.BooleanField(default=True)
    system_notifications = models.BooleanField(default=True)
    reminder_notifications = models.BooleanField(default=True)
    alert_notifications = models.BooleanField(default=True)
    
    # Priority preferences
    low_priority_email = models.BooleanField(default=False)
    medium_priority_email = models.BooleanField(default=True)
    high_priority_email = models.BooleanField(default=True)
    urgent_priority_email = models.BooleanField(default=True)
    
    low_priority_push = models.BooleanField(default=False)
    medium_priority_push = models.BooleanField(default=True)
    high_priority_push = models.BooleanField(default=True)
    urgent_priority_push = models.BooleanField(default=True)
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    quiet_hours_timezone = models.CharField(max_length=50, default='UTC')
    
    # Frequency limits
    daily_email_limit = models.PositiveIntegerField(default=10)
    weekly_email_limit = models.PositiveIntegerField(default=50)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user']

    def __str__(self):
        return f"{self.user.email} Preferences"

    def should_send_email(self, notification):
        """Check if email should be sent for this notification"""
        if not self.enable_email:
            return False
        
        # Check type preference
        type_field = f"{notification.notification_type}_notifications"
        if not getattr(self, type_field, True):
            return False
        
        # Check priority preference
        priority_field = f"{notification.priority}_priority_email"
        if not getattr(self, priority_field, True):
            return False
        
        # Check quiet hours
        if self.quiet_hours_enabled and self._is_quiet_hours():
            return False
        
        return True

    def should_send_push(self, notification):
        """Check if push notification should be sent"""
        if not self.enable_push:
            return False
        
        # Check type preference
        type_field = f"{notification.notification_type}_notifications"
        if not getattr(self, type_field, True):
            return False
        
        # Check priority preference
        priority_field = f"{notification.priority}_priority_push"
        if not getattr(self, priority_field, True):
            return False
        
        # Check quiet hours
        if self.quiet_hours_enabled and self._is_quiet_hours():
            return False
        
        return True

    def _is_quiet_hours(self):
        """Check if current time is within quiet hours"""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        current_time = timezone.now().time()
        start_time = self.quiet_hours_start
        end_time = self.quiet_hours_end
        
        if start_time <= end_time:
            return start_time <= current_time <= end_time
        else:
            # Overnight quiet hours
            return current_time >= start_time or current_time <= end_time

class NotificationChannel(models.Model):
    """Notification delivery channels (email, push, SMS, etc.)"""
    CHANNEL_TYPES = [
        ('email', 'Email'),
        ('push', 'Push Notification'),
        ('sms', 'SMS'),
        ('webhook', 'Webhook'),
        ('slack', 'Slack'),
        ('teams', 'Microsoft Teams'),
    ]

    name = models.CharField(max_length=100)
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPES)
    is_active = models.BooleanField(default=True)
    
    # Channel configuration
    config = models.JSONField(default=dict)  # API keys, webhooks, etc.
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    is_global = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['company', 'name']

    def __str__(self):
        return f"{self.name} ({self.channel_type})"

class NotificationDelivery(models.Model):
    """Track notification delivery attempts and results"""
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='deliveries')
    channel = models.ForeignKey(NotificationChannel, on_delete=models.CASCADE)
    
    # Delivery status
    status = models.CharField(max_length=20, default='pending')  # pending, sent, failed, delivered
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Response data
    response_data = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['notification', 'channel', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.notification.title} - {self.channel.name} ({self.status})"
