# Healthcare Platform Notification Integration
# Enhanced notification system with SMS and email capabilities

from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
import json
import logging
from datetime import datetime, timedelta
from django.utils import timezone

from .notification_system import notification_manager
from .models import NotificationLog, ScheduledNotification, NotificationPreference
from .aws_notification_service import get_aws_notification_service, get_notification_service

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_test_notification(request):
    """
    API endpoint to send test notifications for validation
    """
    try:
        notification_type = request.data.get('type', 'test')
        user = request.user
        
        if notification_type == 'registration_confirmation':
            user_data = {
                'first_name': user.first_name or 'Test',
                'last_name': user.last_name or 'User',
                'email': user.email,
            }
            result = notification_manager.send_registration_confirmation(user_data)
        
        elif notification_type == 'password_reset':
            result = notification_manager.send_password_reset_notification(
                email=user.email,
                reset_token='test-token-123',
                user_name=user.get_full_name() or user.username
            )
        
        elif notification_type == 'account_approved':
            user_data = {
                'first_name': user.first_name or 'Test',
                'last_name': user.last_name or 'User',
                'email': user.email,
            }
            result = notification_manager.send_account_approved_notification(user_data)
        
        else:
            return Response({'error': 'Invalid notification type'}, status=400)
        
        return Response({
            'success': result.get('success', False),
            'message': 'Test notification sent successfully' if result.get('success') else 'Failed to send notification',
            'details': result
        })
        
    except Exception as e:
        logger.error(f"Test notification failed: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_admin_notification(request):
    """
    API endpoint for admins to send notifications to users
    """
    try:
        notification_type = request.data.get('type')
        recipients = request.data.get('recipients', [])
        message = request.data.get('message', '')
        
        if notification_type == 'system_alert':
            alert_type = request.data.get('alert_type', 'General Alert')
            result = notification_manager.send_system_alert(
                admin_emails=recipients,
                alert_type=alert_type,
                message=message,
                priority='high'
            )
        
        elif notification_type == 'compliance_notification':
            compliance_type = request.data.get('compliance_type', 'GDPR')
            details = request.data.get('details', {})
            result = notification_manager.send_compliance_notification(
                recipients=recipients,
                compliance_type=compliance_type,
                details=details
            )
        
        else:
            return Response({'error': 'Invalid notification type'}, status=400)
        
        return Response({
            'success': result.get('success', False),
            'message': 'Admin notification sent successfully' if result.get('success') else 'Failed to send notification',
            'details': result
        })
        
    except Exception as e:
        logger.error(f"Admin notification failed: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notification_logs(request):
    """
    Get notification logs for the current user or all users (admin only)
    """
    try:
        user = request.user
        
        # Admin can see all logs, users can see only their own
        if user.is_staff or user.role == 'super_admin':
            logs = NotificationLog.objects.all()
        else:
            logs = NotificationLog.objects.filter(user=user)
        
        # Apply filters
        notification_type = request.GET.get('type')
        if notification_type:
            logs = logs.filter(notification_type=notification_type)
        
        success_filter = request.GET.get('success')
        if success_filter is not None:
            logs = logs.filter(success=success_filter.lower() == 'true')
        
        # Pagination
        page_size = int(request.GET.get('page_size', 20))
        offset = int(request.GET.get('offset', 0))
        
        total_count = logs.count()
        logs = logs[offset:offset + page_size]
        
        log_data = []
        for log in logs:
            log_data.append({
                'id': log.id,
                'notification_type': log.get_notification_type_display(),
                'recipient': log.recipient,
                'success': log.success,
                'service_used': log.get_service_used_display(),
                'timestamp': log.timestamp.isoformat(),
                'error_message': log.error_message,
            })
        
        return Response({
            'logs': log_data,
            'total_count': total_count,
            'has_more': offset + page_size < total_count
        })
        
    except Exception as e:
        logger.error(f"Failed to get notification logs: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_notification_preferences(request):
    """
    Update notification preferences for the current user
    """
    try:
        user = request.user
        preferences, created = NotificationPreference.objects.get_or_create(user=user)
        
        # Update preferences from request data
        preferences.email_appointment_reminders = request.data.get('email_appointment_reminders', preferences.email_appointment_reminders)
        preferences.sms_appointment_reminders = request.data.get('sms_appointment_reminders', preferences.sms_appointment_reminders)
        preferences.email_system_alerts = request.data.get('email_system_alerts', preferences.email_system_alerts)
        preferences.email_compliance_notifications = request.data.get('email_compliance_notifications', preferences.email_compliance_notifications)
        preferences.email_credential_warnings = request.data.get('email_credential_warnings', preferences.email_credential_warnings)
        
        preferences.save()
        
        return Response({
            'message': 'Notification preferences updated successfully',
            'preferences': {
                'email_appointment_reminders': preferences.email_appointment_reminders,
                'sms_appointment_reminders': preferences.sms_appointment_reminders,
                'email_system_alerts': preferences.email_system_alerts,
                'email_compliance_notifications': preferences.email_compliance_notifications,
                'email_credential_warnings': preferences.email_credential_warnings,
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to update notification preferences: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notification_preferences(request):
    """
    Get notification preferences for the current user
    """
    try:
        user = request.user
        preferences, created = NotificationPreference.objects.get_or_create(user=user)
        
        return Response({
            'preferences': {
                'email_appointment_reminders': preferences.email_appointment_reminders,
                'sms_appointment_reminders': preferences.sms_appointment_reminders,
                'email_system_alerts': preferences.email_system_alerts,
                'email_compliance_notifications': preferences.email_compliance_notifications,
                'email_credential_warnings': preferences.email_credential_warnings,
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get notification preferences: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def schedule_notification(request):
    """
    Schedule a notification to be sent at a specific time
    """
    try:
        notification_type = request.data.get('type')
        recipient_email = request.data.get('recipient_email', '')
        recipient_phone = request.data.get('recipient_phone', '')
        subject = request.data.get('subject', '')
        message_data = request.data.get('message_data', {})
        scheduled_time = request.data.get('scheduled_time')
        priority = request.data.get('priority', 'normal')
        
        if not (recipient_email or recipient_phone):
            return Response({'error': 'Either recipient_email or recipient_phone is required'}, status=400)
        
        # Parse scheduled time
        try:
            scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return Response({'error': 'Invalid scheduled_time format. Use ISO format.'}, status=400)
        
        # Create scheduled notification
        scheduled_notification = ScheduledNotification.objects.create(
            notification_type=notification_type,
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            subject=subject,
            message_data=message_data,
            scheduled_time=scheduled_datetime,
            priority=priority,
            user=request.user
        )
        
        return Response({
            'message': 'Notification scheduled successfully',
            'notification_id': scheduled_notification.id,
            'scheduled_time': scheduled_notification.scheduled_time.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to schedule notification: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_scheduled_notifications(request):
    """
    Get list of scheduled notifications
    """
    try:
        notifications = ScheduledNotification.objects.filter(status='pending').order_by('scheduled_time')
        
        notification_data = []
        for notification in notifications:
            notification_data.append({
                'id': notification.id,
                'notification_type': notification.notification_type,
                'recipient_email': notification.recipient_email,
                'recipient_phone': notification.recipient_phone,
                'subject': notification.subject,
                'scheduled_time': notification.scheduled_time.isoformat(),
                'priority': notification.priority,
                'status': notification.status,
                'attempts': notification.attempts,
            })
        
        return Response({
            'scheduled_notifications': notification_data,
            'total_count': len(notification_data)
        })
        
    except Exception as e:
        logger.error(f"Failed to get scheduled notifications: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def notification_system_status(request):
    """
    Get notification system status and statistics
    """
    try:
        from .notification_system import AWSNotificationService
        
        aws_service = AWSNotificationService()
        
        # Get statistics
        total_notifications = NotificationLog.objects.count()
        successful_notifications = NotificationLog.objects.filter(success=True).count()
        failed_notifications = NotificationLog.objects.filter(success=False).count()
        
        # Recent activity (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        recent_notifications = NotificationLog.objects.filter(timestamp__gte=yesterday).count()
        
        # Pending scheduled notifications
        pending_scheduled = ScheduledNotification.objects.filter(status='pending').count()
        
        return Response({
            'aws_service_available': aws_service.aws_enabled,
            'statistics': {
                'total_notifications': total_notifications,
                'successful_notifications': successful_notifications,
                'failed_notifications': failed_notifications,
                'success_rate': (successful_notifications / total_notifications * 100) if total_notifications > 0 else 0,
                'recent_notifications_24h': recent_notifications,
                'pending_scheduled': pending_scheduled,
            },
            'services': {
                'aws_ses_enabled': aws_service.ses_client is not None,
                'aws_sns_enabled': aws_service.sns_client is not None,
                'django_email_fallback': True,
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get notification system status: {e}")
        return Response({'error': str(e)}, status=500)


# Enhanced Notification Service Endpoints

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_enhanced_notification(request):
    """
    Send enhanced notification with SMS and email support
    """
    try:
        data = request.data
        service = get_notification_service()
        
        # Validate required fields
        notification_type = data.get('notification_type')
        if not notification_type:
            return Response(
                {'error': 'notification_type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        recipient_email = data.get('recipient_email')
        recipient_phone = data.get('recipient_phone')
        
        if not recipient_email and not recipient_phone:
            return Response(
                {'error': 'At least one of recipient_email or recipient_phone is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get target user if user_id provided
        target_user = None
        if data.get('user_id'):
            try:
                target_user = User.objects.get(id=data['user_id'])
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Send notification
        result = service.send_notification(
            notification_type=notification_type,
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            context_data=data.get('context_data', {}),
            user=target_user,
            priority=data.get('priority', 'normal'),
            schedule_time=None  # Immediate sending
        )
        
        return Response(result, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_appointment_reminder(request):
    """
    Send appointment reminder notification with SMS and email
    """
    try:
        data = request.data
        
        # Validate required fields
        required_fields = ['patient_email', 'appointment_date', 'appointment_time', 'doctor_name']
        for field in required_fields:
            if not data.get(field):
                return Response(
                    {'error': f'{field} is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        service = get_notification_service()
        
        context_data = {
            'patient_name': data.get('patient_name', 'Patient'),
            'appointment_date': data['appointment_date'],
            'appointment_time': data['appointment_time'],
            'doctor_name': data['doctor_name'],
            'clinic_name': data.get('clinic_name', 'Healthcare Clinic'),
            'clinic_address': data.get('clinic_address', '')
        }
        
        # Parse schedule time if provided
        schedule_time = None
        if data.get('schedule_time'):
            try:
                schedule_time = datetime.fromisoformat(data['schedule_time'].replace('Z', '+00:00'))
            except ValueError:
                return Response(
                    {'error': 'Invalid schedule_time format. Use ISO format.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        result = service.send_notification(
            notification_type='appointment_reminder',
            recipient_email=data['patient_email'],
            recipient_phone=data.get('patient_phone'),
            context_data=context_data,
            schedule_time=schedule_time
        )
        
        return Response(result, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_test_results_notification(request):
    """
    Send test results available notification
    """
    try:
        data = request.data
        
        required_fields = ['patient_email', 'test_name']
        for field in required_fields:
            if not data.get(field):
                return Response(
                    {'error': f'{field} is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        service = get_notification_service()
        
        context_data = {
            'patient_name': data.get('patient_name', 'Patient'),
            'test_name': data['test_name'],
            'results_url': data.get('results_url', ''),
            'clinic_name': data.get('clinic_name', 'Healthcare Clinic')
        }
        
        result = service.send_notification(
            notification_type='test_results',
            recipient_email=data['patient_email'],
            recipient_phone=data.get('patient_phone'),
            context_data=context_data
        )
        
        return Response(result, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_emergency_alert(request):
    """
    Send emergency alert notification (bypasses quiet hours)
    """
    try:
        data = request.data
        
        if not data.get('emergency_message'):
            return Response(
                {'error': 'emergency_message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not data.get('recipient_email') and not data.get('recipient_phone'):
            return Response(
                {'error': 'At least one recipient contact method is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = get_notification_service()
        
        context_data = {
            'emergency_message': data['emergency_message'],
            'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        result = service.send_notification(
            notification_type='emergency_alert',
            recipient_email=data.get('recipient_email'),
            recipient_phone=data.get('recipient_phone'),
            context_data=context_data,
            priority='critical'
        )
        
        return Response(result, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_bulk_notifications(request):
    """
    Send notifications to multiple recipients
    """
    try:
        data = request.data
        service = get_notification_service()
        
        notification_type = data.get('notification_type')
        recipients = data.get('recipients', [])
        
        if not notification_type or not recipients:
            return Response(
                {'error': 'notification_type and recipients are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(recipients) > 100:
            return Response(
                {'error': 'Maximum 100 recipients allowed per request'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = service.send_bulk_notifications(
            notification_type=notification_type,
            recipients=recipients,
            context_data=data.get('context_data', {})
        )
        
        return Response(result, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def process_notification_queue(request):
    """
    Manually process the notification queue
    """
    try:
        service = get_notification_service()
        batch_size = request.data.get('batch_size', 50)
        
        result = service.process_scheduled_notifications(batch_size=batch_size)
        return Response(result)
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
