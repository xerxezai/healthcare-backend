# Enhanced Notification Serializers
# DRF serializers for the enhanced notification system

from rest_framework import serializers
from django.contrib.auth.models import User
from .notification_models import (
    NotificationLog,
    NotificationTemplate,
    NotificationPreference,
    ScheduledNotification
)


class NotificationLogSerializer(serializers.ModelSerializer):
    """Serializer for notification logs"""
    
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    service_used_display = serializers.CharField(source='get_service_used_display', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = NotificationLog
        fields = [
            'id', 'notification_type', 'notification_type_display',
            'recipient', 'user', 'user_name', 'success', 
            'service_used', 'service_used_display', 'message_id',
            'error_message', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for notification templates"""
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'template_type', 'subject_template', 'email_template',
            'sms_template', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for user notification preferences"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'user', 'user_name', 'email_appointment_reminders',
            'sms_appointment_reminders', 'email_system_alerts',
            'email_compliance_notifications', 'email_credential_warnings',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class ScheduledNotificationSerializer(serializers.ModelSerializer):
    """Serializer for scheduled notifications"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ScheduledNotification
        fields = [
            'id', 'notification_type', 'recipient_email', 'recipient_phone',
            'user', 'user_name', 'subject', 'message_data', 'scheduled_time',
            'priority', 'priority_display', 'status', 'status_display',
            'attempts', 'max_attempts', 'last_attempt', 'sent_at',
            'error_message', 'created_at'
        ]
        read_only_fields = [
            'id', 'attempts', 'last_attempt', 'sent_at', 'error_message', 'created_at'
        ]


class SendNotificationSerializer(serializers.Serializer):
    """Serializer for sending immediate notifications"""
    
    notification_type = serializers.CharField(max_length=50)
    recipient_email = serializers.EmailField(required=False, allow_blank=True)
    recipient_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    user_id = serializers.IntegerField(required=False)
    context_data = serializers.JSONField(default=dict)
    priority = serializers.ChoiceField(
        choices=['low', 'normal', 'high', 'critical'],
        default='normal'
    )
    
    def validate(self, data):
        """Validate that at least one recipient method is provided"""
        if not data.get('recipient_email') and not data.get('recipient_phone'):
            raise serializers.ValidationError(
                "At least one of recipient_email or recipient_phone is required"
            )
        return data


class ScheduleNotificationSerializer(serializers.Serializer):
    """Serializer for scheduling notifications"""
    
    notification_type = serializers.CharField(max_length=50)
    recipient_email = serializers.EmailField(required=False, allow_blank=True)
    recipient_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    user_id = serializers.IntegerField(required=False)
    context_data = serializers.JSONField(default=dict)
    priority = serializers.ChoiceField(
        choices=['low', 'normal', 'high', 'critical'],
        default='normal'
    )
    schedule_time = serializers.DateTimeField()
    
    def validate(self, data):
        """Validate that at least one recipient method is provided"""
        if not data.get('recipient_email') and not data.get('recipient_phone'):
            raise serializers.ValidationError(
                "At least one of recipient_email or recipient_phone is required"
            )
        return data


class BulkNotificationSerializer(serializers.Serializer):
    """Serializer for bulk notifications"""
    
    notification_type = serializers.CharField(max_length=50)
    recipients = serializers.ListField(
        child=serializers.DictField(),
        max_length=100
    )
    context_data = serializers.JSONField(default=dict)
    
    def validate_recipients(self, value):
        """Validate recipients list"""
        if not value:
            raise serializers.ValidationError("Recipients list cannot be empty")
        
        for i, recipient in enumerate(value):
            if not recipient.get('email') and not recipient.get('phone'):
                raise serializers.ValidationError(
                    f"Recipient {i+1} must have either email or phone"
                )
        
        return value


class AppointmentReminderSerializer(serializers.Serializer):
    """Serializer for appointment reminder notifications"""
    
    patient_email = serializers.EmailField()
    patient_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    patient_name = serializers.CharField(max_length=100, default='Patient')
    appointment_date = serializers.CharField(max_length=50)
    appointment_time = serializers.CharField(max_length=50)
    doctor_name = serializers.CharField(max_length=100)
    clinic_name = serializers.CharField(max_length=100, default='Healthcare Clinic')
    clinic_address = serializers.CharField(max_length=200, required=False, allow_blank=True)
    schedule_time = serializers.DateTimeField(required=False)


class TestResultsNotificationSerializer(serializers.Serializer):
    """Serializer for test results notifications"""
    
    patient_email = serializers.EmailField()
    patient_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    patient_name = serializers.CharField(max_length=100, default='Patient')
    test_name = serializers.CharField(max_length=100)
    results_url = serializers.URLField(required=False, allow_blank=True)
    clinic_name = serializers.CharField(max_length=100, default='Healthcare Clinic')


class EmergencyAlertSerializer(serializers.Serializer):
    """Serializer for emergency alert notifications"""
    
    recipient_email = serializers.EmailField(required=False, allow_blank=True)
    recipient_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    emergency_message = serializers.CharField(max_length=500)
    
    def validate(self, data):
        """Validate that at least one recipient method is provided"""
        if not data.get('recipient_email') and not data.get('recipient_phone'):
            raise serializers.ValidationError(
                "At least one of recipient_email or recipient_phone is required"
            )
        return data


class NotificationStatsSerializer(serializers.Serializer):
    """Serializer for notification statistics"""
    
    period_days = serializers.IntegerField()
    total_notifications = serializers.DictField()
    by_type = serializers.ListField()
    by_service = serializers.ListField()
    scheduled = serializers.DictField()
