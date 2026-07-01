# backend/notifications/services.py

import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.template import Template, Context
from django.core.mail import send_mail, EmailMultiAlternatives
from django.contrib.auth.models import User
from .models import (
    NotificationTemplate, NotificationPreference, NotificationLog,
    SMSProvider, EmailProvider, NotificationQueue
)

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Main service for handling all notification operations
    """
    
    def __init__(self):
        self.email_service = EmailService()
        self.sms_service = SMSService()
    
    def send_notification(
        self,
        recipient: User,
        template_type: str,
        context_data: Dict[str, Any],
        notification_types: List[str] = ['email', 'sms'],
        scheduled_for: Optional[datetime] = None,
        priority: str = 'normal',
        sender: Optional[User] = None
    ) -> Dict[str, bool]:
        """
        Send notification using specified types
        
        Args:
            recipient: User to send notification to
            template_type: Type of template to use
            context_data: Data to populate template variables
            notification_types: List of notification types ['email', 'sms']
            scheduled_for: When to send (None for immediate)
            priority: Priority level ('low', 'normal', 'high', 'urgent')
            sender: User sending the notification
        
        Returns:
            Dict with success status for each notification type
        """
        results = {}
        
        # Get user preferences
        preferences = self._get_user_preferences(recipient)
        
        # Get template
        template = self._get_template(template_type)
        if not template:
            logger.error(f"Template not found: {template_type}")
            return {nt: False for nt in notification_types}
        
        # Check if it's within quiet hours
        if self._is_quiet_hours(preferences) and priority not in ['high', 'urgent']:
            # Schedule for after quiet hours
            scheduled_for = self._get_next_allowed_time(preferences)
        
        # Send each notification type
        for notification_type in notification_types:
            try:
                if notification_type == 'email' and self._should_send_email(preferences, template_type):
                    results['email'] = self._send_email_notification(
                        recipient, template, context_data, scheduled_for, priority, sender
                    )
                elif notification_type == 'sms' and self._should_send_sms(preferences, template_type):
                    results['sms'] = self._send_sms_notification(
                        recipient, template, context_data, scheduled_for, priority, sender
                    )
                else:
                    results[notification_type] = False
                    logger.info(f"Skipped {notification_type} for {recipient.username} - disabled in preferences")
                    
            except Exception as e:
                logger.error(f"Error sending {notification_type} to {recipient.username}: {str(e)}")
                results[notification_type] = False
        
        return results
    
    def send_bulk_notification(
        self,
        recipients: List[User],
        template_type: str,
        context_data: Dict[str, Any],
        notification_types: List[str] = ['email', 'sms'],
        scheduled_for: Optional[datetime] = None,
        priority: str = 'normal'
    ) -> Dict[str, int]:
        """
        Send notifications to multiple recipients
        """
        results = {'email_sent': 0, 'sms_sent': 0, 'failed': 0}
        
        for recipient in recipients:
            try:
                notification_results = self.send_notification(
                    recipient, template_type, context_data,
                    notification_types, scheduled_for, priority
                )
                
                if notification_results.get('email'):
                    results['email_sent'] += 1
                if notification_results.get('sms'):
                    results['sms_sent'] += 1
                    
            except Exception as e:
                results['failed'] += 1
                logger.error(f"Failed to send notification to {recipient.username}: {str(e)}")
        
        return results
    
    def _get_user_preferences(self, user: User) -> NotificationPreference:
        """Get or create user notification preferences"""
        preferences, created = NotificationPreference.objects.get_or_create(user=user)
        return preferences
    
    def _get_template(self, template_type: str) -> Optional[NotificationTemplate]:
        """Get active template by type"""
        try:
            return NotificationTemplate.objects.get(
                template_type=template_type,
                is_active=True
            )
        except NotificationTemplate.DoesNotExist:
            return None
    
    def _should_send_email(self, preferences: NotificationPreference, template_type: str) -> bool:
        """Check if email should be sent based on preferences"""
        if not preferences.email_enabled:
            return False
        
        preference_map = {
            'appointment_reminder': preferences.email_appointment_reminders,
            'test_results': preferences.email_test_results,
            'emergency_alert': preferences.email_emergency_alerts,
        }
        
        return preference_map.get(template_type, True)
    
    def _should_send_sms(self, preferences: NotificationPreference, template_type: str) -> bool:
        """Check if SMS should be sent based on preferences"""
        if not preferences.sms_enabled:
            return False
        
        preference_map = {
            'appointment_reminder': preferences.sms_appointment_reminders,
            'test_results': preferences.sms_test_results,
            'emergency_alert': preferences.sms_emergency_alerts,
        }
        
        return preference_map.get(template_type, True)
    
    def _is_quiet_hours(self, preferences: NotificationPreference) -> bool:
        """Check if current time is within user's quiet hours"""
        now = timezone.now().time()
        start = preferences.quiet_hours_start
        end = preferences.quiet_hours_end
        
        if start <= end:
            return start <= now <= end
        else:  # Quiet hours cross midnight
            return now >= start or now <= end
    
    def _get_next_allowed_time(self, preferences: NotificationPreference) -> datetime:
        """Get next allowed sending time after quiet hours"""
        now = timezone.now()
        end_time = preferences.quiet_hours_end
        
        next_send = now.replace(
            hour=end_time.hour,
            minute=end_time.minute,
            second=0,
            microsecond=0
        )
        
        if next_send <= now:
            next_send += timedelta(days=1)
        
        return next_send
    
    def _send_email_notification(
        self, recipient: User, template: NotificationTemplate,
        context_data: Dict, scheduled_for: Optional[datetime],
        priority: str, sender: Optional[User]
    ) -> bool:
        """Send email notification"""
        try:
            # Get recipient email
            preferences = self._get_user_preferences(recipient)
            recipient_email = preferences.preferred_email or recipient.email
            
            if not recipient_email:
                logger.warning(f"No email address for user {recipient.username}")
                return False
            
            # Render email content
            subject = self._render_template(template.email_subject, context_data)
            text_body = self._render_template(template.email_body_text, context_data)
            html_body = self._render_template(template.email_body_html, context_data)
            
            # Create notification log
            notification_log = NotificationLog.objects.create(
                recipient=recipient,
                sender=sender,
                notification_type='email',
                template=template,
                subject=subject,
                message=text_body,
                recipient_email=recipient_email,
                scheduled_at=scheduled_for,
                context_data=context_data
            )
            
            if scheduled_for:
                # Add to queue
                NotificationQueue.objects.create(
                    notification_log=notification_log,
                    priority=priority,
                    scheduled_for=scheduled_for
                )
                return True
            else:
                # Send immediately
                return self.email_service.send_email(
                    recipient_email, subject, text_body, html_body, notification_log
                )
                
        except Exception as e:
            logger.error(f"Error in _send_email_notification: {str(e)}")
            return False
    
    def _send_sms_notification(
        self, recipient: User, template: NotificationTemplate,
        context_data: Dict, scheduled_for: Optional[datetime],
        priority: str, sender: Optional[User]
    ) -> bool:
        """Send SMS notification"""
        try:
            # Get recipient phone
            preferences = self._get_user_preferences(recipient)
            recipient_phone = preferences.preferred_phone
            
            if not recipient_phone:
                logger.warning(f"No phone number for user {recipient.username}")
                return False
            
            # Render SMS content
            message = self._render_template(template.sms_message, context_data)
            
            # Create notification log
            notification_log = NotificationLog.objects.create(
                recipient=recipient,
                sender=sender,
                notification_type='sms',
                template=template,
                message=message,
                recipient_phone=recipient_phone,
                scheduled_at=scheduled_for,
                context_data=context_data
            )
            
            if scheduled_for:
                # Add to queue
                NotificationQueue.objects.create(
                    notification_log=notification_log,
                    priority=priority,
                    scheduled_for=scheduled_for
                )
                return True
            else:
                # Send immediately
                return self.sms_service.send_sms(
                    recipient_phone, message, notification_log
                )
                
        except Exception as e:
            logger.error(f"Error in _send_sms_notification: {str(e)}")
            return False
    
    def _render_template(self, template_string: str, context_data: Dict) -> str:
        """Render template with context data"""
        if not template_string:
            return ""
        
        template = Template(template_string)
        context = Context(context_data)
        return template.render(context)
    
    def process_queue(self, limit: int = 100) -> Dict[str, int]:
        """Process scheduled notifications from queue"""
        now = timezone.now()
        
        # Get due notifications
        queue_items = NotificationQueue.objects.filter(
            scheduled_for__lte=now,
            processed_at__isnull=True
        ).order_by('priority', 'scheduled_for')[:limit]
        
        results = {'processed': 0, 'failed': 0}
        
        for queue_item in queue_items:
            try:
                queue_item.processing_started = now
                queue_item.save()
                
                notification = queue_item.notification_log
                
                if notification.notification_type == 'email':
                    success = self.email_service.send_email(
                        notification.recipient_email,
                        notification.subject,
                        notification.message,
                        None,  # HTML body from template if needed
                        notification
                    )
                elif notification.notification_type == 'sms':
                    success = self.sms_service.send_sms(
                        notification.recipient_phone,
                        notification.message,
                        notification
                    )
                
                if success:
                    results['processed'] += 1
                else:
                    results['failed'] += 1
                
                queue_item.processed_at = timezone.now()
                queue_item.save()
                
            except Exception as e:
                logger.error(f"Error processing queue item {queue_item.id}: {str(e)}")
                results['failed'] += 1
        
        return results


