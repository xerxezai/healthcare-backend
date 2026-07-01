# AWS Enhanced Notification Service for Healthcare Platform
# Integrates with AWS SNS and SES for enterprise-grade notifications

import logging
import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template import Template, Context
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import transaction
from botocore.exceptions import BotoCoreError, ClientError

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


class AWSSNSProvider(SMSProvider):
    """AWS SNS SMS provider implementation"""
    
    def __init__(self):
        self.region_name = getattr(settings, 'AWS_REGION', 'us-east-1')
        self.access_key_id = getattr(settings, 'AWS_ACCESS_KEY_ID', '')
        self.secret_access_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', '')
        
        if not all([self.access_key_id, self.secret_access_key]):
            raise ValueError("AWS credentials not properly configured in settings")
        
        try:
            self.sns_client = boto3.client(
                'sns',
                region_name=self.region_name,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key
            )
            
            # Test connection
            self.sns_client.list_topics(MaxItems=1)
            logger.info("AWS SNS client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AWS SNS client: {e}")
            raise
    
    def send_sms(self, to: str, message: str) -> Dict[str, Any]:
        try:
            # Format phone number for international format
            if not to.startswith('+'):
                to = '+1' + to.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
            
            response = self.sns_client.publish(
                PhoneNumber=to,
                Message=message,
                MessageAttributes={
                    'AWS.SNS.SMS.SenderID': {
                        'DataType': 'String',
                        'StringValue': getattr(settings, 'AWS_SNS_SENDER_ID', 'Healthcare')
                    },
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'  # For healthcare notifications
                    }
                }
            )
            
            return {
                'success': True,
                'message_id': response['MessageId'],
                'provider': 'aws_sns',
                'status': 'sent'
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"AWS SNS SMS failed - {error_code}: {error_message}")
            
            return {
                'success': False,
                'error': f"{error_code}: {error_message}",
                'provider': 'aws_sns'
            }
        except Exception as e:
            logger.error(f"AWS SNS SMS failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'aws_sns'
            }


class TwilioSMSProvider(SMSProvider):
    """Twilio SMS provider implementation (fallback)"""
    
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


class AWSSESProvider(EmailProvider):
    """AWS SES email provider implementation"""
    
    def __init__(self):
        self.region_name = getattr(settings, 'AWS_REGION', 'us-east-1')
        self.access_key_id = getattr(settings, 'AWS_ACCESS_KEY_ID', '')
        self.secret_access_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', '')
        self.from_email = getattr(settings, 'AWS_SES_FROM_EMAIL', '')
        
        if not all([self.access_key_id, self.secret_access_key, self.from_email]):
            raise ValueError("AWS SES credentials not properly configured in settings")
        
        try:
            self.ses_client = boto3.client(
                'ses',
                region_name=self.region_name,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key
            )
            
            # Test connection and verify sender email
            response = self.ses_client.get_send_quota()
            logger.info(f"AWS SES client initialized successfully. Send quota: {response['Max24HourSend']}")
            
        except Exception as e:
            logger.error(f"Failed to initialize AWS SES client: {e}")
            raise
    
    def send_email(self, to: str, subject: str, text_content: str, html_content: str = None) -> Dict[str, Any]:
        try:
            # Prepare email body
            body = {'Text': {'Data': text_content, 'Charset': 'UTF-8'}}
            
            if html_content:
                body['Html'] = {'Data': html_content, 'Charset': 'UTF-8'}
            
            # Send email
            response = self.ses_client.send_email(
                Source=self.from_email,
                Destination={'ToAddresses': [to]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': body
                },
                # Add configuration set if available
                ConfigurationSetName=getattr(settings, 'AWS_SES_CONFIGURATION_SET', None) or None
            )
            
            return {
                'success': True,
                'message_id': response['MessageId'],
                'provider': 'aws_ses'
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"AWS SES email failed - {error_code}: {error_message}")
            
            return {
                'success': False,
                'error': f"{error_code}: {error_message}",
                'provider': 'aws_ses'
            }
        except Exception as e:
            logger.error(f"AWS SES email failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'aws_ses'
            }


class SendGridEmailProvider(EmailProvider):
    """SendGrid email provider implementation (fallback)"""
    
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
    """Django SMTP email provider implementation (fallback)"""
    
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


