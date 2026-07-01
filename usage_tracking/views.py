"""
Usage Tracking Views

API endpoints for usage tracking, analytics, and user dashboard integration.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
from datetime import datetime, timedelta

from .services import UsageTrackingService
from .models import (
    UsageCategory, UsageMetric, UserUsageProfile, 
    MonthlyUsageSummary, UsageAlert, UsageConfiguration
)

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_usage_event(request):
    """
    Track a usage event for the authenticated user
    
    POST /api/usage/track/
    {
        "metric_code": "patient_created",
        "category_code": "patient_management", // optional
        "event_type": "action", // optional
        "metadata": {}, // optional
        "session_id": "session_123" // optional
    }
    """
    try:
        data = request.data
        metric_code = data.get('metric_code')
        
        if not metric_code:
            return Response(
                {'error': 'metric_code is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get client IP
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
        if ip_address:
            ip_address = ip_address.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        success = UsageTrackingService.track_usage(
            user=request.user,
            metric_code=metric_code,
            category_code=data.get('category_code'),
            event_type=data.get('event_type', 'action'),
            metadata=data.get('metadata', {}),
            session_id=data.get('session_id'),
            ip_address=ip_address
        )
        
        if success:
            return Response({'status': 'success'}, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'error': 'Failed to track usage'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error in track_usage_event: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_usage_summary(request):
    """
    Get usage summary for the authenticated user
    
    GET /api/usage/summary/?year=2024&month=12
    """
    try:
        year = request.GET.get('year')
        month = request.GET.get('month')
        
        if year:
            year = int(year)
        if month:
            month = int(month)
        
        summary = UsageTrackingService.get_user_usage_summary(
            user=request.user,
            year=year,
            month=month
        )
        
        return Response(summary, status=status.HTTP_200_OK)
        
    except ValueError:
        return Response(
            {'error': 'Invalid year or month parameter'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error in get_usage_summary: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_usage_analytics(request):
    """
    Get advanced usage analytics for dashboard
    
    GET /api/usage/analytics/?days=30
    """
    try:
        days = int(request.GET.get('days', 30))
        
        if days < 1 or days > 365:
            return Response(
                {'error': 'Days parameter must be between 1 and 365'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        analytics = UsageTrackingService.get_usage_analytics(
            user=request.user,
            days=days
        )
        
        return Response(analytics, status=status.HTTP_200_OK)
        
    except ValueError:
        return Response(
            {'error': 'Invalid days parameter'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error in get_usage_analytics: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_month_counters(request):
    """
    Get current month usage counters for dashboard widgets
    
    GET /api/usage/counters/
    """
    try:
        now = timezone.now()
        summary = UsageTrackingService.get_user_usage_summary(
            user=request.user,
            year=now.year,
            month=now.month
        )
        
        # Extract key counters for dashboard widgets
        counters = {
            'total_usage': summary.get('total_usage_count', 0),
            'total_billing': summary.get('total_billable_amount', 0),
            'month_name': summary.get('month_name', now.strftime('%B')),
            'categories': {},
            'alerts_count': len(summary.get('alerts', []))
        }
        
        # Process category data for widgets
        categories_data = summary.get('categories', {})
        for category_code, metrics in categories_data.items():
            total_count = sum(metric['count'] for metric in metrics.values())
            total_amount = sum(metric['amount'] for metric in metrics.values())
            
            counters['categories'][category_code] = {
                'usage_count': total_count,
                'billing_amount': total_amount,
                'metrics': metrics
            }
        
        return Response(counters, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in get_current_month_counters: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_usage_alerts(request):
    """
    Get active usage alerts for the user
    
    GET /api/usage/alerts/
    """
    try:
        alerts = UsageAlert.objects.filter(
            user=request.user,
            is_read=False,
            is_dismissed=False
        ).select_related('metric', 'metric__category').order_by('-created_at')
        
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                'id': alert.id,
                'type': alert.alert_type,
                'level': alert.alert_level,
                'title': alert.title,
                'message': alert.message,
                'metric_name': alert.metric.metric_name if alert.metric else None,
                'category_name': alert.metric.category.category_name if alert.metric else None,
                'threshold_value': float(alert.threshold_value) if alert.threshold_value else None,
                'current_value': float(alert.current_value) if alert.current_value else None,
                'created_at': alert.created_at.isoformat()
            })
        
        return Response(alerts_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in get_usage_alerts: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def dismiss_alert(request, alert_id):
    """
    Dismiss a usage alert
    
    POST /api/usage/alerts/{alert_id}/dismiss/
    """
    try:
        alert = UsageAlert.objects.get(id=alert_id, user=request.user)
        alert.is_dismissed = True
        alert.save()
        
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
        
    except UsageAlert.DoesNotExist:
        return Response(
            {'error': 'Alert not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error in dismiss_alert: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_alert_read(request, alert_id):
    """
    Mark a usage alert as read
    
    POST /api/usage/alerts/{alert_id}/read/
    """
    try:
        alert = UsageAlert.objects.get(id=alert_id, user=request.user)
        alert.is_read = True
        alert.save()
        
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
        
    except UsageAlert.DoesNotExist:
        return Response(
            {'error': 'Alert not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error in mark_alert_read: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_usage_categories(request):
    """
    Get all available usage categories and metrics
    
    GET /api/usage/categories/
    """
    try:
        categories = UsageCategory.objects.filter(is_active=True).prefetch_related(
            'metrics'
        ).order_by('sort_order')
        
        categories_data = []
        for category in categories:
            metrics_data = []
            for metric in category.metrics.filter(is_active=True):
                metrics_data.append({
                    'metric_code': metric.metric_code,
                    'metric_name': metric.metric_name,
                    'description': metric.description,
                    'unit_cost': float(metric.unit_cost),
                    'is_billable': metric.is_billable,
                    'icon': metric.icon,
                    'color': metric.color
                })
            
            categories_data.append({
                'category_code': category.category_code,
                'category_name': category.category_name,
                'description': category.description,
                'icon': category.icon,
                'color': category.color,
                'sort_order': category.sort_order,
                'metrics': metrics_data
            })
        
        return Response(categories_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in get_usage_categories: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def user_usage_profile(request):
    """
    Get or update user usage profile settings
    
    GET /api/usage/profile/
    POST /api/usage/profile/
    {
        "usage_tracking_enabled": true,
        "monthly_limit": {
            "patient_management.patient_created": 100,
            "ai_diagnostics.ai_diagnosis": 50
        },
        "notification_preferences": {
            "email_alerts": true,
            "dashboard_alerts": true,
            "weekly_reports": true
        }
    }
    """
    try:
        profile, created = UserUsageProfile.objects.get_or_create(
            user=request.user,
            defaults={'usage_tracking_enabled': True}
        )
        
        if request.method == 'GET':
            return Response({
                'usage_tracking_enabled': profile.usage_tracking_enabled,
                'monthly_limit': profile.monthly_limit or {},
                'notification_preferences': profile.notification_preferences or {},
                'timezone': profile.timezone,
                'created_at': profile.created_at.isoformat(),
                'updated_at': profile.updated_at.isoformat()
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'POST':
            data = request.data
            
            if 'usage_tracking_enabled' in data:
                profile.usage_tracking_enabled = data['usage_tracking_enabled']
            
            if 'monthly_limit' in data:
                profile.monthly_limit = data['monthly_limit']
            
            if 'notification_preferences' in data:
                profile.notification_preferences = data['notification_preferences']
            
            if 'timezone' in data:
                profile.timezone = data['timezone']
            
            profile.save()
            
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in user_usage_profile: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initialize_usage_tracking(request):
    """
    Initialize usage tracking system with default categories and metrics
    
    POST /api/usage/initialize/
    """
    try:
        success = UsageTrackingService.initialize_default_metrics()
        
        if success:
            return Response({
                'status': 'success',
                'message': 'Usage tracking initialized successfully'
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Failed to initialize usage tracking'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error in initialize_usage_tracking: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Quick tracking endpoints for common actions
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_patient_action(request):
    """Quick endpoint for patient-related actions"""
    action = request.data.get('action', 'patient_access')
    return track_usage_event(request.__class__(
        'POST', 
        '/api/usage/track/', 
        data={
            'metric_code': action,
            'category_code': 'patient_management',
            'event_type': 'action',
            'metadata': request.data.get('metadata', {})
        }
    ))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_ai_action(request):
    """Quick endpoint for AI diagnostic actions"""
    action = request.data.get('action', 'ai_diagnosis')
    return track_usage_event(request.__class__(
        'POST', 
        '/api/usage/track/', 
        data={
            'metric_code': action,
            'category_code': 'ai_diagnostics',
            'event_type': 'action',
            'metadata': request.data.get('metadata', {})
        }
    ))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_widget_data(request):
    """
    Get condensed usage data for dashboard widgets
    
    GET /api/usage/dashboard/
    """
    try:
        now = timezone.now()
        
        # Get current month summary
        monthly_summary = UsageTrackingService.get_user_usage_summary(
            user=request.user,
            year=now.year,
            month=now.month
        )
        
        # Get 7-day analytics
        weekly_analytics = UsageTrackingService.get_usage_analytics(
            user=request.user,
            days=7
        )
        
        # Get active alerts count
        alerts_count = UsageAlert.objects.filter(
            user=request.user,
            is_read=False,
            is_dismissed=False
        ).count()
        
        widget_data = {
            'monthly_usage': monthly_summary.get('total_usage_count', 0),
            'monthly_billing': monthly_summary.get('total_billable_amount', 0),
            'weekly_usage': weekly_analytics.get('total_usage', 0),
            'weekly_billing': weekly_analytics.get('total_billing', 0),
            'usage_trend': weekly_analytics.get('usage_change_percent', 0),
            'billing_trend': weekly_analytics.get('billing_change_percent', 0),
            'alerts_count': alerts_count,
            'top_categories': weekly_analytics.get('category_breakdown', [])[:5],
            'daily_trends': weekly_analytics.get('daily_trends', [])
        }
        
        return Response(widget_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in dashboard_widget_data: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
