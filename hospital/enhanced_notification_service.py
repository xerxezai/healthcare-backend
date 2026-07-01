# Enhanced Notification Service for Healthcare Platform
# Extends existing notification system with SMS and advanced email capabilities

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template import Template, Context
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import transaction

# Third-party imports (will be available after pip install)
try:
    from twilio.rest import Client as TwilioClient
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    TWILIO_AVAILABLE = True
    SENDGRID_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    SENDGRID_AVAILABLE = False

from .notification_models import (
    NotificationLog, 
    NotificationTemplate, 
    NotificationPreference,
    ScheduledNotification
)

logger = logging.getLogger(__name__)


class SMSProvider:
    """Base class for SMS providers"""
    
    def send_sms(self, to: str, message: str) -> Dict[str, Any]:
        raise NotImplementedError


class TwilioSMSProvider(SMSProvider):
    """Twilio SMS provider implementation"""
    
    def __init__(self):
        if not TWILIO_AVAILABLE:
            raise ImportError("Twilio library not installed. Run: pip install twilio")
        
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        self.from_number = getattr(settings, 'TWILIO_FROM_NUMBER', '')
        
        if not all([self.account_sid, self.auth_token, self.from_number]):
            raise ValueError("Twilio credentials not properly configured in settings")
        
        self.client = TwilioClient(self.account_sid, self.auth_token)
    
    def send_sms(self, to: str, message: str) -> Dict[str, Any]:
        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to
            )
            
            return {
                'success': True,
                'message_id': message_obj.sid,
                'status': message_obj.status,
                'provider': 'twilio'
            }
        except Exception as e:
            logger.error(f"Twilio SMS failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'twilio'
            }


class EmailProvider:
    """Base class for email providers"""
    
    def send_email(self, to: str, subject: str, text_content: str, html_content: str = None) -> Dict[str, Any]:
        raise NotImplementedError


class SendGridEmailProvider(EmailProvider):
    """SendGrid email provider implementation"""
    
    def __init__(self):
        if not SENDGRID_AVAILABLE:
            raise ImportError("SendGrid library not installed. Run: pip install sendgrid")
        
        self.api_key = getattr(settings, 'SENDGRID_API_KEY', '')
        self.from_email = getattr(settings, 'SENDGRID_FROM_EMAIL', '')
        
        if not all([self.api_key, self.from_email]):
            raise ValueError("SendGrid credentials not properly configured in settings")
        
        self.client = SendGridAPIClient(api_key=self.api_key)
    
    def send_email(self, to: str, subject: str, text_content: str, html_content: str = None) -> Dict[str, Any]:
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to,
                subject=subject,
                plain_text_content=text_content,
                html_content=html_content
            )
            
            response = self.client.send(message)
            
            return {
                'success': True,
                'message_id': response.headers.get('X-Message-Id'),
                'status_code': response.status_code,
                'provider': 'sendgrid'
            }
        except Exception as e:
            logger.error(f"SendGrid email failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'sendgrid'
            }


class DjangoEmailProvider(EmailProvider):
    """Django SMTP email provider implementation"""
    
    def send_email(self, to: str, subject: str, text_content: str, html_content: str = None) -> Dict[str, Any]:
        try:
            if html_content:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    to=[to]
                )
                email.attach_alternative(html_content, "text/html")
                result = email.send()
            else:
                result = send_mail(
                    subject=subject,
                    message=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[to],
                    fail_silently=False,
                )
            
            return {
                'success': result > 0,
                'message_id': None,
                'provider': 'django_smtp'
            }
        except Exception as e:
            logger.error(f"Django email failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'django_smtp'
            }