class AWSNotificationService:
    """
    AWS-powered notification service with SNS for SMS and SES for email
    Includes fallback providers for reliability
    """
    
    def __init__(self):
        self.sms_provider = None
        self.email_provider = None
        self.sms_fallback = None
        self.email_fallback = None
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize AWS providers with fallbacks"""
        
        # Initialize SMS providers (AWS SNS primary, Twilio fallback)
        try:
            self.sms_provider = AWSSNSProvider()
            logger.info("✅ AWS SNS SMS provider initialized")
        except Exception as e:
            logger.warning(f"AWS SNS initialization failed: {e}")
            
            # Try Twilio as fallback
            try:
                if TWILIO_AVAILABLE and hasattr(settings, 'TWILIO_ACCOUNT_SID'):
                    self.sms_fallback = TwilioSMSProvider()
                    logger.info("✅ Twilio SMS fallback provider initialized")
            except Exception as fallback_error:
                logger.warning(f"Twilio SMS fallback failed: {fallback_error}")
        
        # Initialize Email providers (AWS SES primary, SendGrid/Django fallback)
        try:
            self.email_provider = AWSSESProvider()
            logger.info("✅ AWS SES email provider initialized")
        except Exception as e:
            logger.warning(f"AWS SES initialization failed: {e}")
            
            # Try SendGrid as fallback
            try:
                if SENDGRID_AVAILABLE and hasattr(settings, 'SENDGRID_API_KEY'):
                    self.email_fallback = SendGridEmailProvider()
                    logger.info("✅ SendGrid email fallback provider initialized")
                else:
                    self.email_fallback = DjangoEmailProvider()
                    logger.info("✅ Django SMTP email fallback provider initialized")
            except Exception as fallback_error:
                logger.warning(f"Email fallback initialization failed: {fallback_error}")
                self.email_fallback = DjangoEmailProvider()
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all notification services"""
        return {
            'aws_sns': {
                'available': self.sms_provider is not None,
                'provider': 'AWS SNS',
                'status': 'active' if self.sms_provider else 'unavailable'
            },
            'aws_ses': {
                'available': self.email_provider is not None,
                'provider': 'AWS SES',
                'status': 'active' if self.email_provider else 'unavailable'
            },
            'sms_fallback': {
                'available': self.sms_fallback is not None,
                'provider': self.sms_fallback.__class__.__name__ if self.sms_fallback else None,
                'status': 'fallback' if self.sms_fallback else 'unavailable'
            },
            'email_fallback': {
                'available': self.email_fallback is not None,
                'provider': self.email_fallback.__class__.__name__ if self.email_fallback else None,
                'status': 'fallback' if self.email_fallback else 'unavailable'
            }
        }
    
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
        schedule_time: datetime = None,
        use_fallback: bool = True
    ) -> Dict[str, Any]:
        """
        Send notification via AWS services with fallback support
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
            user=user,
            use_fallback=use_fallback
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
        user: User = None,
        use_fallback: bool = True
    ) -> Dict[str, Any]:
        """Send notification immediately using AWS services"""
        results = {
            'email': None,
            'sms': None,
            'overall_success': False,
            'services_used': []
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
            
            # Send email via AWS SES
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
                        template, recipient_email, context_data, notification_type, user, use_fallback
                    )
                    if results['email']['success']:
                        results['services_used'].append(results['email']['provider'])
            
            # Send SMS via AWS SNS
            if recipient_phone and self.sms_provider:
                should_send_sms = True
                if preferences and 'appointment' in notification_type:
                    should_send_sms = preferences.sms_appointment_reminders
                
                # Respect quiet hours for non-critical notifications
                if notification_type not in ['emergency_alert', 'system_alert'] and self.check_quiet_hours():
                    logger.info(f"Skipping SMS during quiet hours for {notification_type}")
                elif should_send_sms:
                    results['sms'] = self._send_sms_notification(
                        template, recipient_phone, context_data, notification_type, user, use_fallback
                    )
                    if results['sms']['success']:
                        results['services_used'].append(results['sms']['provider'])
            
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
                'overall_success': False,
                'services_used': []
            }
    
    def _send_email_notification(
        self,
        template: NotificationTemplate,
        recipient_email: str,
        context_data: Dict[str, Any],
        notification_type: str,
        user: User = None,
        use_fallback: bool = True
    ) -> Dict[str, Any]:
        """Send email notification via AWS SES with fallback"""
        
        subject = self.render_template(template.subject_template, context_data)
        text_content = self.render_template(template.email_template, context_data)
        
        # Generate HTML content from text (can be enhanced with proper templates)
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{subject}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .footer {{ background-color: #f8f9fa; padding: 10px; text-align: center; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Healthcare Notification</h1>
            </div>
            <div class="content">
                {text_content.replace(chr(10), '<br>')}
            </div>
            <div class="footer">
                <p>This is an automated message from your healthcare provider.</p>
            </div>
        </body>
        </html>
        """
        
        # Try primary AWS SES provider
        if self.email_provider:
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
                service_used='ses',
                message_id=result.get('message_id', ''),
                error_message=result.get('error', '')
            )
            
            if result['success']:
                return result
            
            # If primary failed and fallback is enabled
            if not result['success'] and use_fallback and self.email_fallback:
                logger.warning(f"AWS SES failed, trying fallback: {result.get('error')}")
                
                fallback_result = self.email_fallback.send_email(
                    to=recipient_email,
                    subject=subject,
                    text_content=text_content,
                    html_content=html_content
                )
                
                # Log fallback attempt
                NotificationLog.objects.create(
                    notification_type=notification_type,
                    recipient=recipient_email,
                    user=user,
                    success=fallback_result['success'],
                    service_used=fallback_result.get('provider', 'unknown'),
                    message_id=fallback_result.get('message_id', ''),
                    error_message=fallback_result.get('error', '')
                )
                
                return fallback_result
            
            return result
        
        # No primary provider, use fallback if available
        elif use_fallback and self.email_fallback:
            result = self.email_fallback.send_email(
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
        
        else:
            error_msg = "No email provider available"
            NotificationLog.objects.create(
                notification_type=notification_type,
                recipient=recipient_email,
                user=user,
                success=False,
                service_used='none',
                error_message=error_msg
            )
            
            return {
                'success': False,
                'error': error_msg,
                'provider': 'none'
            }
    
    def _send_sms_notification(
        self,
        template: NotificationTemplate,
        recipient_phone: str,
        context_data: Dict[str, Any],
        notification_type: str,
        user: User = None,
        use_fallback: bool = True
    ) -> Dict[str, Any]:
        """Send SMS notification via AWS SNS with fallback"""
        
        if not template.sms_template:
            return {
                'success': False,
                'error': 'No SMS template configured',
                'provider': 'none'
            }
        
        message = self.render_template(template.sms_template, context_data)
        
        # Try primary AWS SNS provider
        if self.sms_provider:
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
                service_used='sns',
                message_id=result.get('message_id', ''),
                error_message=result.get('error', '')
            )
            
            if result['success']:
                return result
            
            # If primary failed and fallback is enabled
            if not result['success'] and use_fallback and self.sms_fallback:
                logger.warning(f"AWS SNS failed, trying fallback: {result.get('error')}")
                
                fallback_result = self.sms_fallback.send_sms(
                    to=recipient_phone,
                    message=message
                )
                
                # Log fallback attempt
                NotificationLog.objects.create(
                    notification_type=notification_type,
                    recipient=recipient_phone,
                    user=user,
                    success=fallback_result['success'],
                    service_used=fallback_result.get('provider', 'unknown'),
                    message_id=fallback_result.get('message_id', ''),
                    error_message=fallback_result.get('error', '')
                )
                
                return fallback_result
            
            return result
        
        # No primary provider, use fallback if available
        elif use_fallback and self.sms_fallback:
            result = self.sms_fallback.send_sms(
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
        
        else:
            error_msg = "No SMS provider available"
            NotificationLog.objects.create(
                notification_type=notification_type,
                recipient=recipient_phone,
                user=user,
                success=False,
                service_used='none',
                error_message=error_msg
            )
            
            return {
                'success': False,
                'error': error_msg,
                'provider': 'none'
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
                'message': f'Processed {processed} notifications via AWS services'
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
        """Send notifications to multiple recipients via AWS services"""
        results = {
            'total': len(recipients),
            'sent': 0,
            'failed': 0,
            'details': [],
            'services_used': set()
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
                if 'services_used' in result:
                    results['services_used'].update(result['services_used'])
            else:
                results['failed'] += 1
            
            results['details'].append({
                'recipient': recipient.get('email') or recipient.get('phone'),
                'success': result.get('overall_success', False),
                'error': result.get('error'),
                'services': result.get('services_used', [])
            })
        
        results['services_used'] = list(results['services_used'])
        return results


# Convenience function to get the AWS service instance
def get_aws_notification_service() -> AWSNotificationService:
    """Get an instance of the AWS notification service"""
    return AWSNotificationService()


# Maintain backward compatibility
def get_notification_service() -> AWSNotificationService:
    """Get an instance of the notification service (AWS-powered)"""
    return AWSNotificationService()
