# Notification Log Model for Healthcare Platform
# Stores audit trail of all notification attempts

from django.db import models
from django.conf import settings
from django.utils import timezone

class NotificationLog(models.Model):
    """
    Audit log for all notification attempts (email/SMS)
    """
    NOTIFICATION_TYPES = [
        ('registration_confirmation', 'Registration Confirmation'),
        ('admin_approval_required', 'Admin Approval Required'),
        ('account_approved', 'Account Approved'),
        ('password_reset', 'Password Reset'),
        ('appointment_reminder_email', 'Appointment Reminder Email'),
        ('appointment_reminder_sms', 'Appointment Reminder SMS'),
        ('credential_expiry_warning', 'Credential Expiry Warning'),
        ('compliance_notification', 'Compliance Notification'),
        ('system_alert', 'System Alert'),
    ]
    
    SERVICES = [
        ('ses', 'AWS SES'),
        ('sns', 'AWS SNS'),
        ('django_smtp', 'Django SMTP'),
        ('unknown', 'Unknown'),
    ]
    
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    recipient = models.CharField(max_length=255)  # Email or phone number
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    success = models.BooleanField(default=False)
    service_used = models.CharField(max_length=20, choices=SERVICES, default='unknown')
    message_id = models.CharField(max_length=255, blank=True)  # AWS message ID
    error_message = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'notification_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['notification_type'], name='notif_logs_type_idx'),
            models.Index(fields=['recipient'], name='notif_logs_recipient_idx'),
            models.Index(fields=['success'], name='notif_logs_success_idx'),
            models.Index(fields=['timestamp'], name='notif_logs_timestamp_idx'),
        ]
    
    def __str__(self):
        return f"{self.notification_type} to {self.recipient} - {'Success' if self.success else 'Failed'}"


class NotificationTemplate(models.Model):
    """
    Customizable notification templates for different types
    """
    template_type = models.CharField(max_length=50, unique=True)
    subject_template = models.CharField(max_length=255)
    email_template = models.TextField()
    sms_template = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_templates'
    
    def __str__(self):
        return f"Template: {self.template_type}"


class NotificationPreference(models.Model):
    """
    User preferences for different types of notifications
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email_appointment_reminders = models.BooleanField(default=True)
    sms_appointment_reminders = models.BooleanField(default=True)
    email_system_alerts = models.BooleanField(default=True)
    email_compliance_notifications = models.BooleanField(default=True)
    email_credential_warnings = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"


class ScheduledNotification(models.Model):
    """
    Queue for scheduled notifications (appointment reminders, credential expiry warnings)
    """
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    notification_type = models.CharField(max_length=50)
    recipient_email = models.EmailField(blank=True)
    recipient_phone = models.CharField(max_length=20, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    subject = models.CharField(max_length=255)
    message_data = models.JSONField()  # Template context data
    scheduled_time = models.DateTimeField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    last_attempt = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'scheduled_notifications'
        ordering = ['scheduled_time', 'priority']
        indexes = [
            models.Index(fields=['status'], name='sched_notif_status_idx'),
            models.Index(fields=['scheduled_time'], name='sched_notif_time_idx'),
            models.Index(fields=['priority'], name='sched_notif_priority_idx'),
        ]
    
    def __str__(self):
        return f"{self.notification_type} - {self.status} - {self.scheduled_time}"
