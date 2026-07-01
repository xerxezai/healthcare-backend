"""
Manual Billing Admin Configuration

Django admin interface for managing manual billing accounts,
usage records, invoices, and billing requests.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum
from .models import (
    ManualBillingAccount,
    ServicePricing,
    UsageRecord,
    Invoice,
    BillingRequest,
    SubscriptionPlan,
    SubscriptionFeature,
    MonthlySubscription,
    SubscriptionInvoice
)


@admin.register(BillingRequest)
class BillingRequestAdmin(admin.ModelAdmin):
    """
    Admin interface for billing requests
    """
    list_display = [
        'doctor_name', 'email', 'practice_type', 'status', 
        'submitted_at', 'action_buttons'
    ]
    list_filter = ['status', 'practice_type', 'submitted_at']
    search_fields = ['doctor_name', 'email', 'practice_name']
    readonly_fields = ['submitted_at', 'reviewed_at']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('doctor_name', 'email', 'phone', 'practice_name', 'practice_type')
        }),
        ('Requirements', {
            'fields': ('expected_usage', 'special_requirements')
        }),
        ('Processing', {
            'fields': ('status', 'submitted_at', 'reviewed_at', 'reviewer_notes', 'billing_account')
        }),
    )
    
    def action_buttons(self, obj):
        """
        Display action buttons for each request
        """
        if obj.status == 'pending':
            approve_url = reverse('admin:billing_billingrequest_change', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}">Review</a>',
                approve_url
            )
        elif obj.status == 'approved' and not obj.billing_account:
            return format_html('<span style="color: orange;">Setup Pending</span>')
        elif obj.billing_account:
            account_url = reverse('admin:billing_manualbillingaccount_change', args=[obj.billing_account.pk])
            return format_html(
                '<a class="button" href="{}">View Account</a>',
                account_url
            )
        return '-'
    
    action_buttons.short_description = 'Actions'
    
    def save_model(self, request, obj, form, change):
        """
        Handle status changes and account creation
        """
        if change and obj.status == 'approved' and not obj.billing_account:
            # Create billing account when approved
            obj.approve_and_create_account()
        super().save_model(request, obj, form, change)


@admin.register(ManualBillingAccount)
class ManualBillingAccountAdmin(admin.ModelAdmin):
    """
    Admin interface for manual billing accounts
    """
    list_display = [
        'doctor_name', 'practice_name', 'email', 'status',
        'total_usage_amount', 'outstanding_balance', 'created_at'
    ]
    list_filter = ['status', 'practice_type', 'created_at']
    search_fields = ['doctor_name', 'practice_name', 'email']
    readonly_fields = [
        'account_id', 'created_at', 'activated_at',
        'total_usage_amount', 'total_paid_amount', 'outstanding_balance'
    ]
    
    fieldsets = (
        ('Account Information', {
            'fields': ('account_id', 'doctor_name', 'practice_name', 'email', 'phone', 'practice_type')
        }),
        ('Account Status', {
            'fields': ('status', 'created_at', 'activated_at')
        }),
        ('Billing Details', {
            'fields': ('billing_email', 'payment_terms', 'credit_limit')
        }),
        ('Usage Summary', {
            'fields': ('total_usage_amount', 'total_paid_amount', 'outstanding_balance'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """
        Add usage statistics to queryset
        """
        return super().get_queryset(request).select_related().prefetch_related('usage_records', 'invoices')


@admin.register(ServicePricing)
class ServicePricingAdmin(admin.ModelAdmin):
    """
    Admin interface for service pricing
    """
    list_display = [
        'service_name', 'service_type', 'base_price', 'unit_description',
        'is_active', 'updated_at'
    ]
    list_filter = ['service_type', 'is_active', 'updated_at']
    search_fields = ['service_name', 'service_type']
    
    fieldsets = (
        ('Service Information', {
            'fields': ('service_type', 'service_name', 'pricing_model', 'base_price', 'unit_description')
        }),
        ('Volume Discounts', {
            'fields': (
                ('volume_threshold_1', 'volume_discount_1'),
                ('volume_threshold_2', 'volume_discount_2'),
                ('volume_threshold_3', 'volume_discount_3')
            ),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


class UsageRecordInline(admin.TabularInline):
    """
    Inline for usage records in account admin
    """
    model = UsageRecord
    extra = 0
    readonly_fields = ['usage_date', 'total_amount', 'billed']
    fields = ['service', 'quantity', 'unit_price', 'total_amount', 'usage_date', 'billed']


@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    """
    Admin interface for usage records
    """
    list_display = [
        'account', 'service', 'quantity', 'total_amount',
        'usage_date', 'billed', 'invoice'
    ]
    list_filter = ['billed', 'usage_date', 'service__service_type']
    search_fields = ['account__doctor_name', 'account__email', 'service__service_name', 'reference_id']
    readonly_fields = ['usage_date', 'unit_price', 'total_amount']
    
    def get_queryset(self, request):
        """
        Optimize queryset with select_related
        """
        return super().get_queryset(request).select_related('account', 'service', 'invoice')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """
    Admin interface for invoices
    """
    list_display = [
        'invoice_number', 'account', 'total_amount', 'status',
        'invoice_date', 'due_date', 'paid_at'
    ]
    list_filter = ['status', 'invoice_date', 'due_date']
    search_fields = ['invoice_number', 'account__doctor_name', 'account__email']
    readonly_fields = ['invoice_number', 'invoice_date', 'paid_at']
    
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'account', 'invoice_date', 'due_date')
        }),
        ('Billing Period', {
            'fields': ('period_start', 'period_end')
        }),
        ('Amounts', {
            'fields': ('subtotal', 'tax_amount', 'total_amount')
        }),
        ('Status & Payment', {
            'fields': ('status', 'sent_at', 'paid_at', 'payment_method', 'payment_reference')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_sent', 'mark_as_paid']
    
    def mark_as_sent(self, request, queryset):
        """
        Mark selected invoices as sent
        """
        from django.utils import timezone
        updated = queryset.filter(status='draft').update(
            status='sent',
            sent_at=timezone.now()
        )
        self.message_user(request, f'{updated} invoices marked as sent.')
    
    mark_as_sent.short_description = "Mark selected invoices as sent"
    
    def mark_as_paid(self, request, queryset):
        """
        Mark selected invoices as paid
        """
        count = 0
        for invoice in queryset.filter(status__in=['sent', 'overdue']):
            invoice.mark_as_paid()
            count += 1
        self.message_user(request, f'{count} invoices marked as paid.')
    
    mark_as_paid.short_description = "Mark selected invoices as paid"
    
    def get_queryset(self, request):
        """
        Optimize queryset with select_related
        """
        return super().get_queryset(request).select_related('account')


# Add usage records inline to billing account admin
ManualBillingAccountAdmin.inlines = [UsageRecordInline]


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    """
    Admin interface for subscription plans
    """
    list_display = ['plan_name', 'plan_type', 'base_monthly_price', 'is_active', 'created_at']
    list_filter = ['plan_type', 'is_active', 'created_at']
    search_fields = ['plan_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Plan Details', {
            'fields': ('plan_type', 'plan_name', 'description')
        }),
        ('Pricing', {
            'fields': ('base_monthly_price', 'included_features')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )


@admin.register(SubscriptionFeature)
class SubscriptionFeatureAdmin(admin.ModelAdmin):
    """
    Admin interface for subscription features
    """
    list_display = ['feature_name', 'feature_code', 'monthly_price', 'icon', 'is_active']
    list_filter = ['feature_code', 'is_active', 'created_at']
    search_fields = ['feature_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Feature Details', {
            'fields': ('feature_code', 'feature_name', 'description', 'icon')
        }),
        ('Pricing', {
            'fields': ('monthly_price',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )


class SubscriptionFeatureInline(admin.TabularInline):
    """
    Inline admin for subscription features
    """
    model = MonthlySubscription.additional_features.through
    extra = 0
    verbose_name = "Additional Feature"
    verbose_name_plural = "Additional Features"


@admin.register(MonthlySubscription)
class MonthlySubscriptionAdmin(admin.ModelAdmin):
    """
    Admin interface for monthly subscriptions
    """
    list_display = [
        'subscription_id', 'billing_account', 'plan', 'status', 
        'monthly_total_amount', 'start_date', 'next_billing_date'
    ]
    list_filter = ['status', 'plan', 'start_date']
    search_fields = ['billing_account__doctor_name', 'billing_account__email']
    readonly_fields = [
        'subscription_id', 'created_at', 'updated_at', 
        'monthly_features_amount', 'monthly_total_amount'
    ]
    filter_horizontal = ['additional_features']
    
    fieldsets = (
        ('Subscription Details', {
            'fields': ('subscription_id', 'billing_account', 'plan', 'status')
        }),
        ('Billing Period', {
            'fields': ('start_date', 'end_date', 'next_billing_date')
        }),
        ('Features', {
            'fields': ('additional_features',)
        }),
        ('Pricing', {
            'fields': ('monthly_base_amount', 'monthly_features_amount', 'monthly_total_amount')
        }),
        ('Statistics', {
            'fields': ('total_billed_amount', 'total_paid_amount', 'created_at', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        Calculate totals when saving
        """
        super().save_model(request, obj, form, change)
        obj.calculate_monthly_total()
        obj.save()


