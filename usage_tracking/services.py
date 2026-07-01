"""
Usage Tracking Service

Advanced service for tracking user usage, calculating billing,
and providing real-time analytics with soft-coded configuration.
"""

from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum, Count, Q, F
from django.db import transaction
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import logging
from typing import Dict, List, Optional, Any
import json

from .models import (
    UsageCategory, UsageMetric, UserUsageProfile, MonthlyUsageSummary,
    DailyUsageRecord, UsageEvent, UsageAlert, UsageConfiguration
)

logger = logging.getLogger(__name__)


class UsageTrackingService:
    """
    Comprehensive usage tracking and analytics service
    """

    @staticmethod
    def track_usage(user: User, metric_code: str, category_code: str = None, 
                   event_type: str = 'action', metadata: Dict = None,
                   session_id: str = None, ip_address: str = None) -> bool:
        """
        Track a usage event for a user
        
        Args:
            user: Django User instance
            metric_code: Code for the specific metric being tracked
            category_code: Optional category code if metric_code is not unique
            event_type: Type of event (access, action, creation, etc.)
            metadata: Additional event data
            session_id: User session identifier
            ip_address: User's IP address
            
        Returns:
            bool: Success status
        """
        try:
            # Get or create usage profile
            profile, _ = UserUsageProfile.objects.get_or_create(
                user=user,
                defaults={'usage_tracking_enabled': True}
            )
            
            if not profile.usage_tracking_enabled:
                return False
            
            # Find the metric
            metric_query = UsageMetric.objects.filter(metric_code=metric_code, is_active=True)
            if category_code:
                metric_query = metric_query.filter(category__category_code=category_code)
            
            metric = metric_query.first()
            if not metric:
                logger.warning(f"Metric not found: {metric_code} in category {category_code}")
                return False
            
            # Create usage event
            event = UsageEvent.objects.create(
                user=user,
                metric=metric,
                event_type=event_type,
                session_id=session_id or '',
                ip_address=ip_address,
                event_data=metadata or {},
                is_billable=metric.is_billable
            )
            
            # Update daily usage record
            today = timezone.now().date()
            daily_record, created = DailyUsageRecord.objects.get_or_create(
                user=user,
                metric=metric,
                date=today,
                defaults={
                    'usage_count': 0,
                    'billable_amount': Decimal('0.00')
                }
            )
            
            # Increment usage count
            daily_record.usage_count = F('usage_count') + 1
            if metric.is_billable:
                daily_record.billable_amount = F('billable_amount') + metric.unit_cost
            daily_record.save()
            
            # Update monthly summary
            UsageTrackingService._update_monthly_summary(user, metric, today)
            
            # Check for alerts
            UsageTrackingService._check_usage_alerts(user, metric, daily_record)
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking usage for {user.username}: {str(e)}")
            return False

    @staticmethod
    def _update_monthly_summary(user: User, metric: UsageMetric, date: datetime.date):
        """Update monthly usage summary"""
        try:
            summary, created = MonthlyUsageSummary.objects.get_or_create(
                user=user,
                year=date.year,
                month=date.month,
                defaults={
                    'total_usage_count': 0,
                    'total_billable_amount': Decimal('0.00'),
                    'usage_data': {}
                }
            )
            
            # Update summary counts
            summary.total_usage_count = F('total_usage_count') + 1
            if metric.is_billable:
                summary.total_billable_amount = F('total_billable_amount') + metric.unit_cost
            
            # Update category-specific data
            usage_data = summary.usage_data
            category_code = metric.category.category_code
            metric_code = metric.metric_code
            
            if category_code not in usage_data:
                usage_data[category_code] = {}
            if metric_code not in usage_data[category_code]:
                usage_data[category_code][metric_code] = {'count': 0, 'amount': 0}
            
            usage_data[category_code][metric_code]['count'] += 1
            if metric.is_billable:
                usage_data[category_code][metric_code]['amount'] += float(metric.unit_cost)
            
            summary.usage_data = usage_data
            summary.save()
            
        except Exception as e:
            logger.error(f"Error updating monthly summary: {str(e)}")

    @staticmethod
    def _check_usage_alerts(user: User, metric: UsageMetric, daily_record: DailyUsageRecord):
        """Check if usage alerts should be triggered"""
        try:
            profile = user.usage_profile
            monthly_limits = profile.monthly_limit
            
            if not monthly_limits:
                return
            
            category_code = metric.category.category_code
            metric_code = metric.metric_code
            
            # Check if there's a limit for this metric
            limit_key = f"{category_code}.{metric_code}"
            if limit_key not in monthly_limits:
                return
            
            limit = monthly_limits[limit_key]
            
            # Get current month usage
            today = timezone.now().date()
            current_usage = DailyUsageRecord.objects.filter(
                user=user,
                metric=metric,
                date__year=today.year,
                date__month=today.month
            ).aggregate(total=Sum('usage_count'))['total'] or 0
            
            # Check thresholds
            warning_threshold = limit * 0.8  # 80% warning
            
            if current_usage >= limit:
                UsageAlert.objects.get_or_create(
                    user=user,
                    metric=metric,
                    alert_type='limit_exceeded',
                    defaults={
                        'alert_level': 'error',
                        'title': f'{metric.metric_name} Limit Exceeded',
                        'message': f'You have exceeded your monthly limit of {limit} for {metric.metric_name}.',
                        'threshold_value': Decimal(str(limit)),
                        'current_value': Decimal(str(current_usage))
                    }
                )
            elif current_usage >= warning_threshold:
                UsageAlert.objects.get_or_create(
                    user=user,
                    metric=metric,
                    alert_type='limit_warning',
                    defaults={
                        'alert_level': 'warning',
                        'title': f'{metric.metric_name} Approaching Limit',
                        'message': f'You have used {current_usage} of {limit} {metric.metric_name} this month.',
                        'threshold_value': Decimal(str(warning_threshold)),
                        'current_value': Decimal(str(current_usage))
                    }
                )
                
        except Exception as e:
            logger.error(f"Error checking usage alerts: {str(e)}")

    @staticmethod
    def get_user_usage_summary(user: User, year: int = None, month: int = None) -> Dict:
        """
        Get comprehensive usage summary for a user
        
        Args:
            user: Django User instance
            year: Specific year (defaults to current year)
            month: Specific month (defaults to current month)
            
        Returns:
            Dict: Usage summary with detailed breakdown
        """
        now = timezone.now()
        year = year or now.year
        month = month or now.month
        
        try:
            # Get monthly summary
            summary = MonthlyUsageSummary.objects.filter(
                user=user,
                year=year,
                month=month
            ).first()
            
            if not summary:
                return {
                    'year': year,
                    'month': month,
                    'month_name': datetime(year, month, 1).strftime('%B'),
                    'total_usage_count': 0,
                    'total_billable_amount': 0,
                    'categories': {},
                    'daily_breakdown': [],
                    'alerts': []
                }
            
            # Get daily breakdown
            daily_records = DailyUsageRecord.objects.filter(
                user=user,
                date__year=year,
                date__month=month
            ).select_related('metric', 'metric__category').order_by('date')
            
            daily_breakdown = []
            for record in daily_records:
                daily_breakdown.append({
                    'date': record.date.isoformat(),
                    'metric_name': record.metric.metric_name,
                    'category_name': record.metric.category.category_name,
                    'usage_count': record.usage_count,
                    'billable_amount': float(record.billable_amount)
                })
            
            # Get active alerts
            alerts = UsageAlert.objects.filter(
                user=user,
                is_read=False,
                is_dismissed=False
            ).order_by('-created_at')[:10]
            
            alert_data = []
            for alert in alerts:
                alert_data.append({
                    'id': alert.id,
                    'type': alert.alert_type,
                    'level': alert.alert_level,
                    'title': alert.title,
                    'message': alert.message,
                    'created_at': alert.created_at.isoformat()
                })
            
            return {
                'year': year,
                'month': month,
                'month_name': summary.month_name,
                'total_usage_count': summary.total_usage_count,
                'total_billable_amount': float(summary.total_billable_amount),
                'categories': summary.usage_data,
                'daily_breakdown': daily_breakdown,
                'alerts': alert_data,
                'is_finalized': summary.is_finalized
            }
            
        except Exception as e:
            logger.error(f"Error getting usage summary for {user.username}: {str(e)}")
            return {}

    @staticmethod
    def get_usage_analytics(user: User, days: int = 30) -> Dict:
        """
        Get advanced usage analytics for dashboard
        
        Args:
            user: Django User instance
            days: Number of days to analyze
            
        Returns:
            Dict: Analytics data with trends and insights
        """
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        try:
            # Get usage trends
            daily_usage = DailyUsageRecord.objects.filter(
                user=user,
                date__gte=start_date,
                date__lte=end_date
            ).values('date').annotate(
                total_count=Sum('usage_count'),
                total_amount=Sum('billable_amount')
            ).order_by('date')
            
            # Get category breakdown
            category_usage = DailyUsageRecord.objects.filter(
                user=user,
                date__gte=start_date,
                date__lte=end_date
            ).values(
                'metric__category__category_name',
                'metric__category__category_code',
                'metric__category__icon',
                'metric__category__color'
            ).annotate(
                total_count=Sum('usage_count'),
                total_amount=Sum('billable_amount')
            ).order_by('-total_count')
            
            # Get top metrics
            metric_usage = DailyUsageRecord.objects.filter(
                user=user,
                date__gte=start_date,
                date__lte=end_date
            ).values(
                'metric__metric_name',
                'metric__metric_code',
                'metric__icon',
                'metric__color'
            ).annotate(
                total_count=Sum('usage_count'),
                total_amount=Sum('billable_amount')
            ).order_by('-total_count')[:10]
            
            # Calculate trends
            prev_start = start_date - timedelta(days=days)
            prev_end = start_date - timedelta(days=1)
            
            prev_usage = DailyUsageRecord.objects.filter(
                user=user,
                date__gte=prev_start,
                date__lte=prev_end
            ).aggregate(
                total_count=Sum('usage_count'),
                total_amount=Sum('billable_amount')
            )
            
            current_usage = DailyUsageRecord.objects.filter(
                user=user,
                date__gte=start_date,
                date__lte=end_date
            ).aggregate(
                total_count=Sum('usage_count'),
                total_amount=Sum('billable_amount')
            )
            
            # Calculate percentage changes
            def calc_change(current, previous):
                if not previous or previous == 0:
                    return 100 if current > 0 else 0
                return ((current - previous) / previous) * 100
            
            usage_change = calc_change(
                current_usage['total_count'] or 0,
                prev_usage['total_count'] or 0
            )
            
            billing_change = calc_change(
                float(current_usage['total_amount'] or 0),
                float(prev_usage['total_amount'] or 0)
            )
            
            return {
                'period_days': days,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'daily_trends': list(daily_usage),
                'category_breakdown': list(category_usage),
                'top_metrics': list(metric_usage),
                'total_usage': current_usage['total_count'] or 0,
                'total_billing': float(current_usage['total_amount'] or 0),
                'usage_change_percent': round(usage_change, 2),
                'billing_change_percent': round(billing_change, 2),
                'avg_daily_usage': round((current_usage['total_count'] or 0) / days, 2),
                'avg_daily_billing': round(float(current_usage['total_amount'] or 0) / days, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting usage analytics: {str(e)}")
            return {}

    @staticmethod
    def initialize_default_metrics():
        """Initialize default usage categories and metrics"""
        try:
            # Healthcare-specific categories
            categories_data = [
                {
                    'category_code': 'patient_management',
                    'category_name': 'Patient Management',
                    'description': 'Patient records, appointments, and care management',
                    'icon': 'ri-user-heart-line',
                    'color': 'primary',
                    'sort_order': 1
                },
                {
                    'category_code': 'ai_diagnostics',
                    'category_name': 'AI Diagnostics',
                    'description': 'AI-powered diagnostic tools and analysis',
                    'icon': 'ri-robot-2-line',
                    'color': 'success',
                    'sort_order': 2
                },
                {
                    'category_code': 'radiology',
                    'category_name': 'Radiology Services',
                    'description': 'Medical imaging and radiology analysis',
                    'icon': 'ri-scan-line',
                    'color': 'info',
                    'sort_order': 3
                },
                {
                    'category_code': 'laboratory',
                    'category_name': 'Laboratory Services',
                    'description': 'Lab tests and pathology analysis',
                    'icon': 'ri-test-tube-line',
                    'color': 'warning',
                    'sort_order': 4
                },
                {
                    'category_code': 'telemedicine',
                    'category_name': 'Telemedicine',
                    'description': 'Virtual consultations and remote care',
                    'icon': 'ri-video-chat-line',
                    'color': 'secondary',
                    'sort_order': 5
                },
                {
                    'category_code': 'reports',
                    'category_name': 'Reports & Analytics',
                    'description': 'Report generation and data analytics',
                    'icon': 'ri-file-chart-line',
                    'color': 'dark',
                    'sort_order': 6
                }
            ]
            
            for cat_data in categories_data:
                category, created = UsageCategory.objects.get_or_create(
                    category_code=cat_data['category_code'],
                    defaults=cat_data
                )
                if created:
                    logger.info(f"Created category: {category.category_name}")
            
            # Sample metrics for each category
            metrics_data = [
                # Patient Management
                {'category_code': 'patient_management', 'metric_code': 'patient_created', 'metric_name': 'Patient Records Created', 'unit_cost': '2.50'},
                {'category_code': 'patient_management', 'metric_code': 'appointment_scheduled', 'metric_name': 'Appointments Scheduled', 'unit_cost': '1.00'},
                {'category_code': 'patient_management', 'metric_code': 'patient_updated', 'metric_name': 'Patient Records Updated', 'unit_cost': '0.50'},
                
                # AI Diagnostics
                {'category_code': 'ai_diagnostics', 'metric_code': 'ai_diagnosis', 'metric_name': 'AI Diagnosis Performed', 'unit_cost': '15.00'},
                {'category_code': 'ai_diagnostics', 'metric_code': 'ai_recommendation', 'metric_name': 'AI Recommendations', 'unit_cost': '5.00'},
                
                # Radiology
                {'category_code': 'radiology', 'metric_code': 'scan_analyzed', 'metric_name': 'Medical Scans Analyzed', 'unit_cost': '25.00'},
                {'category_code': 'radiology', 'metric_code': 'image_stored', 'metric_name': 'Medical Images Stored', 'unit_cost': '1.00'},
                
                # Laboratory
                {'category_code': 'laboratory', 'metric_code': 'lab_test', 'metric_name': 'Lab Tests Processed', 'unit_cost': '8.00'},
                {'category_code': 'laboratory', 'metric_code': 'pathology_analysis', 'metric_name': 'Pathology Analysis', 'unit_cost': '20.00'},
                
                # Telemedicine
                {'category_code': 'telemedicine', 'metric_code': 'video_consultation', 'metric_name': 'Video Consultations', 'unit_cost': '10.00'},
                {'category_code': 'telemedicine', 'metric_code': 'chat_session', 'metric_name': 'Chat Sessions', 'unit_cost': '2.00'},
                
                # Reports
                {'category_code': 'reports', 'metric_code': 'report_generated', 'metric_name': 'Reports Generated', 'unit_cost': '3.00'},
                {'category_code': 'reports', 'metric_code': 'data_exported', 'metric_name': 'Data Exports', 'unit_cost': '5.00'},
            ]
            
            for metric_data in metrics_data:
                category = UsageCategory.objects.get(category_code=metric_data['category_code'])
                metric, created = UsageMetric.objects.get_or_create(
                    category=category,
                    metric_code=metric_data['metric_code'],
                    defaults={
                        'metric_name': metric_data['metric_name'],
                        'unit_cost': Decimal(metric_data['unit_cost']),
                        'is_counted': True,
                        'is_billable': True,
                        'is_active': True
                    }
                )
                if created:
                    logger.info(f"Created metric: {metric.metric_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing default metrics: {str(e)}")
            return False
