# Healthcare Platform Notification Management Commands
# Django management command to process scheduled notifications

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import models
from datetime import datetime, timedelta
import logging

from hospital.models import ScheduledNotification
from hospital.notification_system import notification_manager

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process scheduled notifications that are due to be sent'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually sending notifications',
        )
        parser.add_argument(
            '--max-notifications',
            type=int,
            default=100,
            help='Maximum number of notifications to process in one run',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        max_notifications = options['max_notifications']
        
        # Get current time
        now = timezone.now()
        
        # Find notifications that are due to be sent
        due_notifications = ScheduledNotification.objects.filter(
            status='pending',
            scheduled_time__lte=now,
            attempts__lt=models.F('max_attempts')
        ).order_by('priority', 'scheduled_time')[:max_notifications]
        
        if not due_notifications:
            self.stdout.write(
                self.style.SUCCESS('No notifications due to be processed.')
            )
            return
        
        self.stdout.write(
            f'Found {len(due_notifications)} notifications to process.'
        )
        
        processed_count = 0
        success_count = 0
        failed_count = 0
        
        for notification in due_notifications:
            processed_count += 1
            
            if dry_run:
                self.stdout.write(
                    f'[DRY RUN] Would process: {notification.notification_type} to {notification.recipient_email or notification.recipient_phone}'
                )
                continue
            
            try:
                # Update attempts
                notification.attempts += 1
                notification.last_attempt = now
                
                # Determine notification method and send
                result = None
                
                if notification.notification_type == 'appointment_reminder':
                    if notification.recipient_email and notification.recipient_phone:
                        # Send both email and SMS reminder
                        patient_data = {
                            'email': notification.recipient_email,
                            'phone_number': notification.recipient_phone,
                            'first_name': notification.message_data.get('patient_first_name', ''),
                            'last_name': notification.message_data.get('patient_last_name', '')
                        }
                        appointment_data = {
                            'doctor_name': notification.message_data.get('doctor_name', ''),
                            'date': notification.message_data.get('appointment_date', ''),
                            'time': notification.message_data.get('appointment_time', ''),
                            'clinic_name': notification.message_data.get('clinic_name', ''),
                            'clinic_address': notification.message_data.get('clinic_address', '')
                        }
                        result = notification_manager.send_appointment_reminder(patient_data, appointment_data)
                
                elif notification.notification_type == 'credential_expiry_warning':
                    professional_data = {
                        'email': notification.recipient_email,
                        'first_name': notification.message_data.get('first_name', ''),
                        'last_name': notification.message_data.get('last_name', '')
                    }
                    credential_type = notification.message_data.get('credential_type', '')
                    expiry_date = notification.message_data.get('expiry_date', '')
                    result = notification_manager.send_credential_expiry_warning(
                        professional_data, credential_type, expiry_date
                    )
                
                elif notification.notification_type == 'system_alert':
                    admin_emails = [notification.recipient_email] if notification.recipient_email else []
                    alert_type = notification.message_data.get('alert_type', 'System Alert')
                    message = notification.message_data.get('message', '')
                    priority = notification.priority
                    result = notification_manager.send_system_alert(admin_emails, alert_type, message, priority)
                
                # Process result
                if result and result.get('success'):
                    notification.status = 'sent'
                    notification.sent_at = now
                    notification.error_message = ''
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Sent: {notification.notification_type} to {notification.recipient_email or notification.recipient_phone}')
                    )
                else:
                    error_message = result.get('error', 'Unknown error') if result else 'No result returned'
                    notification.error_message = error_message
                    
                    # Mark as failed if max attempts reached
                    if notification.attempts >= notification.max_attempts:
                        notification.status = 'failed'
                        failed_count += 1
                        self.stdout.write(
                            self.style.ERROR(f'✗ Failed (max attempts): {notification.notification_type} to {notification.recipient_email or notification.recipient_phone} - {error_message}')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'⚠ Failed (will retry): {notification.notification_type} to {notification.recipient_email or notification.recipient_phone} - {error_message}')
                        )
                
                notification.save()
                
            except Exception as e:
                notification.error_message = str(e)
                notification.save()
                logger.error(f"Error processing notification {notification.id}: {e}")
                self.stdout.write(
                    self.style.ERROR(f'✗ Error: {notification.notification_type} - {str(e)}')
                )
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nProcessing complete:\n'
                    f'Total processed: {processed_count}\n'
                    f'Successfully sent: {success_count}\n'
                    f'Failed: {failed_count}\n'
                    f'Pending retry: {processed_count - success_count - failed_count}'
                )
            )
