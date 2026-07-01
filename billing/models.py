"""
Manual Billing & Subscription Management System

This module handles both pay-per-use billing and monthly subscription billing
for healthcare professionals with flexible pricing models.

Key Features:
- Monthly subscription plans ($100 base + $100 per feature)
- Pay-per-use billing option
- Custom payment terms
- HIPAA compliant billing
- Flexible pricing models
- Volume discount calculations
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from datetime import datetime, timedelta


class ManualBillingAccount(models.Model):
    """
    Represents a manual billing account for healthcare providers
    """
    PRACTICE_TYPES = [
        ('individual', 'Individual Practice'),
        ('small_clinic', 'Small Clinic (2-5 doctors)'),
        ('medium_practice', 'Medium Practice (6-20 doctors)'),
        ('large_practice', 'Large Practice (20+ doctors)'),
        ('hospital', 'Hospital/Health System'),
        ('diagnostic', 'Diagnostic Center'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Setup'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('closed', 'Closed'),
    ]
    
    account_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    doctor_name = models.CharField(max_length=200)
    practice_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    practice_type = models.CharField(max_length=20, choices=PRACTICE_TYPES)
    
    # Account Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    
    # Billing Details
    billing_email = models.EmailField(blank=True)
    payment_terms = models.IntegerField(default=30, help_text="Payment terms in days")
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Usage Tracking
    total_usage_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    outstanding_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.doctor_name} - {self.practice_name or 'Individual Practice'}"
    
    class Meta:
        db_table = 'manual_billing_accounts'


class ServicePricing(models.Model):
    """
    Defines pricing for different medical services
    """
    SERVICE_TYPES = [
        ('patient_management', 'Patient Management'),
        ('appointment_scheduling', 'Appointment Scheduling'),
        ('ai_diagnosis', 'AI-Powered Diagnosis'),
        ('radiology', 'Radiology & Imaging'),
        ('pathology', 'Pathology & Lab Tests'),
        ('telemedicine', 'Telemedicine Consultation'),
        ('ehr_access', 'Electronic Health Records'),
        ('prescription_management', 'Prescription Management'),
        ('analytics', 'Analytics & Reporting'),
        ('ai_chatbot', 'AI Medical Chatbot'),
    ]
    
    PRICING_MODELS = [
        ('per_patient_month', 'Per Patient Per Month'),
        ('per_appointment', 'Per Appointment'),
        ('per_analysis', 'Per Analysis'),
        ('per_study', 'Per Study'),
        ('per_test', 'Per Test'),
        ('per_consultation', 'Per Consultation'),
        ('per_access', 'Per Access'),
        ('per_prescription', 'Per Prescription'),
        ('per_report', 'Per Report'),
        ('per_query', 'Per Query'),
    ]
    
    service_type = models.CharField(max_length=30, choices=SERVICE_TYPES, unique=True)
    service_name = models.CharField(max_length=100)
    pricing_model = models.CharField(max_length=20, choices=PRICING_MODELS)
    base_price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    unit_description = models.CharField(max_length=50, help_text="e.g., 'per patient/month'")
    
    # Volume Discounts
    volume_threshold_1 = models.IntegerField(default=100, help_text="Units for first discount tier")
    volume_discount_1 = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Discount percentage")
    volume_threshold_2 = models.IntegerField(default=500, help_text="Units for second discount tier") 
    volume_discount_2 = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Discount percentage")
    volume_threshold_3 = models.IntegerField(default=1000, help_text="Units for third discount tier")
    volume_discount_3 = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Discount percentage")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_price(self, quantity):
        """Calculate price with volume discounts"""
        base_total = self.base_price * quantity
        
        if quantity >= self.volume_threshold_3 and self.volume_discount_3 > 0:
            discount = self.volume_discount_3
        elif quantity >= self.volume_threshold_2 and self.volume_discount_2 > 0:
            discount = self.volume_discount_2
        elif quantity >= self.volume_threshold_1 and self.volume_discount_1 > 0:
            discount = self.volume_discount_1
        else:
            discount = 0
        
        discounted_amount = base_total * (discount / 100)
        return base_total - discounted_amount
    
    def __str__(self):
        return f"{self.service_name} - ${self.base_price} {self.unit_description}"
    
    class Meta:
        db_table = 'service_pricing'


class UsageRecord(models.Model):
    """
    Records usage of services for billing
    """
    account = models.ForeignKey(ManualBillingAccount, on_delete=models.CASCADE, related_name='usage_records')
    service = models.ForeignKey(ServicePricing, on_delete=models.CASCADE)
    
    usage_date = models.DateTimeField(auto_now_add=True)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Additional metadata
    description = models.TextField(blank=True, help_text="Additional details about the usage")
    reference_id = models.CharField(max_length=100, blank=True, help_text="External reference (patient ID, appointment ID, etc.)")
    
    # Billing status
    billed = models.BooleanField(default=False)
    invoice = models.ForeignKey('Invoice', on_delete=models.SET_NULL, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.total_amount:
            self.total_amount = self.service.calculate_price(self.quantity)
            self.unit_price = self.total_amount / self.quantity
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.account.doctor_name} - {self.service.service_name} x{self.quantity}"
    
    class Meta:
        db_table = 'usage_records'


class Invoice(models.Model):
    """
    Represents invoices for manual billing
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    invoice_number = models.CharField(max_length=20, unique=True)
    account = models.ForeignKey(ManualBillingAccount, on_delete=models.CASCADE, related_name='invoices')
    
    # Invoice details
    invoice_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    sent_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Payment details
    payment_method = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    
    notes = models.TextField(blank=True)
    
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        current_date = datetime.now()
        prefix = f"MB{current_date.strftime('%Y%m')}"
        
        # Find the latest invoice for this month
        latest = Invoice.objects.filter(
            invoice_number__startswith=prefix
        ).order_by('-invoice_number').first()
        
        if latest:
            last_number = int(latest.invoice_number[8:])  # Extract last 4 digits
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:04d}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        
        if not self.due_date:
            self.due_date = self.invoice_date + timedelta(days=self.account.payment_terms)
        
        super().save(*args, **kwargs)
    
    def mark_as_paid(self, payment_method='', payment_reference=''):
        """Mark invoice as paid"""
        self.status = 'paid'
        self.paid_at = datetime.now()
        self.payment_method = payment_method
        self.payment_reference = payment_reference
        self.save()
        
        # Update account balance
        self.account.outstanding_balance -= self.total_amount
        self.account.total_paid_amount += self.total_amount
        self.account.save()
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.account.doctor_name}"
    
    class Meta:
        db_table = 'invoices'


