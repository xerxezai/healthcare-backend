# backend/notifications/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    NotificationTemplate, NotificationPreference, NotificationLog,
    SMSProvider, EmailProvider, NotificationQueue
)


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'template_type', 'is_active', 'created_by', 'created_at'
    ]
    list_filter = ['template_type', 'is_active', 'created_at']
    search_fields = ['name', 'template_type', 'email_subject']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'template_type', 'is_active', 'created_by')
        }),
        ('Email Template', {
            'fields': ('email_subject', 'email_body_text', 'email_body_html'),
            'classes': ('collapse',)
        }),
        ('SMS Template', {
            'fields': ('sms_message',),
            'classes': ('collapse',)
        }),
        ('Template Variables', {
            'fields': ('available_variables',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'email_enabled', 'sms_enabled', 'preferred_email', 'preferred_phone'
    ]
    list_filter = ['email_enabled', 'sms_enabled', 'created_at']
    search_fields = ['user__username', 'user__email', 'preferred_email', 'preferred_phone']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Email Preferences', {
            'fields': (
                'email_enabled', 'email_appointment_reminders',
                'email_test_results', 'email_emergency_alerts', 'email_marketing',
                'preferred_email'
            )
        }),
        ('SMS Preferences', {
            'fields': (
                'sms_enabled', 'sms_appointment_reminders',
                'sms_emergency_alerts', 'sms_test_results', 'preferred_phone'
            )
        }),
        ('Timing Preferences', {
            'fields': ('appointment_reminder_hours', 'quiet_hours_start', 'quiet_hours_end')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'recipient', 'notification_type', 'status', 'subject_truncated', 'created_at'
    ]
    list_filter = ['notification_type', 'status', 'created_at', 'template__template_type']
    search_fields = [
        'recipient__username', 'recipient__email', 'subject', 'message',
        'recipient_email', 'recipient_phone'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'sent_at', 'delivered_at',
        'provider_message_id', 'provider_response'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'recipient', 'sender', 'notification_type', 'template')
        }),
        ('Content', {
            'fields': ('subject', 'message', 'recipient_email', 'recipient_phone')
        }),
        ('Status & Tracking', {
            'fields': (
                'status', 'scheduled_at', 'sent_at', 'delivered_at',
                'error_message', 'retry_count', 'max_retries'
            )
        }),
        ('Provider Information', {
            'fields': ('provider_message_id', 'provider_response'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('context_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def subject_truncated(self, obj):
        if obj.subject:
            return obj.subject[:50] + '...' if len(obj.subject) > 50 else obj.subject
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    subject_truncated.short_description = 'Subject/Message'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipient', 'sender', 'template')


@admin.register(SMSProvider)
class SMSProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider_type', 'is_active', 'is_default', 'sender_id']
    list_filter = ['provider_type', 'is_active', 'is_default']
    search_fields = ['name', 'sender_id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'provider_type', 'is_active', 'is_default')
        }),
        ('Configuration', {
            'fields': ('api_key', 'api_secret', 'account_sid', 'sender_id')
        }),
        ('Rate Limiting', {
            'fields': ('rate_limit_per_minute', 'rate_limit_per_hour')
        }),
        ('Advanced Configuration', {
            'fields': ('config',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(EmailProvider)
class EmailProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider_type', 'is_active', 'is_default', 'from_email']
    list_filter = ['provider_type', 'is_active', 'is_default']
    search_fields = ['name', 'from_email', 'from_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'provider_type', 'is_active', 'is_default')
        }),
        ('Sender Information', {
            'fields': ('from_email', 'from_name')
        }),
        ('API Configuration', {
            'fields': ('api_key', 'api_secret')
        }),
        ('SMTP Configuration', {
            'fields': (
                'smtp_host', 'smtp_port', 'smtp_username',
                'smtp_password', 'smtp_use_tls'
            ),
            'classes': ('collapse',)
        }),
        ('Rate Limiting', {
            'fields': ('rate_limit_per_minute', 'rate_limit_per_hour')
        }),
        ('Advanced Configuration', {
            'fields': ('config',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(NotificationQueue)
class NotificationQueueAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'notification_type', 'recipient', 'priority',
        'scheduled_for', 'processing_status', 'created_at'
    ]
    list_filter = ['priority', 'scheduled_for', 'processed_at']
    search_fields = ['notification_log__recipient__username', 'processing_node']
    readonly_fields = ['created_at']
    date_hierarchy = 'scheduled_for'
    
    def notification_type(self, obj):
        return obj.notification_log.notification_type
    notification_type.short_description = 'Type'
    
    def recipient(self, obj):
        return obj.notification_log.recipient.username
    recipient.short_description = 'Recipient'
    
    def processing_status(self, obj):
        if obj.processed_at:
            return format_html('<span style="color: green;">Processed</span>')
        elif obj.processing_started:
            return format_html('<span style="color: orange;">Processing</span>')
        else:
            return format_html('<span style="color: red;">Pending</span>')
    processing_status.short_description = 'Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('notification_log__recipient')


# Admin actions for bulk operations
def mark_as_processed(modeladmin, request, queryset):
    """Mark selected queue items as processed"""
    from django.utils import timezone
    queryset.update(processed_at=timezone.now())
mark_as_processed.short_description = "Mark selected items as processed"

def reset_queue_items(modeladmin, request, queryset):
    """Reset selected queue items for reprocessing"""
    queryset.update(processing_started=None, processed_at=None)
reset_queue_items.short_description = "Reset selected items for reprocessing"

NotificationQueueAdmin.actions = [mark_as_processed, reset_queue_items]


def activate_templates(modeladmin, request, queryset):
    """Activate selected templates"""
    queryset.update(is_active=True)
activate_templates.short_description = "Activate selected templates"

def deactivate_templates(modeladmin, request, queryset):
    """Deactivate selected templates"""
    queryset.update(is_active=False)
deactivate_templates.short_description = "Deactivate selected templates"

NotificationTemplateAdmin.actions = [activate_templates, deactivate_templates]
