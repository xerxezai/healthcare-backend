import razorpay
from django.conf import settings
from django.utils import timezone
import hmac
import hashlib
import logging
from .models import UserSubscription, BillingHistory, PaymentMethod

logger = logging.getLogger(__name__)


class RazorpayService:
    """
    Service class for handling Razorpay payment gateway integration
    """
    
    def __init__(self):
        self.client = razorpay.Client(
            auth=(
                getattr(settings, 'RAZORPAY_KEY_ID', ''),
                getattr(settings, 'RAZORPAY_KEY_SECRET', '')
            )
        )
    
    def create_subscription(self, plan_id, user_email, customer_notify=True):
        """
        Create a Razorpay subscription
        """
        try:
            subscription_data = {
                'plan_id': plan_id,
                'customer_notify': customer_notify,
                'total_count': 12,  # 12 months
                'notes': {
                    'user_email': user_email,
                    'created_via': 'healthcare_platform'
                }
            }
            
            subscription = self.client.subscription.create(subscription_data)
            return subscription, None
            
        except Exception as e:
            logger.error(f"Error creating Razorpay subscription: {e}")
            return None, str(e)
    
    def create_order(self, amount, currency, receipt, notes=None):
        """
        Create a Razorpay order (recommended first step)
        """
        try:
            order_data = {
                'amount': int(amount * 100),  # Convert to paise/cents
                'currency': currency.upper(),
                'receipt': receipt,
                'notes': notes or {}
            }
            
            order = self.client.order.create(order_data)
            return order, None
            
        except razorpay.errors.BadRequestError as e:
            logger.error(f"Bad request error creating order: {e}")
            return None, f"Invalid request: {e}"
        except razorpay.errors.ServerError as e:
            logger.error(f"Server error creating order: {e}")
            return None, "Payment service temporarily unavailable"
        except Exception as e:
            logger.error(f"Error creating Razorpay order: {e}")
            return None, str(e)

    def create_payment_link(self, amount, currency, description, user_subscription_id=None, user_email='', plan_id=None):
        """
        Create a payment link for one-time payments
        Enhanced with order creation and better error handling
        Supports both authenticated (with user_subscription_id) and unauthenticated (with plan_id) users
        """
        try:
            # Create receipt based on available information
            timestamp = int(timezone.now().timestamp())
            if user_subscription_id:
                receipt = f"sub_{user_subscription_id}_{timestamp}"
                notes = {
                    'subscription_id': str(user_subscription_id),
                    'platform': 'healthcare_solution',
                    'user_email': user_email
                }
            else:
                receipt = f"plan_{plan_id}_{timestamp}"
                notes = {
                    'plan_id': str(plan_id),
                    'platform': 'healthcare_solution',
                    'user_email': user_email,
                    'type': 'unauthenticated_purchase'
                }
            
            # First create an order (recommended by Razorpay)
            order, order_error = self.create_order(
                amount=amount,
                currency=currency,
                receipt=receipt,
                notes=notes
            )
            
            if order_error:
                return None, order_error
            
            # Create payment link with the order (simplified to avoid extra fields error)
            payment_link_data = {
                'amount': int(amount * 100),  # Convert to paise/cents
                'currency': currency.upper(),
                'description': description,
                'notes': notes,
                'expire_by': int((timezone.now() + timezone.timedelta(hours=24)).timestamp()),  # 24 hour expiry
                'reminder_enable': True,
                'callback_url': f"{settings.FRONTEND_URL}/subscription/payment-success",
                'callback_method': 'get'
            }
            
            # Add customer email if provided
            if user_email:
                payment_link_data['customer'] = {'email': user_email}
            
            payment_link = self.client.payment_link.create(payment_link_data)
            
            # Return both order and payment link info
            return {
                'payment_link': payment_link,
                'order': order
            }, None
            
        except razorpay.errors.BadRequestError as e:
            logger.error(f"Bad request error creating payment link: {e}")
            return None, f"Invalid payment request: {e}"
        except razorpay.errors.ServerError as e:
            logger.error(f"Server error creating payment link: {e}")
            return None, "Payment service temporarily unavailable"
        except Exception as e:
            logger.error(f"Error creating Razorpay payment link: {e}")
            return None, str(e)
    
    def verify_payment_signature(self, razorpay_order_id, razorpay_payment_id, razorpay_signature):
        """
        Verify Razorpay payment signature for security
        Enhanced with proper error handling and validation
        """
        try:
            # Validate input parameters
            if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
                logger.error("Missing required parameters for signature verification")
                return False
            
            # Use Razorpay's built-in verification method (recommended)
            try:
                params_dict = {
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': razorpay_signature
                }
                
                # This will raise an exception if signature is invalid
                self.client.utility.verify_payment_signature(params_dict)
                logger.info(f"Payment signature verified successfully for order: {razorpay_order_id}")
                return True
                
            except razorpay.errors.SignatureVerificationError as e:
                logger.error(f"Signature verification failed: {e}")
                return False
            
        except Exception as e:
            logger.error(f"Error verifying payment signature: {e}")
            return False
    
    def verify_webhook_signature(self, body, signature):
        """
        Verify webhook signature using Razorpay's recommended method
        """
        try:
            webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')
            if not webhook_secret:
                logger.error("Webhook secret not configured")
                return False
            
            # Use Razorpay's built-in webhook verification
            self.client.utility.verify_webhook_signature(body, signature, webhook_secret)
            return True
            
        except razorpay.errors.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    def create_customer(self, user):
        """
        Create a Razorpay customer
        """
        try:
            customer_data = {
                'name': user.full_name,
                'email': user.email,
                'contact': getattr(user, 'phone_number', ''),
                'notes': {
                    'user_id': str(user.id),
                    'platform': 'healthcare_solution'
                }
            }
            
            customer = self.client.customer.create(customer_data)
            return customer, None
            
        except Exception as e:
            logger.error(f"Error creating Razorpay customer: {e}")
            return None, str(e)
    
    def create_plan(self, plan_name, amount, currency='USD', interval='monthly'):
        """
        Create a Razorpay subscription plan
        """
        try:
            plan_data = {
                'period': interval,
                'interval': 1,
                'item': {
                    'name': plan_name,
                    'amount': int(amount * 100),  # Convert to paise
                    'currency': currency,
                    'description': f'Monthly subscription for {plan_name}'
                },
                'notes': {
                    'platform': 'healthcare_solution'
                }
            }
            
            plan = self.client.plan.create(plan_data)
            return plan, None
            
        except Exception as e:
            logger.error(f"Error creating Razorpay plan: {e}")
            return None, str(e)
    
    def get_payment_details(self, payment_id):
        """
        Get payment details from Razorpay
        """
        try:
            payment = self.client.payment.fetch(payment_id)
            return payment, None
            
        except Exception as e:
            logger.error(f"Error fetching payment details: {e}")
            return None, str(e)
    
    def handle_webhook(self, event_data, signature):
        """
        Handle Razorpay webhook events with enhanced security
        """
        try:
            # Verify webhook signature using the new method
            if not self.verify_webhook_signature(event_data, signature):
                logger.warning("Invalid webhook signature")
                return False, "Invalid signature"
            
            import json
            try:
                event = json.loads(event_data)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in webhook data: {e}")
                return False, "Invalid JSON format"
            
            event_type = event.get('event')
            if not event_type:
                logger.error("Missing event type in webhook")
                return False, "Missing event type"
            
            logger.info(f"Processing webhook event: {event_type}")
            
            # Handle different event types
            event_handlers = {
                'payment.captured': self._handle_payment_captured,
                'payment.failed': self._handle_payment_failed,
                'order.paid': self._handle_order_paid,
                'subscription.activated': self._handle_subscription_activated,
                'subscription.cancelled': self._handle_subscription_cancelled,
                'subscription.charged': self._handle_subscription_charged,
                'subscription.completed': self._handle_subscription_completed,
                'subscription.halted': self._handle_subscription_halted,
                'subscription.paused': self._handle_subscription_paused,
                'subscription.resumed': self._handle_subscription_resumed,
            }
            
            handler = event_handlers.get(event_type)
            if handler:
                try:
                    entity_data = event['payload'][event_type.split('.')[0]]['entity']
                    return handler(entity_data)
                except KeyError as e:
                    logger.error(f"Missing required data in webhook payload: {e}")
                    return False, f"Invalid payload structure: {e}"
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                return True, f"Event {event_type} acknowledged but not processed"
            
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return False, str(e)
    
    def _handle_payment_captured(self, payment_data):
        """
        Handle successful payment capture
        """
        try:
            payment_id = payment_data['id']
            amount = payment_data['amount'] / 100  # Convert from paise
            
            # Find the corresponding billing record
            billing_record = BillingHistory.objects.filter(
                payment_gateway_charge_id=payment_id
            ).first()
            
            if billing_record:
                billing_record.status = 'succeeded'
                billing_record.amount_paid = amount
                billing_record.date_paid = timezone.now()
                billing_record.save()
                
                # Update subscription status if applicable
                if billing_record.user_subscription:
                    subscription = billing_record.user_subscription
                    subscription.status = 'active'
                    subscription.save()
                    
                logger.info(f"Payment captured: {payment_id}, Amount: {amount}")
                return True, "Payment processed successfully"
            
            logger.warning(f"No billing record found for payment: {payment_id}")
            return False, "Billing record not found"
            
        except Exception as e:
            logger.error(f"Error handling payment captured: {e}")
            return False, str(e)
    
    def _handle_subscription_activated(self, subscription_data):
        """
        Handle subscription activation
        """
        try:
            subscription_id = subscription_data['id']
            
            # Update user subscription status
            user_subscription = UserSubscription.objects.filter(
                payment_gateway_subscription_id=subscription_id
            ).first()
            
            if user_subscription:
                user_subscription.status = 'active'
                user_subscription.save()
                
                logger.info(f"Subscription activated: {subscription_id}")
                return True, "Subscription activated"
            
            logger.warning(f"No user subscription found for: {subscription_id}")
            return False, "User subscription not found"
            
        except Exception as e:
            logger.error(f"Error handling subscription activation: {e}")
            return False, str(e)
    
    def _handle_subscription_cancelled(self, subscription_data):
        """
        Handle subscription cancellation
        """
        try:
            subscription_id = subscription_data['id']
            
            # Update user subscription status
            user_subscription = UserSubscription.objects.filter(
                payment_gateway_subscription_id=subscription_id
            ).first()
            
            if user_subscription:
                user_subscription.status = 'cancelled'
                user_subscription.auto_renew = False
                user_subscription.save()
                
                logger.info(f"Subscription cancelled: {subscription_id}")
                return True, "Subscription cancelled"
            
            logger.warning(f"No user subscription found for: {subscription_id}")
            return False, "User subscription not found"
            
        except Exception as e:
            logger.error(f"Error handling subscription cancellation: {e}")
            return False, str(e)
    
    def _handle_payment_failed(self, payment_data):
        """
        Handle payment failure
        """
        try:
            payment_id = payment_data['id']
            error_code = payment_data.get('error_code', 'unknown')
            error_description = payment_data.get('error_description', 'Payment failed')
            
            # Find and update billing record
            billing_record = BillingHistory.objects.filter(
                payment_gateway_charge_id=payment_id
            ).first()
            
            if billing_record:
                billing_record.status = 'failed'
                billing_record.failure_reason = f"{error_code}: {error_description}"
                billing_record.save()
                
                # Update subscription status if applicable
                if billing_record.user_subscription:
                    subscription = billing_record.user_subscription
                    subscription.status = 'past_due'
                    subscription.save()
                    
                logger.info(f"Payment failed: {payment_id}, Error: {error_code}")
                return True, "Payment failure processed"
            
            logger.warning(f"No billing record found for failed payment: {payment_id}")
            return False, "Billing record not found"
            
        except Exception as e:
            logger.error(f"Error handling payment failure: {e}")
            return False, str(e)
    
    def _handle_order_paid(self, order_data):
        """
        Handle order payment completion
        """
        try:
            order_id = order_data['id']
            amount = order_data['amount'] / 100  # Convert from paise
            
            logger.info(f"Order paid: {order_id}, Amount: {amount}")
            
            # Find related subscription and update status
            notes = order_data.get('notes', {})
            subscription_id = notes.get('subscription_id')
            
            if subscription_id:
                try:
                    user_subscription = UserSubscription.objects.get(id=subscription_id)
                    user_subscription.status = 'active'
                    user_subscription.save()
                    
                    # Create billing history record
                    BillingHistory.objects.create(
                        user_subscription=user_subscription,
                        amount=amount,
                        amount_paid=amount,
                        status='succeeded',
                        date_paid=timezone.now(),
                        payment_gateway_charge_id=order_id,
                        currency=order_data.get('currency', 'USD')
                    )
                    
                    logger.info(f"Subscription activated for order: {order_id}")
                    
                except UserSubscription.DoesNotExist:
                    logger.warning(f"Subscription not found for order: {order_id}")
            
            return True, "Order payment processed"
            
        except Exception as e:
            logger.error(f"Error handling order payment: {e}")
            return False, str(e)
    
    def _handle_subscription_charged(self, subscription_data):
        """
        Handle subscription charge events
        """
        try:
            subscription_id = subscription_data['id']
            charge_amount = subscription_data.get('charge_amount', 0) / 100
            
            user_subscription = UserSubscription.objects.filter(
                payment_gateway_subscription_id=subscription_id
            ).first()
            
            if user_subscription:
                # Create billing history record for the charge
                BillingHistory.objects.create(
                    user_subscription=user_subscription,
                    amount=charge_amount,
                    amount_paid=charge_amount,
                    status='succeeded',
                    date_paid=timezone.now(),
                    payment_gateway_charge_id=f"charge_{subscription_id}_{int(timezone.now().timestamp())}",
                    currency='USD'
                )
                
                logger.info(f"Subscription charged: {subscription_id}, Amount: {charge_amount}")
                return True, "Subscription charge processed"
            
            logger.warning(f"No user subscription found for charge: {subscription_id}")
            return False, "User subscription not found"
            
        except Exception as e:
            logger.error(f"Error handling subscription charge: {e}")
            return False, str(e)
    
    def _handle_subscription_completed(self, subscription_data):
        """
        Handle subscription completion
        """
        try:
            subscription_id = subscription_data['id']
            
            user_subscription = UserSubscription.objects.filter(
                payment_gateway_subscription_id=subscription_id
            ).first()
            
            if user_subscription:
                user_subscription.status = 'completed'
                user_subscription.auto_renew = False
                user_subscription.save()
                
                logger.info(f"Subscription completed: {subscription_id}")
                return True, "Subscription completion processed"
            
            logger.warning(f"No user subscription found for completion: {subscription_id}")
            return False, "User subscription not found"
            
        except Exception as e:
            logger.error(f"Error handling subscription completion: {e}")
            return False, str(e)
    
    def _handle_subscription_halted(self, subscription_data):
        """
        Handle subscription halt (due to payment failures)
        """
        try:
            subscription_id = subscription_data['id']
            
            user_subscription = UserSubscription.objects.filter(
                payment_gateway_subscription_id=subscription_id
            ).first()
            
            if user_subscription:
                user_subscription.status = 'past_due'
                user_subscription.save()
                
                logger.info(f"Subscription halted: {subscription_id}")
                return True, "Subscription halt processed"
            
            logger.warning(f"No user subscription found for halt: {subscription_id}")
            return False, "User subscription not found"
            
        except Exception as e:
            logger.error(f"Error handling subscription halt: {e}")
            return False, str(e)
    
    def _handle_subscription_paused(self, subscription_data):
        """
        Handle subscription pause
        """
        try:
            subscription_id = subscription_data['id']
            
            user_subscription = UserSubscription.objects.filter(
                payment_gateway_subscription_id=subscription_id
            ).first()
            
            if user_subscription:
                user_subscription.status = 'paused'
                user_subscription.save()
                
                logger.info(f"Subscription paused: {subscription_id}")
                return True, "Subscription pause processed"
            
            logger.warning(f"No user subscription found for pause: {subscription_id}")
            return False, "User subscription not found"
            
        except Exception as e:
            logger.error(f"Error handling subscription pause: {e}")
            return False, str(e)
    
    def _handle_subscription_resumed(self, subscription_data):
        """
        Handle subscription resume
        """
        try:
            subscription_id = subscription_data['id']
            
            user_subscription = UserSubscription.objects.filter(
                payment_gateway_subscription_id=subscription_id
            ).first()
            
            if user_subscription:
                user_subscription.status = 'active'
                user_subscription.save()
                
                logger.info(f"Subscription resumed: {subscription_id}")
                return True, "Subscription resume processed"
            
            logger.warning(f"No user subscription found for resume: {subscription_id}")
            return False, "User subscription not found"
            
        except Exception as e:
            logger.error(f"Error handling subscription resume: {e}")
            return False, str(e)


# Global instance
razorpay_service = RazorpayService()