# backend/subscriptions/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

class Service(models.Model):
    APP_SUITE_CHOICES = [
        ('SecureNeat', 'SecureNeat'),
        ('RadiologySuite', 'Radiology Suite'),
        ('General', 'General'), # For services not tied to a specific suite
    ]
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    price_monthly = models.DecimalField(max_digits=6, decimal_places=2, help_text="Individual service price if offered a la carte, or for plan value calculation.")
    app_suite = models.CharField(max_length=20, choices=APP_SUITE_CHOICES)
    # For usage tracking, define what unit of usage this service has
    usage_unit_name = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., API Calls, Documents, Chat Messages, PDFs Processed")
    is_metered = models.BooleanField(default=False, help_text="Is usage for this service tracked against plan limits?")


    def __str__(self):
        return f"{self.name} ({self.app_suite})"

class SubscriptionPlan(models.Model):
    CURRENCY_CHOICES = [
        ('USD', '$'),
        ('INR', '₹'),
    ]
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    price_monthly = models.DecimalField(max_digits=6, decimal_places=2)
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='USD',
        help_text="Currency for the plan's price (e.g., USD, INR, EUR)"
    )
    services = models.ManyToManyField(Service, related_name='plans_included_in') # Changed related_name for clarity
    is_active = models.BooleanField(default=True, help_text="Is this plan available for new subscriptions?")
    
    # Example usage limits per service within this plan. Null means unlimited for that service.
    # These should correspond to the 'name' field of the Service model for clarity.
    # Consider a more dynamic way if you have many services (e.g., a separate PlanServiceLimit model).
    limit_chatbot_messages = models.PositiveIntegerField(null=True, blank=True, help_text="Monthly limit for Dr. Max messages. Null for unlimited.")
    limit_mcq_generations = models.PositiveIntegerField(null=True, blank=True, help_text="Monthly limit for MCQ generations. Null for unlimited.")
    limit_report_analyses = models.PositiveIntegerField(null=True, blank=True, help_text="Monthly limit for radiology report analyses. Null for unlimited.")
    limit_document_anonymizations = models.PositiveIntegerField(null=True, blank=True, help_text="Monthly limit for document anonymizations. Null for unlimited.")
    # limit_storage_gb = models.FloatField(null=True, blank=True, help_text="Storage limit in GB. Null for unlimited.")


    def __str__(self):
        return f"{self.name} ({self.price_monthly} {self.currency.upper()})"

class UserSubscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('trial', 'Trial'),
        ('pending_payment', 'Pending Payment'),
        ('past_due', 'Past Due'), # Payment failed, grace period might apply
        ('cancelled', 'Cancelled'), # User initiated cancellation, access until end_date
        ('expired', 'Expired'),     # Past end_date and not renewed
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='user_subscriptions_to_plan') # PROTECT to prevent deleting a plan with active subs
    start_date = models.DateField()
    end_date = models.DateField(help_text="Date when the current billing cycle ends or access expires.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment')
    
    payment_gateway_subscription_id = models.CharField(max_length=255, blank=True, null=True, unique=True, help_text="Subscription ID from payment gateway (e.g., Stripe sub_xxx)")
    # payment_gateway_customer_id = models.CharField(max_length=255, blank=True, null=True, help_text="Customer ID from payment gateway (e.g., Stripe cus_xxx)")

    auto_renew = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_currently_active(self):
        return self.status in ['active', 'trial'] and self.end_date >= timezone.now().date()

    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.status}) until {self.end_date}"

    class Meta:
        ordering = ['-end_date', '-start_date']


