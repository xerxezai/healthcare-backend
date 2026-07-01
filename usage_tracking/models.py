"""
Advanced Usage Tracking System for Healthcare Platform

This module provides comprehensive usage tracking and analytics for each user,
enabling monthly billing calculations, feature usage monitoring, and insights.

Features:
- Per-user usage tracking
- Monthly aggregation
- Real-time counters
- Feature-specific metrics
- Billing integration
- Usage analytics
- Soft coding for flexible configuration
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json

User = get_user_model()


class UsageCategory(models.Model):
    """
    Soft-coded usage categories for flexible tracking
    """
    category_code = models.CharField(max_length=50, unique=True)
    category_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_billable = models.BooleanField(default=True)
    unit_name = models.CharField(max_length=50, default='usage')  # e.g., 'patients', 'scans', 'diagnoses'
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=20, default='primary')
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'usage_categories'
        ordering = ['sort_order', 'category_name']

    def __str__(self):
        return f"{self.category_name} ({self.category_code})"


class UsageMetric(models.Model):
    """
    Specific metrics within each category for granular tracking
    """
    category = models.ForeignKey(UsageCategory, on_delete=models.CASCADE, related_name='metrics')
    metric_code = models.CharField(max_length=50)
    metric_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    unit_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_counted = models.BooleanField(default=True)  # Whether to count this metric
    is_billable = models.BooleanField(default=True)  # Whether to bill for this metric
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=20, default='secondary')
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'usage_metrics'
        unique_together = ['category', 'metric_code']
        ordering = ['sort_order', 'metric_name']

    def __str__(self):
        return f"{self.category.category_name} - {self.metric_name}"


class UserUsageProfile(models.Model):
    """
    User-specific usage profile and preferences
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='usage_profile')
    subscription_plan = models.CharField(max_length=50, blank=True)
    monthly_limit = models.JSONField(default=dict, help_text="Monthly limits per metric")
    notification_preferences = models.JSONField(default=dict)
    usage_tracking_enabled = models.BooleanField(default=True)
    billing_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_usage_profiles'

    def __str__(self):
        return f"Usage Profile - {self.user.username}"


class MonthlyUsageSummary(models.Model):
    """
    Monthly aggregated usage summary for each user
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='monthly_usage')
    year = models.IntegerField()
    month = models.IntegerField()
    total_usage_count = models.IntegerField(default=0)
    total_billable_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    usage_data = models.JSONField(default=dict)  # Detailed usage breakdown
    is_finalized = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'monthly_usage_summaries'
        unique_together = ['user', 'year', 'month']
        indexes = [
            models.Index(fields=['user', 'year', 'month']),
            models.Index(fields=['year', 'month']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.year}-{self.month:02d}"

    @property
    def month_name(self):
        return datetime(self.year, self.month, 1).strftime('%B')

    def get_category_usage(self, category_code):
        """Get usage for specific category"""
        return self.usage_data.get(category_code, {})


class DailyUsageRecord(models.Model):
    """
    Daily usage records for detailed tracking
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_usage')
    metric = models.ForeignKey(UsageMetric, on_delete=models.CASCADE)
    date = models.DateField()
    usage_count = models.IntegerField(default=0)
    billable_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    metadata = models.JSONField(default=dict, help_text="Additional context data")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'daily_usage_records'
        unique_together = ['user', 'metric', 'date']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['metric', 'date']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.metric.metric_name} - {self.date}"


class UsageEvent(models.Model):
    """
    Individual usage events for real-time tracking
    """
    EVENT_TYPES = [
        ('access', 'Feature Access'),
        ('action', 'Action Performed'),
        ('creation', 'Resource Created'),
        ('modification', 'Resource Modified'),
        ('deletion', 'Resource Deleted'),
        ('view', 'Resource Viewed'),
        ('export', 'Data Exported'),
        ('import', 'Data Imported'),
        ('api_call', 'API Call Made'),
        ('report_generated', 'Report Generated'),
    ]

    event_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usage_events')
    metric = models.ForeignKey(UsageMetric, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='action')
    timestamp = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    reference_id = models.CharField(max_length=100, blank=True)  # ID of related object
    reference_type = models.CharField(max_length=50, blank=True)  # Type of related object
    event_data = models.JSONField(default=dict)
    is_billable = models.BooleanField(default=True)
    is_processed = models.BooleanField(default=False)

    class Meta:
        db_table = 'usage_events'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['metric', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['is_processed']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.metric.metric_name} - {self.timestamp}"


class UsageAlert(models.Model):
    """
    Usage-based alerts and notifications
    """
    ALERT_TYPES = [
        ('limit_warning', 'Approaching Limit'),
        ('limit_exceeded', 'Limit Exceeded'),
        ('unusual_activity', 'Unusual Activity'),
        ('high_usage', 'High Usage Detected'),
        ('billing_threshold', 'Billing Threshold Reached'),
    ]

    ALERT_LEVELS = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usage_alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    alert_level = models.CharField(max_length=10, choices=ALERT_LEVELS, default='info')
    title = models.CharField(max_length=200)
    message = models.TextField()
    threshold_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    current_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    metric = models.ForeignKey(UsageMetric, on_delete=models.CASCADE, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'usage_alerts'
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['alert_level', 'is_read']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.alert_type} - {self.title}"


class UsageConfiguration(models.Model):
    """
    System-wide usage tracking configuration
    """
    config_key = models.CharField(max_length=100, unique=True)
    config_value = models.JSONField(default=dict)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'usage_configurations'

    def __str__(self):
        return f"Config: {self.config_key}"

    @classmethod
    def get_config(cls, key, default=None):
        """Get configuration value"""
        try:
            config = cls.objects.get(config_key=key, is_active=True)
            return config.config_value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_config(cls, key, value, description=""):
        """Set configuration value"""
        config, created = cls.objects.update_or_create(
            config_key=key,
            defaults={
                'config_value': value,
                'description': description,
                'is_active': True
            }
        )
        return config