class BillingRequest(models.Model):
    """
    Handles initial requests for manual billing setup
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('in_review', 'Under Review'),
        ('approved', 'Approved'),
        ('setup_complete', 'Setup Complete'),
        ('rejected', 'Rejected'),
    ]
    
    # Contact Information
    doctor_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    practice_name = models.CharField(max_length=200, blank=True)
    practice_type = models.CharField(max_length=20, choices=ManualBillingAccount.PRACTICE_TYPES)
    
    # Requirements
    expected_usage = models.TextField(help_text="Expected usage details")
    special_requirements = models.TextField(blank=True)
    
    # Processing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer_notes = models.TextField(blank=True)
    
    # Related account (when approved)
    billing_account = models.OneToOneField(
        ManualBillingAccount, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='initial_request'
    )
    
    def approve_and_create_account(self):
        """Approve request and create billing account"""
        if self.status != 'approved':
            self.status = 'approved'
            self.reviewed_at = datetime.now()
            self.save()
            
            # Create billing account
            account = ManualBillingAccount.objects.create(
                doctor_name=self.doctor_name,
                practice_name=self.practice_name,
                email=self.email,
                phone=self.phone,
                practice_type=self.practice_type,
                billing_email=self.email,
                status='active',
                activated_at=datetime.now()
            )
            
            self.billing_account = account
            self.status = 'setup_complete'
            self.save()
            
            return account
    
    def __str__(self):
        return f"Billing Request - {self.doctor_name} ({self.status})"
    
    class Meta:
        db_table = 'billing_requests'


class SubscriptionPlan(models.Model):
    """
    Monthly subscription plans with base platform + additional features
    """
    PLAN_TYPES = [
        ('base', 'Base Healthcare Platform'),
        ('starter', 'Starter Practice'),
        ('professional', 'Professional Practice'), 
        ('enterprise', 'Enterprise Practice'),
        ('custom', 'Custom Plan'),
    ]
    
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    plan_name = models.CharField(max_length=100)
    description = models.TextField()
    base_monthly_price = models.DecimalField(max_digits=8, decimal_places=2, default=100)
    included_features = models.JSONField(default=list, help_text="List of included feature codes")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.plan_name} - ${self.base_monthly_price}/month"
    
    class Meta:
        db_table = 'subscription_plans'


class SubscriptionFeature(models.Model):
    """
    Additional features that can be added to subscriptions
    """
    FEATURE_TYPES = [
        ('ai_diagnosis', 'AI Diagnosis Module'),
        ('radiology', 'Radiology Services'),
        ('lab_management', 'Laboratory Management'),
        ('telemedicine', 'Telemedicine Suite'),
        ('appointment_advanced', 'Advanced Scheduling'),
        ('analytics', 'Advanced Analytics'),
        ('pathology', 'Pathology Management'),
        ('billing_advanced', 'Advanced Billing'),
        ('reporting', 'Custom Reporting'),
        ('integration', 'Third-party Integrations'),
    ]
    
    feature_code = models.CharField(max_length=30, choices=FEATURE_TYPES, unique=True)
    feature_name = models.CharField(max_length=100)
    description = models.TextField()
    monthly_price = models.DecimalField(max_digits=8, decimal_places=2, default=100)
    icon = models.CharField(max_length=10, default='⚡')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.feature_name} - ${self.monthly_price}/month"
    
    class Meta:
        db_table = 'subscription_features'


class MonthlySubscription(models.Model):
    """
    Customer's monthly subscription with base plan + additional features
    """
    SUBSCRIPTION_STATUS = [
        ('pending', 'Pending Activation'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    subscription_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    billing_account = models.ForeignKey(ManualBillingAccount, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    additional_features = models.ManyToManyField(SubscriptionFeature, blank=True)
    
    # Subscription Details
    status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS, default='pending')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    next_billing_date = models.DateTimeField()
    
    # Pricing
    monthly_base_amount = models.DecimalField(max_digits=8, decimal_places=2)
    monthly_features_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    monthly_total_amount = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Billing History
    total_billed_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_monthly_total(self):
        """Calculate total monthly amount including additional features"""
        features_total = sum(feature.monthly_price for feature in self.additional_features.all())
        self.monthly_features_amount = features_total
        self.monthly_total_amount = self.monthly_base_amount + features_total
        return self.monthly_total_amount
    
    def add_feature(self, feature_code):
        """Add a feature to the subscription"""
        try:
            feature = SubscriptionFeature.objects.get(feature_code=feature_code, is_active=True)
            self.additional_features.add(feature)
            self.calculate_monthly_total()
            self.save()
            return True
        except SubscriptionFeature.DoesNotExist:
            return False
    
    def remove_feature(self, feature_code):
        """Remove a feature from the subscription"""
        try:
            feature = SubscriptionFeature.objects.get(feature_code=feature_code)
            self.additional_features.remove(feature)
            self.calculate_monthly_total()
            self.save()
            return True
        except SubscriptionFeature.DoesNotExist:
            return False
    
    def activate(self):
        """Activate the subscription"""
        if self.status == 'pending':
            self.status = 'active'
            self.start_date = datetime.now()
            self.next_billing_date = self.start_date + timedelta(days=30)
            self.save()
    
    def cancel(self, end_date=None):
        """Cancel the subscription"""
        self.status = 'cancelled'
        if end_date:
            self.end_date = end_date
        else:
            self.end_date = datetime.now()
        self.save()
    
    def __str__(self):
        return f"{self.billing_account.doctor_name} - {self.plan.plan_name} (${self.monthly_total_amount}/month)"
    
    class Meta:
        db_table = 'monthly_subscriptions'


class SubscriptionInvoice(models.Model):
    """
    Monthly invoices for subscriptions
    """
    INVOICE_STATUS = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    invoice_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    subscription = models.ForeignKey(MonthlySubscription, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=20, unique=True)
    
    # Invoice Details
    billing_period_start = models.DateTimeField()
    billing_period_end = models.DateTimeField()
    issue_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    
    # Amounts
    base_amount = models.DecimalField(max_digits=8, decimal_places=2)
    features_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=8, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Status
    status = models.CharField(max_length=20, choices=INVOICE_STATUS, default='draft')
    paid_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - ${self.total_amount}"
    
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        import datetime
        today = datetime.date.today()
        prefix = f"INV-{today.strftime('%Y%m')}"
        
        # Get last invoice number for this month
        last_invoice = SubscriptionInvoice.objects.filter(
            invoice_number__startswith=prefix
        ).order_by('-invoice_number').first()
        
        if last_invoice:
            last_num = int(last_invoice.invoice_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        self.invoice_number = f"{prefix}-{new_num:04d}"
        
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.generate_invoice_number()
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'subscription_invoices'