class EmailService:
    """
    Email sending service with multiple provider support
    """
    
    def __init__(self):
        self.provider = self._get_default_provider()
    
    def _get_default_provider(self) -> Optional[EmailProvider]:
        """Get default email provider"""
        try:
            return EmailProvider.objects.get(is_default=True, is_active=True)
        except EmailProvider.DoesNotExist:
            return None
    
    def send_email(
        self, recipient_email: str, subject: str,
        text_body: str, html_body: Optional[str] = None,
        notification_log: Optional[NotificationLog] = None
    ) -> bool:
        """Send email using configured provider"""
        try:
            if not self.provider:
                logger.error("No email provider configured")
                return False
            
            if self.provider.provider_type == 'sendgrid':
                return self._send_via_sendgrid(
                    recipient_email, subject, text_body, html_body, notification_log
                )
            elif self.provider.provider_type == 'smtp':
                return self._send_via_smtp(
                    recipient_email, subject, text_body, html_body, notification_log
                )
            else:
                logger.error(f"Unsupported email provider: {self.provider.provider_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            if notification_log:
                notification_log.mark_as_failed(str(e))
            return False
    
    def _send_via_sendgrid(
        self, recipient_email: str, subject: str,
        text_body: str, html_body: Optional[str],
        notification_log: Optional[NotificationLog]
    ) -> bool:
        """Send email via SendGrid"""
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail
            
            sg = sendgrid.SendGridAPIClient(api_key=self.provider.api_key)
            
            message = Mail(
                from_email=(self.provider.from_email, self.provider.from_name),
                to_emails=recipient_email,
                subject=subject,
                plain_text_content=text_body,
                html_content=html_body
            )
            
            response = sg.send(message)
            
            if notification_log:
                notification_log.provider_message_id = response.headers.get('X-Message-Id', '')
                notification_log.provider_response = {
                    'status_code': response.status_code,
                    'headers': dict(response.headers)
                }
                notification_log.mark_as_sent()
            
            return response.status_code in [200, 201, 202]
            
        except Exception as e:
            logger.error(f"SendGrid error: {str(e)}")
            if notification_log:
                notification_log.mark_as_failed(str(e))
            return False
    
    def _send_via_smtp(
        self, recipient_email: str, subject: str,
        text_body: str, html_body: Optional[str],
        notification_log: Optional[NotificationLog]
    ) -> bool:
        """Send email via SMTP"""
        try:
            if html_body:
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_body,
                    from_email=f"{self.provider.from_name} <{self.provider.from_email}>",
                    to=[recipient_email]
                )
                msg.attach_alternative(html_body, "text/html")
                msg.send()
            else:
                send_mail(
                    subject=subject,
                    message=text_body,
                    from_email=f"{self.provider.from_name} <{self.provider.from_email}>",
                    recipient_list=[recipient_email],
                    fail_silently=False
                )
            
            if notification_log:
                notification_log.mark_as_sent()
            
            return True
            
        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            if notification_log:
                notification_log.mark_as_failed(str(e))
            return False