class EnhancedNotificationService:
    """
    Enhanced notification service that extends the existing hospital notification system
    with improved SMS and email capabilities
    """
    
    def __init__(self):
        self.sms_provider = None
        self.email_provider = None
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize SMS and email providers based on available settings"""
        # Initialize SMS provider
        try:
            if TWILIO_AVAILABLE and hasattr(settings, 'TWILIO_ACCOUNT_SID'):
                self.sms_provider = TwilioSMSProvider()
                logger.info("Initialized Twilio SMS provider")
        except (ImportError, ValueError) as e:
            logger.warning(f"SMS provider initialization failed: {e}")
        
        # Initialize email provider
        try:
            if SENDGRID_AVAILABLE and hasattr(settings, 'SENDGRID_API_KEY'):
                self.email_provider = SendGridEmailProvider()
                logger.info("Initialized SendGrid email provider")
            else:
                self.email_provider = DjangoEmailProvider()
                logger.info("Initialized Django SMTP email provider")
        except (ImportError, ValueError) as e:
            logger.warning(f"Email provider initialization failed: {e}")
            self.email_provider = DjangoEmailProvider()
    
    def render_template(self, template_content: str, context_data: Dict[str, Any]) -> str:
        """Render template with context data"""
        try:
            template = Template(template_content)
            context = Context(context_data)
            return template.render(context)
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return template_content
    
    def check_quiet_hours(self, user: User = None) -> bool:
        """Check if current time is within quiet hours (9 PM - 8 AM)"""
        current_hour = timezone.now().hour
        return 21 <= current_hour or current_hour <= 8
    
    def get_user_preferences(self, user: User) -> NotificationPreference:
        """Get or create user notification preferences"""
        preferences, created = NotificationPreference.objects.get_or_create(
            user=user,
            defaults={
                'email_appointment_reminders': True,
                'sms_appointment_reminders': True,
                'email_system_alerts': True,
                'email_compliance_notifications': True,
                'email_credential_warnings': True,
            }
        )
        return preferences
    
    def send_notification(
        self,
        notification_type: str,
        recipient_email: str = None,
        recipient_phone: str = None,
        context_data: Dict[str, Any] = None,
        user: User = None,
        priority: str = 'normal',
        schedule_time: datetime = None
    ) -> Dict[str, Any]:
        """
        Send notification immediately or schedule for later
        """
        context_data = context_data or {}
        
        # If scheduled, queue the notification
        if schedule_time and schedule_time > timezone.now():
            return self._schedule_notification(
                notification_type=notification_type,
                recipient_email=recipient_email,
                recipient_phone=recipient_phone,
                context_data=context_data,
                user=user,
                priority=priority,
                schedule_time=schedule_time
            )
        
        # Send immediately
        return self._send_immediate_notification(
            notification_type=notification_type,
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            context_data=context_data,
            user=user
        )
    
    def _schedule_notification(
        self,
        notification_type: str,
        recipient_email: str = None,
        recipient_phone: str = None,
        context_data: Dict[str, Any] = None,
        user: User = None,
        priority: str = 'normal',
        schedule_time: datetime = None
    ) -> Dict[str, Any]:
        """Schedule a notification for future delivery"""
        try:
            # Get template for subject
            template = NotificationTemplate.objects.filter(
                template_type=notification_type,
                is_active=True
            ).first()
            
            if not template:
                return {
                    'success': False,
                    'error': f'No active template found for {notification_type}'
                }
            
            subject = self.render_template(template.subject_template, context_data)
            
            # Create scheduled notification
            scheduled_notification = ScheduledNotification.objects.create(
                notification_type=notification_type,
                recipient_email=recipient_email or '',
                recipient_phone=recipient_phone or '',
                user=user,
                subject=subject,
                message_data=context_data,
                scheduled_time=schedule_time,
                priority=priority
            )
            
            return {
                'success': True,
                'scheduled_id': scheduled_notification.id,
                'scheduled_time': schedule_time,
                'message': 'Notification scheduled successfully'
            }
        
        except Exception as e:
            logger.error(f"Failed to schedule notification: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_immediate_notification(
        self,
        notification_type: str,
        recipient_email: str = None,
        recipient_phone: str = None,
        context_data: Dict[str, Any] = None,
        user: User = None
    ) -> Dict[str, Any]:
        """Send notification immediately"""
        results = {
            'email': None,
            'sms': None,
            'overall_success': False
        }
        
        try:
            # Get template
            template = NotificationTemplate.objects.filter(
                template_type=notification_type,
                is_active=True
            ).first()
            
            if not template:
                error_msg = f'No active template found for {notification_type}'
                logger.error(error_msg)
                return {'success': False, 'error': error_msg}
            
            # Check user preferences
            preferences = None
            if user:
                preferences = self.get_user_preferences(user)
            
            # Send email
            if recipient_email and self.email_provider:
                should_send_email = True
                if preferences:
                    # Check specific preference based on notification type
                    if 'appointment' in notification_type:
                        should_send_email = preferences.email_appointment_reminders
                    elif 'system' in notification_type:
                        should_send_email = preferences.email_system_alerts
                    elif 'compliance' in notification_type:
                        should_send_email = preferences.email_compliance_notifications
                    elif 'credential' in notification_type:
                        should_send_email = preferences.email_credential_warnings
                
                if should_send_email:
                    results['email'] = self._send_email_notification(
                        template, recipient_email, context_data, notification_type, user
                    )
            
            # Send SMS
            if recipient_phone and self.sms_provider:
                should_send_sms = True
                if preferences and 'appointment' in notification_type:
                    should_send_sms = preferences.sms_appointment_reminders
                
                # Respect quiet hours for non-critical notifications
                if notification_type not in ['system_alert', 'critical'] and self.check_quiet_hours():
                    logger.info(f"Skipping SMS during quiet hours for {notification_type}")
                elif should_send_sms:
                    results['sms'] = self._send_sms_notification(
                        template, recipient_phone, context_data, notification_type, user
                    )
            
            # Determine overall success
            results['overall_success'] = any([
                results.get('email', {}).get('success', False),
                results.get('sms', {}).get('success', False)
            ])
            
            return results
        
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return {
                'success': False,
                'error': str(e),
                'email': None,
                'sms': None,
                'overall_success': False
            }
    
    def _send_email_notification(
        self,
        template: NotificationTemplate,
        recipient_email: str,
        context_data: Dict[str, Any],
        notification_type: str,
        user: User = None
    ) -> Dict[str, Any]:
        """Send email notification"""
        try:
            subject = self.render_template(template.subject_template, context_data)
            text_content = self.render_template(template.email_template, context_data)
            
            # For now, use text content as HTML content (can be enhanced later)
            html_content = text_content.replace('\n', '<br>')
            
            result = self.email_provider.send_email(
                to=recipient_email,
                subject=subject,
                text_content=text_content,
                html_content=html_content
            )
            
            # Log the attempt
            NotificationLog.objects.create(
                notification_type=notification_type,
                recipient=recipient_email,
                user=user,
                success=result['success'],
                service_used=result.get('provider', 'unknown'),
                message_id=result.get('message_id', ''),
                error_message=result.get('error', '')
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            
            # Log the failure
            NotificationLog.objects.create(
                notification_type=notification_type,
                recipient=recipient_email,
                user=user,
                success=False,
                service_used='unknown',
                error_message=str(e)
            )
            
            return {
                'success': False,
                'error': str(e),
                'provider': 'unknown'
            }
    
    def _send_sms_notification(
        self,
        template: NotificationTemplate,
        recipient_phone: str,
        context_data: Dict[str, Any],
        notification_type: str,
        user: User = None
    ) -> Dict[str, Any]:
        """Send SMS notification"""
        try:
            if not template.sms_template:
                return {
                    'success': False,
                    'error': 'No SMS template configured',
                    'provider': 'none'
                }
            
            message = self.render_template(template.sms_template, context_data)
            
            result = self.sms_provider.send_sms(
                to=recipient_phone,
                message=message
            )
            
            # Log the attempt
            NotificationLog.objects.create(
                notification_type=notification_type,
                recipient=recipient_phone,
                user=user,
                success=result['success'],
                service_used=result.get('provider', 'unknown'),
                message_id=result.get('message_id', ''),
                error_message=result.get('error', '')
            )
            
            return result
        
        except Exception as e:
            logger.error(f"SMS notification failed: {e}")
            
            # Log the failure
            NotificationLog.objects.create(
                notification_type=notification_type,
                recipient=recipient_phone,
                user=user,
                success=False,
                service_used='unknown',
                error_message=str(e)
            )
            
            return {
                'success': False,
                'error': str(e),
                'provider': 'unknown'
            }
    
    def process_scheduled_notifications(self, batch_size: int = 50) -> Dict[str, Any]:
        """Process pending scheduled notifications"""
        try:
            current_time = timezone.now()
            
            # Get notifications ready to be sent
            pending_notifications = ScheduledNotification.objects.filter(
                status='pending',
                scheduled_time__lte=current_time,
                attempts__lt=models.F('max_attempts')
            ).order_by('priority', 'scheduled_time')[:batch_size]
            
            processed = 0
            sent = 0
            failed = 0
            
            for notification in pending_notifications:
                with transaction.atomic():
                    notification.attempts += 1
                    notification.last_attempt = current_time
                    notification.save()
                    
                    result = self._send_immediate_notification(
                        notification_type=notification.notification_type,
                        recipient_email=notification.recipient_email or None,
                        recipient_phone=notification.recipient_phone or None,
                        context_data=notification.message_data,
                        user=notification.user
                    )
                    
                    if result.get('overall_success', False):
                        notification.status = 'sent'
                        notification.sent_at = current_time
                        sent += 1
                    else:
                        if notification.attempts >= notification.max_attempts:
                            notification.status = 'failed'
                            notification.error_message = str(result.get('error', 'Max attempts exceeded'))
                        failed += 1
                    
                    notification.save()
                    processed += 1
            
            return {
                'success': True,
                'processed': processed,
                'sent': sent,
                'failed': failed,
                'message': f'Processed {processed} notifications'
            }
        
        except Exception as e:
            logger.error(f"Failed to process scheduled notifications: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_bulk_notifications(
        self,
        notification_type: str,
        recipients: List[Dict[str, Any]],
        context_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Send notifications to multiple recipients"""
        results = {
            'total': len(recipients),
            'sent': 0,
            'failed': 0,
            'details': []
        }
        
        for recipient in recipients:
            result = self.send_notification(
                notification_type=notification_type,
                recipient_email=recipient.get('email'),
                recipient_phone=recipient.get('phone'),
                context_data={**(context_data or {}), **recipient.get('context', {})},
                user=recipient.get('user')
            )
            
            if result.get('overall_success', False):
                results['sent'] += 1
            else:
                results['failed'] += 1
            
            results['details'].append({
                'recipient': recipient.get('email') or recipient.get('phone'),
                'success': result.get('overall_success', False),
                'error': result.get('error')
            })
        
        return results


# Convenience function to get the service instance
def get_notification_service() -> EnhancedNotificationService:
    """Get an instance of the enhanced notification service"""
    return EnhancedNotificationService()
