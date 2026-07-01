# backend/notifications/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    NotificationTemplate, NotificationPreference, NotificationLog,
    SMSProvider, EmailProvider, NotificationQueue
)


class NotificationTemplateSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    template_type_display = serializers.CharField(source='get_template_type_display', read_only=True)
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'template_type', 'template_type_display',
            'email_subject', 'email_body_text', 'email_body_html',
            'sms_message', 'available_variables', 'is_active',
            'created_at', 'updated_at', 'created_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = NotificationPreference
        fields = [
            'user_name', 'email_enabled', 'email_appointment_reminders',
            'email_test_results', 'email_emergency_alerts', 'email_marketing',
            'sms_enabled', 'sms_appointment_reminders', 'sms_emergency_alerts',
            'sms_test_results', 'appointment_reminder_hours',
            'quiet_hours_start', 'quiet_hours_end', 'preferred_email',
            'preferred_phone', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class NotificationLogSerializer(serializers.ModelSerializer):
    recipient_name = serializers.CharField(source='recipient.get_full_name', read_only=True)
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = NotificationLog
        fields = [
            'id', 'recipient_name', 'sender_name', 'notification_type',
            'notification_type_display', 'template_name', 'subject',
            'message', 'recipient_email', 'recipient_phone', 'status',
            'status_display', 'scheduled_at', 'sent_at', 'delivered_at',
            'error_message', 'retry_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SendNotificationSerializer(serializers.Serializer):
    """
    Serializer for sending notifications
    """
    # Recipients
    recipient_id = serializers.IntegerField(required=False)
    recipient_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    
    # Notification details
    template_type = serializers.CharField(max_length=50)
    notification_types = serializers.ListField(
        child=serializers.ChoiceField(choices=['email', 'sms', 'push', 'in_app']),
        default=['email', 'sms']
    )
    
    # Content
    context_data = serializers.JSONField(default=dict)
    
    # Scheduling
    scheduled_for = serializers.CharField(required=False, allow_blank=True)
    priority = serializers.ChoiceField(
        choices=['low', 'normal', 'high', 'urgent'],
        default='normal'
    )
    
    def validate(self, data):
        # Ensure at least one recipient is specified
        if not data.get('recipient_id') and not data.get('recipient_ids'):
            raise serializers.ValidationError("Either recipient_id or recipient_ids must be provided")
        
        # Validate template type exists
        try:
            NotificationTemplate.objects.get(
                template_type=data['template_type'],
                is_active=True
            )
        except NotificationTemplate.DoesNotExist:
            raise serializers.ValidationError(f"Template type '{data['template_type']}' not found or inactive")
        
        return data


class SMSProviderSerializer(serializers.ModelSerializer):
    provider_type_display = serializers.CharField(source='get_provider_type_display', read_only=True)
    
    class Meta:
        model = SMSProvider
        fields = [
            'id', 'name', 'provider_type', 'provider_type_display',
            'is_active', 'is_default', 'sender_id', 'rate_limit_per_minute',
            'rate_limit_per_hour', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmailProviderSerializer(serializers.ModelSerializer):
    provider_type_display = serializers.CharField(source='get_provider_type_display', read_only=True)
    
    class Meta:
        model = EmailProvider
        fields = [
            'id', 'name', 'provider_type', 'provider_type_display',
            'is_active', 'is_default', 'from_email', 'from_name',
            'smtp_host', 'smtp_port', 'smtp_use_tls',
            'rate_limit_per_minute', 'rate_limit_per_hour',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationQueueSerializer(serializers.ModelSerializer):
    notification_log = NotificationLogSerializer(read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = NotificationQueue
        fields = [
            'id', 'notification_log', 'priority', 'priority_display',
            'scheduled_for', 'processing_started', 'processed_at',
            'processing_node', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class BulkNotificationSerializer(serializers.Serializer):
    """
    Serializer for bulk notification operations
    """
    recipient_ids = serializers.ListField(child=serializers.IntegerField())
    template_type = serializers.CharField(max_length=50)
    context_data = serializers.JSONField(default=dict)
    notification_types = serializers.ListField(
        child=serializers.ChoiceField(choices=['email', 'sms']),
        default=['email', 'sms']
    )
    scheduled_for = serializers.DateTimeField(required=False)
    priority = serializers.ChoiceField(
        choices=['low', 'normal', 'high', 'urgent'],
        default='normal'
    )
    
    def validate_recipient_ids(self, value):
        if not value:
            raise serializers.ValidationError("At least one recipient must be specified")
        
        # Check if all users exist
        existing_users = User.objects.filter(id__in=value).count()
        if existing_users != len(value):
            raise serializers.ValidationError("Some recipient IDs are invalid")
        
        return value


class NotificationStatsSerializer(serializers.Serializer):
    """
    Serializer for notification statistics
    """
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    notification_type = serializers.ChoiceField(
        choices=['email', 'sms', 'push', 'in_app'],
        required=False
    )
    status = serializers.ChoiceField(
        choices=['pending', 'sent', 'delivered', 'failed', 'bounced'],
        required=False
    )


class TemplatePreviewSerializer(serializers.Serializer):
    """
    Serializer for template preview
    """
    template_id = serializers.UUIDField()
    context_data = serializers.JSONField(default=dict)
    
    def validate_template_id(self, value):
        try:
            NotificationTemplate.objects.get(id=value, is_active=True)
        except NotificationTemplate.DoesNotExist:
            raise serializers.ValidationError("Template not found or inactive")
        return value


class TestNotificationSerializer(serializers.Serializer):
    """
    Serializer for sending test notifications
    """
    template_type = serializers.CharField(max_length=50)
    notification_types = serializers.ListField(
        child=serializers.ChoiceField(choices=['email', 'sms']),
        default=['email']
    )
    test_email = serializers.EmailField(required=False)
    test_phone = serializers.CharField(max_length=20, required=False)
    context_data = serializers.JSONField(default=dict)
    
    def validate(self, data):
        notification_types = data.get('notification_types', [])
        
        if 'email' in notification_types and not data.get('test_email'):
            raise serializers.ValidationError("test_email is required when email notification is selected")
        
        if 'sms' in notification_types and not data.get('test_phone'):
            raise serializers.ValidationError("test_phone is required when SMS notification is selected")
        
        return data
