# backend/subscriptions/admin.py
from django.contrib import admin
from .models import Service, SubscriptionPlan, UserSubscription, ServiceUsage, BillingHistory, PaymentMethod

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'app_suite', 'price_monthly', 'usage_unit_name', 'is_metered')
    list_filter = ('app_suite', 'is_metered')
    search_fields = ('name', 'description')

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_monthly', 'currency', 'is_active')
    list_filter = ('is_active', 'currency')
    search_fields = ('name', 'description')
    filter_horizontal = ('services',)
    fieldsets = (
        (None, {'fields': ('name', 'description', 'price_monthly', 'currency', 'is_active', 'services')}),
        ('Usage Limits (SecureNeat)', {'fields': ('limit_chatbot_messages', 'limit_mcq_generations')}),
        ('Usage Limits (Radiology Suite)', {'fields': ('limit_report_analyses', 'limit_document_anonymizations')}),
        # ('Usage Limits (General)', {'fields': ('limit_storage_gb',)}),
    )

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user_email_display', 'plan_name_display', 'start_date', 'end_date', 'status', 'auto_renew', 'payment_gateway_subscription_id')
    list_filter = ('status', 'plan__name', 'start_date', 'end_date', 'auto_renew')
    search_fields = ('user__email', 'plan__name', 'payment_gateway_subscription_id')
    autocomplete_fields = ['user', 'plan']
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('user', 'plan') # Optimize queries

    def user_email_display(self, obj):
        return obj.user.email
    user_email_display.short_description = 'User Email'
    user_email_display.admin_order_field = 'user__email'

    def plan_name_display(self, obj):
        return obj.plan.name if obj.plan else "N/A"
    plan_name_display.short_description = 'Plan'
    plan_name_display.admin_order_field = 'plan__name'


@admin.register(ServiceUsage)
class ServiceUsageAdmin(admin.ModelAdmin):
    list_display = ('user_email_display', 'service_name_display', 'usage_count', 'period_start_date', 'period_end_date', 'last_recorded_usage_at')
    list_filter = ('service__name', 'period_start_date', 'period_end_date')
    search_fields = ('user_subscription__user__email', 'service__name')
    readonly_fields = ('last_recorded_usage_at',)
    list_select_related = ('user_subscription__user', 'service') # Optimize queries

    def user_email_display(self, obj):
        return obj.user_subscription.user.email
    user_email_display.short_description = 'User Email'

    def service_name_display(self, obj):
        return obj.service.name
    service_name_display.short_description = 'Service'


@admin.register(BillingHistory)
class BillingHistoryAdmin(admin.ModelAdmin):
    list_display = ('payment_gateway_invoice_id', 'user_email_display', 'date_created', 'plan_name_snapshot', 'amount_due', 'status')
    list_filter = ('status', 'date_created', 'currency')
    search_fields = ('user__email', 'payment_gateway_invoice_id', 'payment_gateway_charge_id', 'plan_name_snapshot')
    autocomplete_fields = ['user', 'user_subscription']
    readonly_fields = ('date_created', 'date_paid')
    list_select_related = ('user',)

    def user_email_display(self, obj):
        return obj.user.email if obj.user else "N/A"
    user_email_display.short_description = 'User Email'


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user_email_display', 'card_brand', 'last4', 'exp_month', 'exp_year', 'is_default', 'payment_gateway_method_id')
    list_filter = ('card_brand', 'is_default', 'exp_year')
    search_fields = ('user__email', 'last4', 'payment_gateway_method_id')
    autocomplete_fields = ['user']
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('user',)

    def user_email_display(self, obj):
        return obj.user.email
    user_email_display.short_description = 'User Email'