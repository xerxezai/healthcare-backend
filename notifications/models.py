# backend/notifications/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class NotificationTemplate(models.Model):
    """
    Templates for different types of notifications (appointment reminders, test results, etc.)
    """
    TEMPLATE_TYPES = [
        ('appointment_reminder', 'Appointment Reminder'),
        ('appointment_confirmation', 'Appointment Confirmation'),
        ('test_results', 'Test Results Available'),
        ('prescription_ready', 'Prescription Ready'),
        ('follow_up', 'Follow-up Required'),
        ('emergency_alert', 'Emergency Alert'),
        ('system_maintenance', 'System Maintenance'),
        ('payment_reminder', 'Payment Reminder'),
        ('birthday_wishes', 'Birthday Wishes'),
        ('wellness_tip', 'Wellness Tip'),
        ('custom', 'Custom Message'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES)
    
    # Email template fields
    email_subject = models.CharField(max_length=200, blank=True)
    email_body_text = models.TextField(blank=True, help_text="Plain text version")
    email_body_html = models.TextField(blank=True, help_text="HTML version")
    
    # SMS template fields
    sms_message = models.TextField(max_length=1600, blank=True, help_text="SMS message (max 1600 chars)")
    
    # Template variables documentation
    available_variables = models.JSONField(
        default=list,
        help_text="List of available variables like {patient_name}, {appointment_date}, etc."
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'notification_templates'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class NotificationPreference(models.Model):
    """
    User preferences for notifications
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Email preferences
    email_enabled = models.BooleanField(default=True)
    email_appointment_reminders = models.BooleanField(default=True)
    email_test_results = models.BooleanField(default=True)
    email_emergency_alerts = models.BooleanField(default=True)
    email_marketing = models.BooleanField(default=False)
    
    # SMS preferences
    sms_enabled = models.BooleanField(default=True)
    sms_appointment_reminders = models.BooleanField(default=True)
    sms_emergency_alerts = models.BooleanField(default=True)
    sms_test_results = models.BooleanField(default=False)  # Sensitive info
    
    # Timing preferences
    appointment_reminder_hours = models.IntegerField(
        default=24, 
        help_text="Hours before appointment to send reminder"
    )
    quiet_hours_start = models.TimeField(default="22:00", help_text="Start of quiet hours")
    quiet_hours_end = models.TimeField(default="08:00", help_text="End of quiet hours")
    
    # Contact information
    preferred_email = models.EmailField(blank=True)
    preferred_phone = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.username}"


class NotificationLog(models.Model):
    """
    Log of all sent notifications
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
    ]
    
    NOTIFICATION_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App Notification'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_received')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications_sent')
    
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    template = models.ForeignKey(NotificationTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Message content
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    recipient_email = models.EmailField(blank=True)
    recipient_phone = models.CharField(max_length=20, blank=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    
    # Provider information
    provider_message_id = models.CharField(max_length=100, blank=True)
    provider_response = models.JSONField(default=dict)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    # Metadata
    context_data = models.JSONField(default=dict, help_text="Additional context for the notification")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['status', 'scheduled_at']),
            models.Index(fields=['notification_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} to {self.recipient.username} - {self.status}"
    
    def mark_as_sent(self):
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at', 'updated_at'])
    
    def mark_as_delivered(self):
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at', 'updated_at'])
    
    def mark_as_failed(self, error_message):
        self.status = 'failed'
        self.error_message = error_message
        self.retry_count += 1
        self.save(update_fields=['status', 'error_message', 'retry_count', 'updated_at'])


class SMSProvider(models.Model):
    """
    Configuration for SMS providers (Twilio, AWS SNS, etc.)
    """
    PROVIDER_CHOICES = [
        ('twilio', 'Twilio'),
        ('aws_sns', 'AWS SNS'),
        ('nexmo', 'Nexmo/Vonage'),
        ('textlocal', 'TextLocal'),
        ('custom', 'Custom Provider'),
    ]
    
    name = models.CharField(max_length=100)
    provider_type = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Provider configuration
    api_key = models.CharField(max_length=200, blank=True)
    api_secret = models.CharField(max_length=200, blank=True)
    account_sid = models.CharField(max_length=200, blank=True)  # For Twilio
    sender_id = models.CharField(max_length=20, blank=True, help_text="Sender ID or phone number")
    
    # Configuration JSON for additional settings
    config = models.JSONField(default=dict)
    
    # Rate limiting
    rate_limit_per_minute = models.IntegerField(default=100)
    rate_limit_per_hour = models.IntegerField(default=1000)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sms_providers'
    
    def __str__(self):
        return f"{self.name} ({self.get_provider_type_display()})"
    
    def save(self, *args, **kwargs):
        # Ensure only one default provider
        if self.is_default:
            SMSProvider.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class EmailProvider(models.Model):
    """
    Configuration for email providers (SendGrid, AWS SES, SMTP, etc.)
    """
    PROVIDER_CHOICES = [
        ('sendgrid', 'SendGrid'),
        ('aws_ses', 'AWS SES'),
        ('mailgun', 'Mailgun'),
        ('smtp', 'SMTP'),
        ('custom', 'Custom Provider'),
    ]
    
    name = models.CharField(max_length=100)
    provider_type = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Provider configuration
    api_key = models.CharField(max_length=200, blank=True)
    api_secret = models.CharField(max_length=200, blank=True)
    
    # SMTP settings
    smtp_host = models.CharField(max_length=100, blank=True)
    smtp_port = models.IntegerField(null=True, blank=True)
    smtp_username = models.CharField(max_length=100, blank=True)
    smtp_password = models.CharField(max_length=200, blank=True)
    smtp_use_tls = models.BooleanField(default=True)
    
    # Sender information
    from_email = models.EmailField()
    from_name = models.CharField(max_length=100, default="Healthcare Platform")
    
    # Configuration JSON for additional settings
    config = models.JSONField(default=dict)
    
    # Rate limiting
    rate_limit_per_minute = models.IntegerField(default=1000)
    rate_limit_per_hour = models.IntegerField(default=10000)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'email_providers'
    
    def __str__(self):
        return f"{self.name} ({self.get_provider_type_display()})"
    
    def save(self, *args, **kwargs):
        # Ensure only one default provider
        if self.is_default:
            EmailProvider.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class NotificationQueue(models.Model):
    """
    Queue for scheduled notifications
    """
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    notification_log = models.OneToOneField(NotificationLog, on_delete=models.CASCADE, related_name='queue_item')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    scheduled_for = models.DateTimeField()
    
    # Processing information
    processing_started = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_node = models.CharField(max_length=100, blank=True, help_text="Processing server/worker ID")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notification_queue'
        ordering = ['priority', 'scheduled_for']
        indexes = [
            models.Index(fields=['scheduled_for', 'priority']),
            models.Index(fields=['processed_at']),
        ]
    
    def __str__(self):
        return f"Queue item for {self.notification_log}"
