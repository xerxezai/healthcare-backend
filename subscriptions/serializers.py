# backend/subscriptions/serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import Service, SubscriptionPlan, UserSubscription, ServiceUsage, BillingHistory, PaymentMethod
# from hospital.serializers import RegisterSerializer # Or a simpler user serializer if needed

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'price_monthly', 'app_suite', 'usage_unit_name', 'is_metered']

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True, read_only=True)
    currency = serializers.CharField(source='get_currency_display', read_only=True) # To display full name like "US Dollar"
    currency_code = serializers.CharField(source='currency', read_only=True) # To display code like "USD"


    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'description', 'price_monthly', 'currency', 'currency_code', 'services', 'is_active',
            'limit_chatbot_messages', 'limit_mcq_generations', 
            'limit_report_analyses', 'limit_document_anonymizations',
            # 'limit_storage_gb',
        ]

class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    is_currently_active = serializers.BooleanField(read_only=True) # Add this method field

    class Meta:
        model = UserSubscription
        fields = [
            'id', 'user', 'plan', 'start_date', 'end_date', 'status', 
            'payment_gateway_subscription_id', 'auto_renew', 'is_currently_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'payment_gateway_subscription_id', 'created_at', 'updated_at', 'is_currently_active']

class ServiceUsageSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    user_email = serializers.EmailField(source='user_subscription.user.email', read_only=True)
    plan_name = serializers.CharField(source='user_subscription.plan.name', read_only=True)

    class Meta:
        model = ServiceUsage
        fields = ['id', 'user_email', 'plan_name', 'service', 'usage_count', 'period_start_date', 'period_end_date', 'last_recorded_usage_at']

class BillingHistorySerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True, allow_null=True)
    class Meta:
        model = BillingHistory
        fields = [
            'id', 'user_email', 'payment_gateway_invoice_id', 'payment_gateway_charge_id',
            'date_created', 'date_paid', 'plan_name_snapshot', 'amount_due', 'amount_paid',
            'currency', 'status', 'description', 'invoice_pdf_url'
        ]

class PaymentMethodSerializer(serializers.ModelSerializer):
    card_brand_display = serializers.CharField(source='get_card_brand_display', read_only=True)

    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'payment_gateway_method_id', 'card_brand', 'card_brand_display', 
            'last4', 'exp_month', 'exp_year', 'is_default'
        ]
        # `payment_gateway_method_id` is crucial. For creation, it usually comes from frontend (e.g. Stripe.js token)
        # For this example, we'll make it writable for easier testing without full gateway.
        # In production, you'd likely have a separate serializer for creation that takes a token.
        read_only_fields = ['card_brand_display'] 


class CreatePaymentMethodSerializer(serializers.Serializer):
    # This serializer would typically take a token from Stripe.js or similar
    payment_token = serializers.CharField(write_only=True, required=True, help_text="Token from payment gateway (e.g., Stripe Elements)")
    set_as_default = serializers.BooleanField(default=False, required=False)

    # You would add validation and logic to create the PaymentMethod in the view using this token.


class UsageStatsSerializer(serializers.Serializer):
    # These field names should match the keys in the dictionary passed to the serializer in the view
    chatbot_messages_current_period = serializers.IntegerField(default=0)
    chatbot_sessions_current_period = serializers.IntegerField(default=0) # You'll need to define how to calculate this
    mcqs_generated_current_period = serializers.IntegerField(default=0)
    pdfs_for_mcq_current_period = serializers.IntegerField(default=0) # You'll need to define how to calculate this
    reports_analyzed_current_period = serializers.IntegerField(default=0)
    documents_anonymized_current_period = serializers.IntegerField(default=0)
    # storageUsedGB = serializers.FloatField(default=0)
    # storageLimitGB = serializers.FloatField(allow_null=True)

    # Plan limits for context
    limit_chatbot_messages = serializers.IntegerField(allow_null=True)
    limit_mcq_generations = serializers.IntegerField(allow_null=True)
    limit_report_analyses = serializers.IntegerField(allow_null=True)
    limit_document_anonymizations = serializers.IntegerField(allow_null=True)

    current_cycle_start_date = serializers.DateField()
    current_cycle_end_date = serializers.DateField()