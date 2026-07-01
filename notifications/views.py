# backend/notifications/views.py

import json
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from .models import (
    NotificationTemplate, NotificationPreference, NotificationLog,
    SMSProvider, EmailProvider, NotificationQueue
)
from .services import NotificationService, send_appointment_reminder, send_test_results_notification
from .serializers import (
    NotificationTemplateSerializer, NotificationPreferenceSerializer,
    NotificationLogSerializer, SendNotificationSerializer
)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def notification_templates(request):
    """
    GET: List all notification templates
    POST: Create a new notification template
    """
    if request.method == 'GET':
        templates = NotificationTemplate.objects.filter(is_active=True)
        template_type = request.GET.get('template_type')
        if template_type:
            templates = templates.filter(template_type=template_type)
        
        serializer = NotificationTemplateSerializer(templates, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        })
    
    elif request.method == 'POST':
        if not request.user.is_staff:
            return Response({
                'status': 'error',
                'message': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = NotificationTemplateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'status': 'error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def notification_template_detail(request, template_id):
    """
    GET: Get notification template details
    PUT: Update notification template
    DELETE: Delete notification template
    """
    template = get_object_or_404(NotificationTemplate, id=template_id)
    
    if request.method == 'GET':
        serializer = NotificationTemplateSerializer(template)
        return Response({
            'status': 'success',
            'data': serializer.data
        })
    
    elif request.method == 'PUT':
        if not request.user.is_staff:
            return Response({
                'status': 'error',
                'message': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = NotificationTemplateSerializer(template, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'data': serializer.data
            })
        else:
            return Response({
                'status': 'error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        if not request.user.is_staff:
            return Response({
                'status': 'error',
                'message': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        template.is_active = False
        template.save()
        return Response({
            'status': 'success',
            'message': 'Template deactivated successfully'
        })


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_notification_preferences(request):
    """
    GET: Get current user's notification preferences
    PUT: Update current user's notification preferences
    """
    preferences, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'GET':
        serializer = NotificationPreferenceSerializer(preferences)
        return Response({
            'status': 'success',
            'data': serializer.data
        })
    
    elif request.method == 'PUT':
        serializer = NotificationPreferenceSerializer(preferences, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'data': serializer.data
            })
        else:
            return Response({
                'status': 'error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_notification(request):
    """
    Send a notification to one or more users
    """
    serializer = SendNotificationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    service = NotificationService()
    
    try:
        # Get recipients
        if 'recipient_ids' in data:
            recipients = User.objects.filter(id__in=data['recipient_ids'])
        elif 'recipient_id' in data:
            recipients = [User.objects.get(id=data['recipient_id'])]
        else:
            return Response({
                'status': 'error',
                'message': 'No recipients specified'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse scheduled_for if provided
        scheduled_for = None
        if data.get('scheduled_for'):
            try:
                scheduled_for = datetime.fromisoformat(data['scheduled_for'].replace('Z', '+00:00'))
            except ValueError:
                return Response({
                    'status': 'error',
                    'message': 'Invalid scheduled_for format. Use ISO 8601 format.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Send notifications
        if len(recipients) == 1:
            results = service.send_notification(
                recipient=recipients[0],
                template_type=data['template_type'],
                context_data=data.get('context_data', {}),
                notification_types=data.get('notification_types', ['email', 'sms']),
                scheduled_for=scheduled_for,
                priority=data.get('priority', 'normal'),
                sender=request.user
            )
        else:
            results = service.send_bulk_notification(
                recipients=list(recipients),
                template_type=data['template_type'],
                context_data=data.get('context_data', {}),
                notification_types=data.get('notification_types', ['email', 'sms']),
                scheduled_for=scheduled_for,
                priority=data.get('priority', 'normal')
            )
        
        return Response({
            'status': 'success',
            'data': results,
            'message': 'Notifications processed successfully'
        })
        
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'One or more recipients not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Error sending notifications: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_history(request):
    """
    Get notification history for current user
    """
    notifications = NotificationLog.objects.filter(recipient=request.user)
    
    # Filtering
    notification_type = request.GET.get('type')
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)
    
    status_filter = request.GET.get('status')
    if status_filter:
        notifications = notifications.filter(status=status_filter)
    
    # Date range filtering
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            notifications = notifications.filter(created_at__date__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            notifications = notifications.filter(created_at__date__lte=date_to)
        except ValueError:
            pass
    
    # Pagination
    page = request.GET.get('page', 1)
    page_size = min(int(request.GET.get('page_size', 20)), 100)
    
    paginator = Paginator(notifications, page_size)
    page_obj = paginator.get_page(page)
    
    serializer = NotificationLogSerializer(page_obj.object_list, many=True)
    
    return Response({
        'status': 'success',
        'data': {
            'notifications': serializer.data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        }
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_notification_stats(request):
    """
    Get notification statistics for admins
    """
    # Date range for stats (default to last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        try:
            start_date = datetime.strptime(date_from, '%Y-%m-%d')
            start_date = timezone.make_aware(start_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            end_date = datetime.strptime(date_to, '%Y-%m-%d')
            end_date = timezone.make_aware(end_date) + timedelta(days=1)
        except ValueError:
            pass
    
    # Base queryset
    notifications = NotificationLog.objects.filter(
        created_at__gte=start_date,
        created_at__lt=end_date
    )
    
    # Basic stats
    total_notifications = notifications.count()
    email_count = notifications.filter(notification_type='email').count()
    sms_count = notifications.filter(notification_type='sms').count()
    
    # Status breakdown
    status_stats = notifications.values('status').annotate(count=Count('id'))
    
    # Daily breakdown
    daily_stats = []
    current_date = start_date.date()
    while current_date < end_date.date():
        day_notifications = notifications.filter(
            created_at__date=current_date
        )
        daily_stats.append({
            'date': current_date.isoformat(),
            'total': day_notifications.count(),
            'email': day_notifications.filter(notification_type='email').count(),
            'sms': day_notifications.filter(notification_type='sms').count(),
            'sent': day_notifications.filter(status='sent').count(),
            'failed': day_notifications.filter(status='failed').count()
        })
        current_date += timedelta(days=1)
    
    # Template usage
    template_stats = notifications.filter(
        template__isnull=False
    ).values('template__name', 'template__template_type').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Queue stats
    queue_pending = NotificationQueue.objects.filter(processed_at__isnull=True).count()
    queue_processing = NotificationQueue.objects.filter(
        processing_started__isnull=False,
        processed_at__isnull=True
    ).count()
    
    return Response({
        'status': 'success',
        'data': {
            'summary': {
                'total_notifications': total_notifications,
                'email_count': email_count,
                'sms_count': sms_count,
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
            },
            'status_breakdown': list(status_stats),
            'daily_stats': daily_stats,
            'template_usage': list(template_stats),
            'queue_stats': {
                'pending': queue_pending,
                'processing': queue_processing
            }
        }
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def process_notification_queue(request):
    """
    Manually trigger notification queue processing
    """
    limit = request.data.get('limit', 100)
    
    try:
        service = NotificationService()
        results = service.process_queue(limit=limit)
        
        return Response({
            'status': 'success',
            'data': results,
            'message': f"Processed {results['processed']} notifications"
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Error processing queue: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def email_providers(request):
    """
    GET: List email providers
    POST: Create new email provider
    """
    if request.method == 'GET':
        providers = EmailProvider.objects.all()
        data = []
        for provider in providers:
            data.append({
                'id': provider.id,
                'name': provider.name,
                'provider_type': provider.provider_type,
                'is_active': provider.is_active,
                'is_default': provider.is_default,
                'from_email': provider.from_email,
                'from_name': provider.from_name
            })
        
        return Response({
            'status': 'success',
            'data': data
        })
    
    elif request.method == 'POST':
        try:
            provider = EmailProvider.objects.create(
                name=request.data['name'],
                provider_type=request.data['provider_type'],
                from_email=request.data['from_email'],
                from_name=request.data.get('from_name', 'Healthcare Platform'),
                api_key=request.data.get('api_key', ''),
                smtp_host=request.data.get('smtp_host', ''),
                smtp_port=request.data.get('smtp_port'),
                smtp_username=request.data.get('smtp_username', ''),
                smtp_password=request.data.get('smtp_password', ''),
                smtp_use_tls=request.data.get('smtp_use_tls', True),
                is_default=request.data.get('is_default', False)
            )
            
            return Response({
                'status': 'success',
                'data': {'id': provider.id, 'name': provider.name},
                'message': 'Email provider created successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error creating email provider: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def sms_providers(request):
    """
    GET: List SMS providers
    POST: Create new SMS provider
    """
    if request.method == 'GET':
        providers = SMSProvider.objects.all()
        data = []
        for provider in providers:
            data.append({
                'id': provider.id,
                'name': provider.name,
                'provider_type': provider.provider_type,
                'is_active': provider.is_active,
                'is_default': provider.is_default,
                'sender_id': provider.sender_id
            })
        
        return Response({
            'status': 'success',
            'data': data
        })
    
    elif request.method == 'POST':
        try:
            provider = SMSProvider.objects.create(
                name=request.data['name'],
                provider_type=request.data['provider_type'],
                api_key=request.data.get('api_key', ''),
                api_secret=request.data.get('api_secret', ''),
                account_sid=request.data.get('account_sid', ''),
                sender_id=request.data.get('sender_id', ''),
                is_default=request.data.get('is_default', False)
            )
            
            return Response({
                'status': 'success',
                'data': {'id': provider.id, 'name': provider.name},
                'message': 'SMS provider created successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error creating SMS provider: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


# Healthcare-specific notification endpoints

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_appointment_reminder_api(request):
    """
    Send appointment reminder notification
    """
    try:
        appointment_id = request.data.get('appointment_id')
        hours_before = request.data.get('hours_before', 24)
        
        # This would integrate with your appointment model
        # For now, we'll create a mock appointment object
        patient_id = request.data.get('patient_id')
        patient = User.objects.get(id=patient_id)
        
        context_data = {
            'patient_name': patient.get_full_name(),
            'appointment_date': request.data.get('appointment_date', 'TBD'),
            'appointment_time': request.data.get('appointment_time', 'TBD'),
            'doctor_name': request.data.get('doctor_name', 'Dr. Smith'),
            'clinic_name': request.data.get('clinic_name', 'Healthcare Clinic'),
        }
        
        service = NotificationService()
        results = service.send_notification(
            recipient=patient,
            template_type='appointment_reminder',
            context_data=context_data,
            priority='normal'
        )
        
        return Response({
            'status': 'success',
            'data': results,
            'message': 'Appointment reminder sent successfully'
        })
        
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Patient not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Error sending appointment reminder: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_test_results_api(request):
    """
    Send test results available notification
    """
    try:
        patient_id = request.data.get('patient_id')
        patient = User.objects.get(id=patient_id)
        
        context_data = {
            'patient_name': patient.get_full_name(),
            'test_name': request.data.get('test_name', 'Laboratory Test'),
            'results_url': request.data.get('results_url', '#'),
            'clinic_name': request.data.get('clinic_name', 'Healthcare Clinic'),
        }
        
        service = NotificationService()
        results = service.send_notification(
            recipient=patient,
            template_type='test_results',
            context_data=context_data,
            priority='high'
        )
        
        return Response({
            'status': 'success',
            'data': results,
            'message': 'Test results notification sent successfully'
        })
        
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Patient not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Error sending test results notification: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Web interface views (for admin panel)

@staff_member_required
def notification_dashboard(request):
    """
    Admin dashboard for notification management
    """
    # Get some basic stats
    total_notifications = NotificationLog.objects.count()
    pending_queue = NotificationQueue.objects.filter(processed_at__isnull=True).count()
    
    # Recent notifications
    recent_notifications = NotificationLog.objects.select_related('recipient', 'template').order_by('-created_at')[:10]
    
    context = {
        'total_notifications': total_notifications,
        'pending_queue': pending_queue,
        'recent_notifications': recent_notifications,
    }
    
    return render(request, 'notifications/dashboard.html', context)