@admin.register(SubscriptionInvoice)
class SubscriptionInvoiceAdmin(admin.ModelAdmin):
    """
    Admin interface for subscription invoices
    """
    list_display = [
        'invoice_number', 'subscription', 'billing_period', 'total_amount', 
        'status', 'issue_date', 'due_date'
    ]
    list_filter = ['status', 'issue_date', 'due_date']
    search_fields = [
        'invoice_number', 'subscription__billing_account__doctor_name',
        'subscription__billing_account__email'
    ]
    readonly_fields = [
        'invoice_id', 'invoice_number', 'issue_date', 'paid_date'
    ]
    
    fieldsets = (
        ('Invoice Details', {
            'fields': ('invoice_id', 'invoice_number', 'subscription')
        }),
        ('Billing Period', {
            'fields': ('billing_period_start', 'billing_period_end', 'issue_date', 'due_date')
        }),
        ('Amounts', {
            'fields': ('base_amount', 'features_amount', 'total_amount', 'paid_amount')
        }),
        ('Status', {
            'fields': ('status', 'paid_date')
        }),
    )
    
    def billing_period(self, obj):
        """
        Display billing period
        """
        return f"{obj.billing_period_start.strftime('%b %d')} - {obj.billing_period_end.strftime('%b %d, %Y')}"
    
    billing_period.short_description = "Billing Period"
    
    actions = ['mark_as_sent', 'mark_as_paid']
    
    def mark_as_sent(self, request, queryset):
        """
        Mark selected invoices as sent
        """
        updated = queryset.filter(status='draft').update(status='sent')
        self.message_user(request, f'{updated} invoices marked as sent.')
    
    mark_as_sent.short_description = "Mark selected invoices as sent"
    
    def mark_as_paid(self, request, queryset):
        """
        Mark selected invoices as paid
        """
        from django.utils import timezone
        count = 0
        for invoice in queryset.filter(status__in=['sent', 'overdue']):
            invoice.status = 'paid'
            invoice.paid_date = timezone.now()
            invoice.paid_amount = invoice.total_amount
            invoice.save()
            count += 1
        self.message_user(request, f'{count} invoices marked as paid.')
    
    mark_as_paid.short_description = "Mark selected invoices as paid"