class ServiceUsage(models.Model):
    user_subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name='service_usages')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='usages')
    usage_count = models.PositiveIntegerField(default=0)
    # Defines the period for which this usage_count is valid (typically a billing cycle)
    period_start_date = models.DateField()
    period_end_date = models.DateField()
    last_recorded_usage_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user_subscription', 'service', 'period_start_date') # One record per service per billing period start for a subscription
        ordering = ['-period_start_date', 'service__name']

    def __str__(self):
        return f"Usage for {self.service.name} by {self.user_subscription.user.email} ({self.usage_count}) for period {self.period_start_date} to {self.period_end_date}"

    @classmethod
    def record_usage(cls, user, service_name, count=1):
        try:
            service = Service.objects.get(name=service_name)
            if not service.is_metered:
                return None # Not a metered service, no need to track specific usage count against limit

            active_subscription = UserSubscription.objects.filter(
                user=user, status__in=['active', 'trial'], end_date__gte=timezone.now().date()
            ).order_by('-start_date').first() # Get the most recent active/trial

            if not active_subscription:
                raise ValidationError("No active or trial subscription found to record usage against.")

            # Determine current billing cycle for this subscription
            # This logic assumes the active_subscription's start_date and end_date define the *current* cycle.
            # For more complex scenarios (e.g., if a UserSubscription object spans multiple renewals),
            # you'd need to calculate the current cycle's start/end based on today's date and the subscription's anchor date.
            current_cycle_start = active_subscription.start_date 
            current_cycle_end = active_subscription.end_date
            
            # Ensure today is within the cycle we are recording for
            today = timezone.now().date()
            if not (current_cycle_start <= today <= current_cycle_end):
                 # This might happen if the subscription just renewed and the object isn't updated yet,
                 # or if trying to record usage for an expired part of a subscription.
                 # For simplicity, we'll assume the passed active_subscription is for the current period.
                 # A more robust system would find or create the ServiceUsage for the *actual* current billing period.
                 print(f"Warning: Recording usage for {service_name} outside of current subscription period {current_cycle_start}-{current_cycle_end} for user {user.email}")
                 # Potentially, find the *true* current cycle start/end here if UserSubscription is long-lived.
                 # For now, we proceed with the active_subscription's dates.


            usage, created = cls.objects.get_or_create(
                user_subscription=active_subscription,
                service=service,
                period_start_date=current_cycle_start,
                defaults={'period_end_date': current_cycle_end, 'usage_count': 0}
            )
            
            # Check against plan limits
            limit = None
            if service.name == "Dr. Max AI Chatbot": # Use exact names as in Service model
                limit = active_subscription.plan.limit_chatbot_messages
            elif service.name == "Intelligent MCQ Generator":
                limit = active_subscription.plan.limit_mcq_generations
            elif service.name == "Radiology Report Analysis":
                limit = active_subscription.plan.limit_report_analyses
            elif service.name == "Data Anonymization Tool":
                limit = active_subscription.plan.limit_document_anonymizations
            # Add other service limits here...

            if limit is not None and (usage.usage_count + count) > limit:
                # Option 1: Prevent usage and raise error
                raise ValidationError(f"Usage limit of {limit} for {service.name} exceeded for the current period.")
                # Option 2: Allow usage but flag it (e.g., for overage charges or soft limits)
                # usage.is_over_limit = True (add this field to model if needed)
                # print(f"Usage limit exceeded for {service.name} by {user.email}")
            
            usage.usage_count += count
            usage.save()
            return usage

        except Service.DoesNotExist:
            raise ValidationError(f"Service '{service_name}' not found.")
        except UserSubscription.DoesNotExist: # Should be caught by the filter query above
            raise ValidationError("No active subscription found.")


class BillingHistory(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('succeeded', 'Succeeded'), # Changed from 'paid' for Stripe terminology
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='billing_history')
    user_subscription = models.ForeignKey(UserSubscription, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    
    payment_gateway_invoice_id = models.CharField(max_length=255, unique=True, blank=True, null=True, help_text="Invoice ID from payment gateway (e.g., Stripe in_xxx)")
    payment_gateway_charge_id = models.CharField(max_length=255, blank=True, null=True, help_text="Charge/PaymentIntent ID from payment gateway (e.g., Stripe pi_xxx or ch_xxx)")
    
    date_created = models.DateTimeField(default=timezone.now) # When the invoice/record was created
    date_paid = models.DateTimeField(null=True, blank=True) # When it was actually paid

    plan_name_snapshot = models.CharField(max_length=100, help_text="Snapshot of the plan name at time of billing")
    amount_due = models.DecimalField(max_digits=8, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='usd') # e.g., 'usd', 'eur'
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True, null=True)
    invoice_pdf_url = models.URLField(blank=True, null=True, help_text="Link to the invoice PDF from payment gateway")

    def __str__(self):
        return f"Invoice {self.payment_gateway_invoice_id or self.id} for {self.user.email if self.user else 'N/A User'} - {self.currency.upper()} {self.amount_due} ({self.status})"

    class Meta:
        ordering = ['-date_created']
        verbose_name_plural = "Billing Histories"


class PaymentMethod(models.Model):
    CARD_TYPE_CHOICES = [
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('amex', 'American Express'),
        ('discover', 'Discover'),
        ('diners_club', 'Diners Club'),
        ('jcb', 'JCB'),
        ('unionpay', 'UnionPay'),
        ('unknown', 'Unknown'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_methods')
    payment_gateway_customer_id = models.CharField(max_length=255, help_text="Customer ID from payment gateway (e.g., Stripe cus_xxx)")
    payment_gateway_method_id = models.CharField(max_length=255, unique=True, help_text="Payment method ID from payment gateway (e.g., Stripe pm_xxx)")
    
    card_brand = models.CharField(max_length=20, choices=CARD_TYPE_CHOICES, default='unknown')
    last4 = models.CharField(max_length=4)
    exp_month = models.PositiveIntegerField()
    exp_year = models.PositiveIntegerField()
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_card_brand_display()} ending in {self.last4} for {self.user.email}"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Set other payment methods for this user to not be default
            PaymentMethod.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-is_default', '-created_at']