class SMSService:
    """
    SMS sending service with multiple provider support
    """
    
    def __init__(self):
        self.provider = self._get_default_provider()
    
    def _get_default_provider(self) -> Optional[SMSProvider]:
        """Get default SMS provider"""
        try:
            return SMSProvider.objects.get(is_default=True, is_active=True)
        except SMSProvider.DoesNotExist:
            return None
    
    def send_sms(
        self, recipient_phone: str, message: str,
        notification_log: Optional[NotificationLog] = None
    ) -> bool:
        """Send SMS using configured provider"""
        try:
            if not self.provider:
                logger.error("No SMS provider configured")
                return False
            
            # Clean phone number
            phone = self._clean_phone_number(recipient_phone)
            
            if self.provider.provider_type == 'twilio':
                return self._send_via_twilio(phone, message, notification_log)
            else:
                logger.error(f"Unsupported SMS provider: {self.provider.provider_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            if notification_log:
                notification_log.mark_as_failed(str(e))
            return False
    
    def _send_via_twilio(
        self, recipient_phone: str, message: str,
        notification_log: Optional[NotificationLog]
    ) -> bool:
        """Send SMS via Twilio"""
        try:
            from twilio.rest import Client
            
            client = Client(self.provider.account_sid, self.provider.api_secret)
            
            message_obj = client.messages.create(
                body=message,
                from_=self.provider.sender_id,
                to=recipient_phone
            )
            
            if notification_log:
                notification_log.provider_message_id = message_obj.sid
                notification_log.provider_response = {
                    'status': message_obj.status,
                    'sid': message_obj.sid
                }
                notification_log.mark_as_sent()
            
            return True
            
        except Exception as e:
            logger.error(f"Twilio error: {str(e)}")
            if notification_log:
                notification_log.mark_as_failed(str(e))
            return False
    
    def _clean_phone_number(self, phone: str) -> str:
        """Clean and format phone number"""
        # Remove all non-digit characters
        cleaned = re.sub(r'\D', '', phone)
        
        # Add country code if missing (assuming US)
        if len(cleaned) == 10:
            cleaned = '+1' + cleaned
        elif len(cleaned) == 11 and cleaned.startswith('1'):
            cleaned = '+' + cleaned
        
        return cleaned


# Utility functions for common notification scenarios

def send_appointment_reminder(appointment, hours_before: int = 24):
    """Send appointment reminder notification"""
    service = NotificationService()
    
    context_data = {
        'patient_name': appointment.patient.get_full_name(),
        'appointment_date': appointment.scheduled_date.strftime('%B %d, %Y'),
        'appointment_time': appointment.scheduled_date.strftime('%I:%M %p'),
        'doctor_name': appointment.doctor.get_full_name(),
        'clinic_name': getattr(appointment, 'clinic_name', 'Healthcare Clinic'),
        'clinic_address': getattr(appointment, 'clinic_address', ''),
    }
    
    # Schedule reminder
    reminder_time = appointment.scheduled_date - timedelta(hours=hours_before)
    
    return service.send_notification(
        recipient=appointment.patient,
        template_type='appointment_reminder',
        context_data=context_data,
        scheduled_for=reminder_time,
        priority='normal'
    )


def send_test_results_notification(patient, test_name: str, results_url: str):
    """Send test results available notification"""
    service = NotificationService()
    
    context_data = {
        'patient_name': patient.get_full_name(),
        'test_name': test_name,
        'results_url': results_url,
        'clinic_name': 'Healthcare Clinic',
    }
    
    return service.send_notification(
        recipient=patient,
        template_type='test_results',
        context_data=context_data,
        priority='high'
    )


def send_emergency_alert(recipients: List[User], message: str):
    """Send emergency alert to multiple recipients"""
    service = NotificationService()
    
    context_data = {
        'emergency_message': message,
        'timestamp': timezone.now().strftime('%B %d, %Y at %I:%M %p'),
    }
    
    return service.send_bulk_notification(
        recipients=recipients,
        template_type='emergency_alert',
        context_data=context_data,
        priority='urgent'
    )
