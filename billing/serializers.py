"""
Manual Billing Serializers

Serializers for the manual billing system API endpoints
"""

from rest_framework import serializers
from .models import (
    ManualBillingAccount,
    ServicePricing,
    UsageRecord,
    Invoice,
    BillingRequest
)


class BillingRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for billing setup requests
    """
    class Meta:
        model = BillingRequest
        fields = [
            'id', 'doctor_name', 'email', 'phone', 'practice_name',
            'practice_type', 'expected_usage', 'special_requirements',
            'status', 'submitted_at'
        ]
        read_only_fields = ['id', 'status', 'submitted_at']
    
    def validate_email(self, value):
        """
        Validate email format and check for duplicates
        """
        if BillingRequest.objects.filter(email=value, status__in=['pending', 'in_review', 'approved']).exists():
            raise serializers.ValidationError(
                "A billing request with this email is already pending or approved."
            )
        return value


class ServicePricingSerializer(serializers.ModelSerializer):
    """
    Serializer for service pricing information
    """
    class Meta:
        model = ServicePricing
        fields = [
            'id', 'service_type', 'service_name', 'pricing_model',
            'base_price', 'unit_description', 'volume_threshold_1',
            'volume_discount_1', 'volume_threshold_2', 'volume_discount_2',
            'volume_threshold_3', 'volume_discount_3'
        ]
        read_only_fields = ['id']


class ManualBillingAccountSerializer(serializers.ModelSerializer):
    """
    Serializer for manual billing accounts
    """
    practice_type_display = serializers.CharField(source='get_practice_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ManualBillingAccount
        fields = [
            'id', 'account_id', 'doctor_name', 'practice_name', 'email',
            'phone', 'practice_type', 'practice_type_display', 'status',
            'status_display', 'created_at', 'activated_at', 'billing_email',
            'payment_terms', 'credit_limit', 'total_usage_amount',
            'total_paid_amount', 'outstanding_balance'
        ]
        read_only_fields = [
            'id', 'account_id', 'created_at', 'activated_at',
            'total_usage_amount', 'total_paid_amount', 'outstanding_balance'
        ]


class UsageRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for usage records
    """
    service_name = serializers.CharField(source='service.service_name', read_only=True)
    service_type = serializers.CharField(source='service.service_type', read_only=True)
    unit_description = serializers.CharField(source='service.unit_description', read_only=True)
    
    class Meta:
        model = UsageRecord
        fields = [
            'id', 'account', 'service', 'service_name', 'service_type',
            'unit_description', 'usage_date', 'quantity', 'unit_price',
            'total_amount', 'description', 'reference_id', 'billed'
        ]
        read_only_fields = ['id', 'usage_date', 'unit_price', 'total_amount', 'billed']
    
    def validate(self, data):
        """
        Validate usage record data
        """
        account = data.get('account')
        if account and account.status != 'active':
            raise serializers.ValidationError(
                "Cannot record usage for inactive account"
            )
        
        quantity = data.get('quantity', 0)
        if quantity <= 0:
            raise serializers.ValidationError(
                "Quantity must be greater than zero"
            )
        
        return data


class InvoiceSerializer(serializers.ModelSerializer):
    """
    Serializer for invoices
    """
    account_name = serializers.CharField(source='account.doctor_name', read_only=True)
    account_email = serializers.CharField(source='account.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'account', 'account_name', 'account_email',
            'invoice_date', 'due_date', 'period_start', 'period_end',
            'subtotal', 'tax_amount', 'total_amount', 'status', 'status_display',
            'sent_at', 'paid_at', 'payment_method', 'payment_reference', 'notes'
        ]
        read_only_fields = [
            'id', 'invoice_number', 'invoice_date', 'sent_at', 'paid_at'
        ]


class UsageEstimateSerializer(serializers.Serializer):
    """
    Serializer for usage cost estimates
    """
    service_type = serializers.CharField()
    quantity = serializers.IntegerField(min_value=1)
    
    def validate_service_type(self, value):
        """
        Validate service type exists
        """
        if not ServicePricing.objects.filter(service_type=value, is_active=True).exists():
            raise serializers.ValidationError(f"Service type '{value}' not found or inactive")
        return value


class BillingContactSerializer(serializers.Serializer):
    """
    Serializer for billing contact form submissions
    """
    name = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    practice_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    practice_type = serializers.ChoiceField(choices=ManualBillingAccount.PRACTICE_TYPES)
    message = serializers.CharField(max_length=2000)
    expected_usage = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    
    def validate_email(self, value):
        """
        Validate email format
        """
        from django.core.validators import validate_email
        try:
            validate_email(value)
        except:
            raise serializers.ValidationError("Please enter a valid email address")
        return value


class AccountDashboardSerializer(serializers.Serializer):
    """
    Serializer for account dashboard data
    """
    account_summary = serializers.DictField()
    recent_usage = UsageRecordSerializer(many=True, read_only=True)
    recent_invoices = InvoiceSerializer(many=True, read_only=True)
    monthly_stats = serializers.DictField()
    
    
class BillingAdminStatsSerializer(serializers.Serializer):
    """
    Serializer for admin billing statistics
    """
    total_accounts = serializers.IntegerField()
    active_accounts = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    outstanding_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    monthly_usage = serializers.DictField()
    top_services = serializers.ListField()
    recent_activity = serializers.ListField()
