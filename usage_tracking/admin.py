"""
Usage Tracking Admin Interface

Django admin configuration for usage tracking models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.utils import timezone
import json

from .models import (
    UsageCategory, UsageMetric, UserUsageProfile, MonthlyUsageSummary,
    DailyUsageRecord, UsageEvent, UsageAlert, UsageConfiguration
)


@admin.register(UsageCategory)
class UsageCategoryAdmin(admin.ModelAdmin):
    list_display = ['category_name', 'category_code', 'color_badge', 'is_active', 'sort_order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['category_name', 'category_code', 'description']
    ordering = ['sort_order', 'category_name']
    
    def color_badge(self, obj):
        if obj.color:
            return format_html(
                '<span class="badge bg-{}">{}</span>',
                obj.color,
                obj.color
            )
        return '-'
    color_badge.short_description = 'Color'


@admin.register(UsageMetric)
class UsageMetricAdmin(admin.ModelAdmin):
    list_display = ['metric_name', 'metric_code', 'category', 'unit_cost', 'is_billable', 'is_active', 'created_at']
    list_filter = ['category', 'is_billable', 'is_active', 'created_at']
    search_fields = ['metric_name', 'metric_code', 'description']
    ordering = ['category__sort_order', 'sort_order', 'metric_name']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')


@admin.register(UserUsageProfile)
class UserUsageProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'usage_tracking_enabled', 'has_limits', 'created_at']
    list_filter = ['usage_tracking_enabled', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    def has_limits(self, obj):
        return bool(obj.monthly_limit)
    has_limits.boolean = True
    has_limits.short_description = 'Has Monthly Limits'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(MonthlyUsageSummary)
class MonthlyUsageSummaryAdmin(admin.ModelAdmin):
    list_display = ['user', 'month_year', 'total_usage_count', 'total_billable_amount', 'is_finalized', 'created_at']
    list_filter = ['year', 'month', 'is_finalized', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'usage_data_display']
    
    def month_year(self, obj):
        return f"{obj.month_name} {obj.year}"
    month_year.short_description = 'Month/Year'
    
    def usage_data_display(self, obj):
        if obj.usage_data:
            return format_html('<pre>{}</pre>', json.dumps(obj.usage_data, indent=2))
        return 'No data'
    usage_data_display.short_description = 'Usage Data (JSON)'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(DailyUsageRecord)
class DailyUsageRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'metric', 'date', 'usage_count', 'billable_amount', 'created_at']
    list_filter = ['date', 'metric__category', 'metric', 'created_at']
    search_fields = ['user__username', 'user__email', 'metric__metric_name']
    date_hierarchy = 'date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'metric', 'metric__category')


@admin.register(UsageEvent)
class UsageEventAdmin(admin.ModelAdmin):
    list_display = ['user', 'metric', 'event_type', 'is_billable', 'ip_address', 'timestamp']
    list_filter = ['event_type', 'is_billable', 'metric__category', 'timestamp']
    search_fields = ['user__username', 'user__email', 'metric__metric_name', 'session_id', 'ip_address']
    readonly_fields = ['timestamp', 'event_data_display']
    date_hierarchy = 'timestamp'
    
    def event_data_display(self, obj):
        if obj.event_data:
            return format_html('<pre>{}</pre>', json.dumps(obj.event_data, indent=2))
        return 'No data'
    event_data_display.short_description = 'Event Data (JSON)'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'metric', 'metric__category')


@admin.register(UsageAlert)
class UsageAlertAdmin(admin.ModelAdmin):
    list_display = ['user', 'alert_type', 'alert_level', 'title', 'is_read', 'is_dismissed', 'created_at']
    list_filter = ['alert_type', 'alert_level', 'is_read', 'is_dismissed', 'created_at']
    search_fields = ['user__username', 'user__email', 'title', 'message']
    readonly_fields = ['created_at']
    actions = ['mark_as_read', 'mark_as_dismissed']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = 'Mark selected alerts as read'
    
    def mark_as_dismissed(self, request, queryset):
        queryset.update(is_dismissed=True)
    mark_as_dismissed.short_description = 'Mark selected alerts as dismissed'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'metric', 'metric__category')


@admin.register(UsageConfiguration)
class UsageConfigurationAdmin(admin.ModelAdmin):
    list_display = ['config_key', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['config_key', 'description']
    readonly_fields = ['created_at', 'updated_at', 'config_value_display']
    
    def config_value_display(self, obj):
        if obj.config_value:
            return format_html('<pre>{}</pre>', json.dumps(obj.config_value, indent=2))
        return 'No value'
    config_value_display.short_description = 'Configuration Value (JSON)'


# Custom admin views for analytics
class UsageAnalyticsAdmin(admin.ModelAdmin):
    """Custom admin view for usage analytics"""
    
    def changelist_view(self, request, extra_context=None):
        # Add analytics data to the context
        extra_context = extra_context or {}
        
        # Get summary statistics
        today = timezone.now().date()
        this_month_start = today.replace(day=1)
        
        monthly_stats = MonthlyUsageSummary.objects.filter(
            year=today.year,
            month=today.month
        ).aggregate(
            total_users=Count('user', distinct=True),
            total_usage=Sum('total_usage_count'),
            total_billing=Sum('total_billable_amount')
        )
        
        daily_stats = DailyUsageRecord.objects.filter(
            date__gte=this_month_start
        ).aggregate(
            total_records=Count('id'),
            total_usage=Sum('usage_count'),
            total_billing=Sum('billable_amount')
        )
        
        top_categories = DailyUsageRecord.objects.filter(
            date__gte=this_month_start
        ).values(
            'metric__category__category_name'
        ).annotate(
            usage_count=Sum('usage_count')
        ).order_by('-usage_count')[:5]
        
        extra_context.update({
            'monthly_stats': monthly_stats,
            'daily_stats': daily_stats,
            'top_categories': top_categories,
            'current_month': today.strftime('%B %Y')
        })
        
        return super().changelist_view(request, extra_context=extra_context)
