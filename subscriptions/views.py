from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.utils import timezone
from django.db import transaction, models
from datetime import timedelta, datetime
import calendar
import json
import logging
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponseBadRequest
from django.conf import settings

from .models import (
    SubscriptionPlan,
    UserSubscription,
    Service,
    ServiceUsage,
    BillingHistory,
    PaymentMethod,
)
from .serializers import (
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
    ServiceSerializer,
    BillingHistorySerializer,
    PaymentMethodSerializer,
    UsageStatsSerializer,
    CreatePaymentMethodSerializer,
)
from django.http import Http404
from .razorpay_service import RazorpayService

logger = logging.getLogger(__name__)


# --- Placeholder for Payment Gateway Service ---
class MockPaymentGateway:
    def create_customer(self, user):
        print(f"MockPaymentGateway: Creating customer for {user.email}")
        # Simulate a unique customer ID
        return f"cus_{user.id}_{int(timezone.now().timestamp())}"

    def create_payment_method(self, token, customer_id):
        print(
            f"MockPaymentGateway: Creating payment method with token {token} for customer {customer_id}"
        )
        return {
            "id": f"pm_{token[:8]}_{int(timezone.now().timestamp())}",
            "brand": "visa",
            "last4": "4242",
            "exp_month": 12,
            "exp_year": timezone.now().year + 3,
        }

    def attach_payment_method_to_customer(self, pm_id, customer_id):
        print(f"MockPaymentGateway: Attaching PM {pm_id} to customer {customer_id}")
        return True

    def set_default_payment_method(self, customer_id, pm_id):
        print(
            f"MockPaymentGateway: Setting PM {pm_id} as default for customer {customer_id}"
        )
        return True

    def delete_payment_method(self, pm_id):
        print(f"MockPaymentGateway: Deleting PM {pm_id}")
        return True

    def create_subscription(self, customer_id, plan_price_id, default_pm_id):
        print(
            f"MockPaymentGateway: Creating subscription for customer {customer_id} with plan {plan_price_id} and PM {default_pm_id}"
        )
        # Simulate a new subscription ID
        new_sub_id = f"sub_new_{int(timezone.now().timestamp())}"
        return {
            "id": new_sub_id,
            "current_period_start": timezone.now().timestamp(),
            "current_period_end": (timezone.now() + timedelta(days=30)).timestamp(),
            "status": "active",
        }

    def update_subscription(self, gateway_sub_id, new_plan_price_id):
        print(
            f"MockPaymentGateway: Updating subscription {gateway_sub_id} to plan {new_plan_price_id}"
        )
        # For an update, the gateway_sub_id typically remains the same
        return {
            "id": gateway_sub_id,  # Important: ID remains the same
            "current_period_start": timezone.now().timestamp(),  # Or actual new period start from gateway
            "current_period_end": (
                timezone.now() + timedelta(days=30)
            ).timestamp(),  # New period end
            "status": "active",
        }

    def cancel_subscription(self, gateway_sub_id, at_period_end=True):
        print(
            f"MockPaymentGateway: Cancelling subscription {gateway_sub_id} (at_period_end={at_period_end})"
        )
        return {"status": "active" if at_period_end else "canceled"}


payment_gateway = MockPaymentGateway()


# ... (rest of your imports and helper functions)
def get_current_billing_cycle_for_subscription(user_subscription):
    # This is a simplified example. Real-world cycle calculation can be complex.
    # It depends on whether billing is anniversary-based or fixed-day-of-month.
    # For this example, we assume the UserSubscription's start_date and end_date
    # accurately reflect the *current* active billing period.
    # In a system with renewals, these dates would be updated by webhooks or tasks.
    today = timezone.now().date()
    if user_subscription.start_date <= today <= user_subscription.end_date:
        return user_subscription.start_date, user_subscription.end_date

    # Fallback or error if the subscription object isn't for the current period
    # This indicates a need for more robust cycle management if UserSubscription objects are long-lived.
    # For now, we'll assume the passed user_subscription is the one for the current period.
    # If no active period, we might default to the current month for general stats display.
    first_day_current_month = today.replace(day=1)
    last_day_current_month = first_day_current_month.replace(
        day=calendar.monthrange(today.year, today.month)[1]
    )
    return first_day_current_month, last_day_current_month


class ServiceListView(generics.ListAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.AllowAny]


class SubscriptionPlanListView(generics.ListAPIView):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [
        permissions.AllowAny
    ]  # Users should see plans before logging in too


class UserSubscriptionDetailView(generics.RetrieveAPIView):
    serializer_class = UserSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Bypass subscription requirement for superusers and admin role
        if getattr(self.request.user, 'is_superuser', False) or getattr(self.request.user, 'role', None) == 'admin':
            # Create a virtual subscription object for admins with unlimited access
            from .models import SubscriptionPlan
            
            # Get the most premium plan or create a virtual one
            premium_plan = SubscriptionPlan.objects.filter(is_active=True).order_by('-price_monthly').first()
            if not premium_plan:
                # Create a virtual plan object for display purposes
                class VirtualPlan:
                    def __init__(self):
                        self.id = 999
                        self.name = "Super Admin Access"
                        self.description = "Unlimited access to all features"
                        self.price_monthly = 0.00
                        self.currency = "USD"
                        self.limit_chatbot_messages = None
                        self.limit_mcq_generations = None
                        self.limit_report_analyses = None
                        self.limit_document_anonymizations = None
                        self.is_active = True
                
                premium_plan = VirtualPlan()
            
            # Create virtual subscription for super users
            class VirtualSubscription:
                def __init__(self, user, plan):
                    self.id = 999
                    self.user = user
                    self.plan = plan
                    self.status = "active"
                    self.start_date = timezone.now().date()
                    self.end_date = timezone.now().date() + timezone.timedelta(days=365)  # 1 year
                    self.auto_renew = True
                    self.payment_gateway_subscription_id = "admin_access"
            
            return VirtualSubscription(self.request.user, premium_plan)
        
        # Get the most relevant subscription: active, then trial, then most recent non-active.
        subscription = (
            UserSubscription.objects.filter(
                user=self.request.user,
                status__in=[
                    "active",
                    "trial",
                    "past_due",
                ],  # Include past_due as they might want to update payment
                end_date__gte=timezone.now().date(),
            )
            .order_by("-status", "-end_date")
            .first()
        )  # Prioritize active, then trial

        if not subscription:
            # If no currently "usable" subscription, show the latest one (even if expired/cancelled)
            subscription = (
                UserSubscription.objects.filter(user=self.request.user)
                .order_by("-end_date")
                .first()
            )

        if not subscription:
            raise Http404("No subscription found for this user.")
        return subscription


class UsageStatsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Bypass subscription requirement for superusers and admin role
        if getattr(user, 'is_superuser', False) or getattr(user, 'role', None) == 'admin':
            today = timezone.now().date()
            first_day_current_month = today.replace(day=1)
            last_day_current_month = first_day_current_month.replace(
                day=calendar.monthrange(today.year, today.month)[1]
            )

            stats_data = {
                "chatbot_messages_current_period": 0,
                "chatbot_sessions_current_period": 0,
                "mcqs_generated_current_period": 0,
                "pdfs_for_mcq_current_period": 0,
                "reports_analyzed_current_period": 0,
                "documents_anonymized_current_period": 0,
                "limit_chatbot_messages": None,  # Unlimited for admins
                "limit_mcq_generations": None,   # Unlimited for admins
                "limit_report_analyses": None,   # Unlimited for admins
                "limit_document_anonymizations": None,  # Unlimited for admins
                "current_cycle_start_date": first_day_current_month,
                "current_cycle_end_date": last_day_current_month,
            }
            serializer = UsageStatsSerializer(data=stats_data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data)
        
        active_subscription = (
            UserSubscription.objects.filter(
                user=user,
                status__in=["active", "trial"],
                end_date__gte=timezone.now().date(),
            )
            .order_by("-start_date")
            .first()
        )

        if not active_subscription:
            # Return default/zeroed stats if no active subscription
            today = timezone.now().date()
            first_day_current_month = today.replace(day=1)
            last_day_current_month = first_day_current_month.replace(
                day=calendar.monthrange(today.year, today.month)[1]
            )

            stats_data = {
                "chatbot_messages_current_period": 0,
                "chatbot_sessions_current_period": 0,
                "mcqs_generated_current_period": 0,
                "pdfs_for_mcq_current_period": 0,
                "reports_analyzed_current_period": 0,
                "documents_anonymized_current_period": 0,
                "limit_chatbot_messages": None,
                "limit_mcq_generations": None,
                "limit_report_analyses": None,
                "limit_document_anonymizations": None,
                "current_cycle_start_date": first_day_current_month,
                "current_cycle_end_date": last_day_current_month,
            }
            serializer = UsageStatsSerializer(data=stats_data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data)

        period_start, period_end = get_current_billing_cycle_for_subscription(
            active_subscription
        )

        stats_data = {
            "chatbot_messages_current_period": 0,
            "chatbot_sessions_current_period": 0,
            "mcqs_generated_current_period": 0,
            "pdfs_for_mcq_current_period": 0,
            "reports_analyzed_current_period": 0,
            "documents_anonymized_current_period": 0,
            "limit_chatbot_messages": active_subscription.plan.limit_chatbot_messages,
            "limit_mcq_generations": active_subscription.plan.limit_mcq_generations,
            "limit_report_analyses": active_subscription.plan.limit_report_analyses,
            "limit_document_anonymizations": active_subscription.plan.limit_document_anonymizations,
            "current_cycle_start_date": period_start,
            "current_cycle_end_date": period_end,
        }

        usages = ServiceUsage.objects.filter(
            user_subscription=active_subscription,
            period_start_date=period_start,  # Match the exact cycle
        )

        for usage in usages:
            if usage.service.name == "Dr. Max AI Chatbot":
                stats_data["chatbot_messages_current_period"] = usage.usage_count
            elif usage.service.name == "Intelligent MCQ Generator":
                stats_data["mcqs_generated_current_period"] = usage.usage_count
            elif usage.service.name == "Radiology Report Analysis":
                stats_data["reports_analyzed_current_period"] = usage.usage_count
            elif usage.service.name == "Data Anonymization Tool":
                stats_data["documents_anonymized_current_period"] = usage.usage_count

        # Placeholder for sessions and PDF counts - these might need more complex tracking
        # stats_data['chatbot_sessions_current_period'] = stats_data['chatbot_messages_current_period'] // 5 # Example
        # stats_data['pdfs_for_mcq_current_period'] = stats_data['mcqs_generated_current_period'] // 10 # Example

        serializer = UsageStatsSerializer(data=stats_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class BillingHistoryListView(generics.ListAPIView):
    serializer_class = BillingHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BillingHistory.objects.filter(user=self.request.user).order_by(
            "-date_created"
        )


class PaymentMethodListView(
    generics.ListAPIView
):  # Changed from ListCreate for separation
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user).order_by(
            "-is_default", "-created_at"
        )


class CreatePaymentMethodView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = CreatePaymentMethodSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            token = serializer.validated_data["payment_token"]
            set_as_default = serializer.validated_data.get("set_as_default", False)

            try:
                # 1. Get or create payment gateway customer ID for the user
                pg_customer_id = None
                # Attempt to get from StaffProfile or PatientProfile - adapt to your actual profile model structure
                if (
                    hasattr(user, "staffprofile")
                    and user.staffprofile
                    and hasattr(user.staffprofile, "payment_gateway_customer_id")
                    and user.staffprofile.payment_gateway_customer_id
                ):
                    pg_customer_id = user.staffprofile.payment_gateway_customer_id
                elif (
                    hasattr(user, "patientprofile")
                    and user.patientprofile
                    and hasattr(user.patientprofile, "payment_gateway_customer_id")
                    and user.patientprofile.payment_gateway_customer_id
                ):
                    pg_customer_id = user.patientprofile.payment_gateway_customer_id

                if not pg_customer_id:
                    pg_customer_id = payment_gateway.create_customer(user)
                    # Save pg_customer_id to user's profile
                    # This part needs robust handling based on your user profile setup.
                    # Example:
                    # if hasattr(user, 'staffprofile') and user.staffprofile:
                    #     user.staffprofile.payment_gateway_customer_id = pg_customer_id
                    #     user.staffprofile.save()
                    # elif hasattr(user, 'patientprofile') and user.patientprofile:
                    #     user.patientprofile.payment_gateway_customer_id = pg_customer_id
                    #     user.patientprofile.save()
                    # else:
                    # Fallback or error if no profile to save to
                    print(
                        f"Mock: Associated pg_customer_id {pg_customer_id} with user {user.email}."
                    )

                # 2. Create payment method on gateway
                gateway_pm_details = payment_gateway.create_payment_method(
                    token, pg_customer_id
                )

                # 3. Attach to customer on gateway (some gateways do this automatically with creation)
                payment_gateway.attach_payment_method_to_customer(
                    gateway_pm_details["id"], pg_customer_id
                )

                # 4. Save to local DB
                with transaction.atomic():
                    new_pm = PaymentMethod.objects.create(
                        user=user,
                        payment_gateway_customer_id=pg_customer_id,
                        payment_gateway_method_id=gateway_pm_details["id"],
                        card_brand=gateway_pm_details["brand"],
                        last4=gateway_pm_details["last4"],
                        exp_month=gateway_pm_details["exp_month"],
                        exp_year=gateway_pm_details["exp_year"],
                        is_default=set_as_default,  # This will trigger the model's save method logic
                    )

                # 5. (Optional) If set_as_default, update gateway's default PM for customer/subscription
                if set_as_default:
                    payment_gateway.set_default_payment_method(
                        pg_customer_id, new_pm.payment_gateway_method_id
                    )

                return Response(
                    PaymentMethodSerializer(new_pm).data, status=status.HTTP_201_CREATED
                )
            except Exception as e:
                # Log the error
                print(f"Error creating payment method: {str(e)}")
                return Response(
                    {"error": f"Could not add payment method: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentMethodDetailView(generics.DestroyAPIView):  # Only allowing DELETE for now
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        try:
            # Detach/delete from payment gateway first
            payment_gateway.delete_payment_method(instance.payment_gateway_method_id)
            instance.delete()
        except Exception as e:
            # Log error
            print(f"Error deleting payment method {instance.id} from gateway: {str(e)}")
            # Decide if you still want to delete locally or return an error
            # For now, let's assume if gateway fails, we don't delete locally to avoid inconsistency
            raise serializers.ValidationError(
                {
                    "error": "Failed to delete payment method from payment provider. Please try again."
                }
            )


class SetDefaultPaymentMethodView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk, *args, **kwargs):
        user = request.user
        try:
            payment_method_to_set_default = PaymentMethod.objects.get(pk=pk, user=user)

            # Update on payment gateway
            if payment_gateway.set_default_payment_method(
                payment_method_to_set_default.payment_gateway_customer_id,
                payment_method_to_set_default.payment_gateway_method_id,
            ):
                # Model's save method handles unsetting other local defaults
                payment_method_to_set_default.is_default = True
                payment_method_to_set_default.save()
                return Response(
                    {"message": "Default payment method updated successfully."},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"error": "Failed to set default payment method with provider."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except PaymentMethod.DoesNotExist:
            return Response(
                {"error": "Payment method not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChangePlanView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user
        new_plan_id = request.data.get("plan_id")

        if not new_plan_id:
            return Response(
                {"error": "plan_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            new_plan = SubscriptionPlan.objects.get(id=new_plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {"error": "Invalid or inactive plan selected."},
                status=status.HTTP_404_NOT_FOUND,
            )

        current_subscription = (
            UserSubscription.objects.filter(
                user=user,
                status__in=["active", "trial", "past_due"],
                end_date__gte=timezone.now().date(),
            )
            .order_by("-start_date")
            .first()
        )

        if current_subscription and current_subscription.plan.id == new_plan.id:
            return Response(
                {"message": "You are already subscribed to this plan."},
                status=status.HTTP_200_OK,
            )

        pg_customer_id = None
        if (
            hasattr(user, "staffprofile")
            and user.staffprofile
            and hasattr(user.staffprofile, "payment_gateway_customer_id")
            and user.staffprofile.payment_gateway_customer_id
        ):
            pg_customer_id = user.staffprofile.payment_gateway_customer_id
        elif (
            hasattr(user, "patientprofile")
            and user.patientprofile
            and hasattr(user.patientprofile, "payment_gateway_customer_id")
            and user.patientprofile.payment_gateway_customer_id
        ):
            pg_customer_id = user.patientprofile.payment_gateway_customer_id

        if not pg_customer_id:
            pg_customer_id = payment_gateway.create_customer(user)
            # TODO: Save pg_customer_id to user's profile model here
            # Example:
            # if hasattr(user, 'staffprofile') and user.staffprofile:
            #     user.staffprofile.payment_gateway_customer_id = pg_customer_id
            #     user.staffprofile.save()
            # elif hasattr(user, 'patientprofile') and user.patientprofile:
            #     user.patientprofile.payment_gateway_customer_id = pg_customer_id
            #     user.patientprofile.save()
            print(
                f"Mock: Associated pg_customer_id {pg_customer_id} with user {user.email}."
            )

        default_pm = PaymentMethod.objects.filter(user=user, is_default=True).first()
        if not default_pm:
            return Response(
                {"error": "No default payment method found. Please add one."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment_method_to_use_pg_id = default_pm.payment_gateway_method_id
        gateway_sub_details = None
        local_user_sub_for_response = None  # To store the sub object for response

        if (
            current_subscription
            and current_subscription.payment_gateway_subscription_id
        ):
            # Scenario: User has an existing subscription managed by the payment gateway.
            # We update this subscription on the gateway.
            gateway_sub_details = payment_gateway.update_subscription(
                current_subscription.payment_gateway_subscription_id,
                new_plan.id,  # In Stripe, this would be a Price ID
            )
            if not gateway_sub_details:
                return Response(
                    {"error": "Failed to update subscription with payment provider."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Update the existing local UserSubscription record
            current_subscription.plan = new_plan
            current_subscription.start_date = datetime.fromtimestamp(
                gateway_sub_details["current_period_start"], tz=timezone.utc
            ).date()
            current_subscription.end_date = datetime.fromtimestamp(
                gateway_sub_details["current_period_end"], tz=timezone.utc
            ).date()
            current_subscription.status = gateway_sub_details["status"]
            current_subscription.auto_renew = True  # Typically reset on plan change
            current_subscription.save()
            local_user_sub_for_response = current_subscription

        else:
            # Scenario: User has no existing gateway subscription, or their current local one isn't tied to a gateway ID.
            # We create a new subscription on the payment gateway.
            gateway_sub_details = payment_gateway.create_subscription(
                pg_customer_id,
                new_plan.id,  # In Stripe, this would be a Price ID
                payment_method_to_use_pg_id,
            )
            if not gateway_sub_details:
                return Response(
                    {"error": "Failed to create subscription with payment provider."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # If there was a local subscription (not gateway managed), mark it as superseded/cancelled.
            if current_subscription:
                current_subscription.status = "cancelled"
                current_subscription.auto_renew = False
                current_subscription.save()

            start_date = datetime.fromtimestamp(
                gateway_sub_details["current_period_start"], tz=timezone.utc
            ).date()
            end_date = datetime.fromtimestamp(
                gateway_sub_details["current_period_end"], tz=timezone.utc
            ).date()

            # Create a new local UserSubscription record for the new gateway subscription
            local_user_sub_for_response = UserSubscription.objects.create(
                user=user,
                plan=new_plan,
                start_date=start_date,
                end_date=end_date,
                status=gateway_sub_details["status"],
                payment_gateway_subscription_id=gateway_sub_details[
                    "id"
                ],  # This is the NEW ID from the gateway
                auto_renew=True,
            )

        # Create BillingHistory record for the new/changed plan
        # Use the local_user_sub_for_response which is either the updated or newly created sub
        
        current_timestamp_for_id = int(timezone.now().timestamp())
        
        BillingHistory.objects.create(
            user=user,
            user_subscription=local_user_sub_for_response,
            payment_gateway_invoice_id=f"inv_{gateway_sub_details['id']}_{current_timestamp_for_id}",
            payment_gateway_charge_id=f"ch_{gateway_sub_details['id']}_{current_timestamp_for_id}",
            date_created=timezone.now(),
            date_paid=(
                timezone.now() if gateway_sub_details["status"] == "active" else None
            ),
            plan_name_snapshot=new_plan.name,
            amount_due=new_plan.price_monthly,
            amount_paid=(
                new_plan.price_monthly
                if gateway_sub_details["status"] == "active"
                else 0.00
            ),
            currency=new_plan.currency.lower(),
            status=(
                "succeeded" if gateway_sub_details["status"] == "active" else "pending"
            ),
            description=f"Subscription to {new_plan.name}",
        )

        serializer = UserSubscriptionSerializer(local_user_sub_for_response)
        return Response(
            {"message": "Plan changed successfully.", "subscription": serializer.data},
            status=status.HTTP_200_OK,
        )


class CancelSubscriptionView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user
        active_subscription = (
            UserSubscription.objects.filter(
                user=user,
                status__in=["active", "trial"],
                end_date__gte=timezone.now().date(),
            )
            .order_by("-start_date")
            .first()
        )

        if not active_subscription:
            return Response(
                {"error": "No active subscription to cancel."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not active_subscription.payment_gateway_subscription_id:
            active_subscription.status = "cancelled"
            active_subscription.auto_renew = False
            active_subscription.save()
            serializer = UserSubscriptionSerializer(active_subscription)
            return Response(
                {
                    "message": "Subscription marked as cancelled. Access will remain until the current period ends.",
                    "subscription": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        try:
            payment_gateway.cancel_subscription(
                active_subscription.payment_gateway_subscription_id, at_period_end=True
            )
            active_subscription.status = "cancelled"
            active_subscription.auto_renew = False
            active_subscription.save()

            serializer = UserSubscriptionSerializer(active_subscription)
            return Response(
                {
                    "message": "Subscription cancellation initiated. Access will remain until the current period ends.",
                    "subscription": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(
                f"Error cancelling subscription {active_subscription.payment_gateway_subscription_id} with gateway: {str(e)}"
            )
            return Response(
                {
                    "error": "Failed to cancel subscription with payment provider. Please contact support."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# --- Razorpay Integration Views ---

class RazorpayCreatePaymentLinkView(views.APIView):
    """
    Create a Razorpay payment link for subscription payment - allows unauthenticated users
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        plan_id = request.data.get('plan_id')
        customer_email = request.data.get('customer_email', '')  # Optional email for payment
        
        if not plan_id:
            return Response(
                {'error': 'plan_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {'error': 'Invalid plan selected'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # For unauthenticated users, create payment link without user subscription
        try:
            # Create payment link for the plan without creating subscription yet
            payment_result, error = razorpay_service.create_payment_link(
                amount=float(plan.price_monthly),
                currency=plan.currency,
                description=f'Subscription to {plan.name}',
                user_subscription_id=None,  # No subscription yet
                user_email=customer_email,
                plan_id=plan.id  # Pass plan_id for later processing
            )
            
            if error:
                logger.error(f"Error creating payment link: {error}")
                return Response(
                    {'error': f'Failed to create payment link: {error}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Extract payment link and order data
            payment_link = payment_result['payment_link']
            order = payment_result['order']
            
            return Response({
                'payment_link': payment_link.get('short_url'),
                'payment_link_id': payment_link.get('id'),
                'order_id': order['id'],
                'plan_id': plan.id,
                'amount': float(plan.price_monthly),
                'currency': plan.currency,
                'expires_at': payment_link.get('expire_by')
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating payment link: {e}")
            return Response(
                {'error': 'Failed to create payment link'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RazorpayPaymentSuccessView(views.APIView):
    """
    Handle successful payment callback from Razorpay
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        user = request.user
        payment_link_id = request.data.get('payment_link_id')
        payment_id = request.data.get('payment_id')
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_signature = request.data.get('razorpay_signature')
        
        # Validate required fields
        required_fields = ['payment_link_id', 'payment_id']
        if not all(request.data.get(field) for field in required_fields):
            return Response(
                {'error': f'Required fields: {", ".join(required_fields)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Find the billing record
            billing_record = BillingHistory.objects.filter(
                user=user,
                payment_gateway_invoice_id=payment_link_id,
                status='pending'
            ).first()
            
            if not billing_record:
                return Response(
                    {'error': 'Payment record not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get payment details from Razorpay
            payment_details, error = razorpay_service.get_payment_details(payment_id)
            if error:
                logger.error(f"Error fetching payment details: {error}")
                return Response(
                    {'error': 'Failed to verify payment'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Verify payment signature if provided (for enhanced security)
            if razorpay_order_id and razorpay_signature:
                signature_valid = razorpay_service.verify_payment_signature(
                    razorpay_order_id, payment_id, razorpay_signature
                )
                if not signature_valid:
                    logger.warning(f"Invalid payment signature for payment {payment_id}")
                    return Response(
                        {'error': 'Payment verification failed'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Verify payment status and amount
            if payment_details.get('status') == 'captured':
                paid_amount = payment_details.get('amount', 0) / 100  # Convert from paise
                expected_amount = float(billing_record.amount_due)
                
                # Verify amount matches (allow small variance for currency conversion)
                if abs(paid_amount - expected_amount) > 0.01:
                    logger.error(f"Amount mismatch: paid {paid_amount}, expected {expected_amount}")
                    return Response(
                        {'error': 'Payment amount verification failed'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                with transaction.atomic():
                    # Update billing record
                    billing_record.status = 'succeeded'
                    billing_record.amount_paid = paid_amount
                    billing_record.date_paid = timezone.now()
                    billing_record.payment_gateway_charge_id = payment_id
                    billing_record.save()
                    
                    # Update subscription status
                    user_subscription = billing_record.user_subscription
                    user_subscription.status = 'active'
                    user_subscription.save()
                    
                    logger.info(f"Payment successful for user {user.email}, amount: {paid_amount}")
                    
                    return Response({
                        'success': True,
                        'message': 'Payment successful, subscription activated',
                        'subscription': UserSubscriptionSerializer(user_subscription).data,
                        'payment': {
                            'payment_id': payment_id,
                            'amount_paid': paid_amount,
                            'currency': payment_details.get('currency', 'USD').upper(),
                            'method': payment_details.get('method', 'unknown')
                        }
                    }, status=status.HTTP_200_OK)
            else:
                payment_status = payment_details.get('status', 'unknown')
                logger.warning(f"Payment not captured, status: {payment_status}")
                return Response(
                    {'error': f'Payment not completed. Status: {payment_status}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Error processing payment success: {e}")
            return Response(
                {'error': 'Failed to process payment. Please contact support.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookView(views.APIView):
    """
    Handle Razorpay webhook events
    """
    permission_classes = [permissions.AllowAny]  # Webhook doesn't send auth tokens
    
    def post(self, request, *args, **kwargs):
        try:
            # Get webhook signature from headers
            signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE')
            if not signature:
                logger.warning("Webhook received without signature")
                return JsonResponse({'error': 'Missing signature'}, status=400)
            
            # Process webhook
            success, message = razorpay_service.handle_webhook(
                request.body.decode('utf-8'), 
                signature
            )
            
            if success:
                return JsonResponse({'status': 'success', 'message': message})
            else:
                logger.error(f"Webhook processing failed: {message}")
                return JsonResponse({'error': message}, status=400)
                
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return JsonResponse({'error': 'Webhook processing failed'}, status=500)


class RazorpayCreateCustomerView(views.APIView):
    """
    Create a Razorpay customer for the authenticated user
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        user = request.user
        
        try:
            customer, error = razorpay_service.create_customer(user)
            if error:
                return Response(
                    {'error': f'Failed to create customer: {error}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Store customer ID in user profile (you may need to adapt this to your user model)
            # user.razorpay_customer_id = customer['id']
            # user.save()
            
            return Response({
                'customer_id': customer['id'],
                'message': 'Customer created successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating customer: {e}")
            return Response(
                {'error': 'Failed to create customer'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def create_razorpay_order(request):
    """
    Create a Razorpay order for custom checkout
    This replaces payment links with a more branded experience
    """
    try:
        plan_id = request.data.get('plan_id')
        user_email = request.data.get('email', '')
        
        if not plan_id:
            return Response({
                'error': 'Plan ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get plan details
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            return Response({
                'error': 'Invalid plan selected'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initialize Razorpay service
        razorpay_service = RazorpayService()
        
        # Create order with detailed receipt and notes
        timestamp = int(timezone.now().timestamp())
        receipt = f"plan_{plan_id}_{timestamp}"
        notes = {
            'plan_id': str(plan_id),
            'plan_name': plan.name,
            'platform': 'healthcare_solution',
            'user_email': user_email,
            'type': 'subscription_purchase'
        }
        
        order, error = razorpay_service.create_order(
            amount=float(plan.price_monthly),
            currency=plan.currency,
            receipt=receipt,
            notes=notes
        )
        
        if error:
            return Response({
                'error': error
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Return order details with Razorpay key for frontend
        return Response({
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency'],
            'plan_id': plan_id,
            'plan_name': plan.name,
            'plan_description': plan.description,
            'key': settings.RAZORPAY_KEY_ID,  # Frontend needs this for checkout
            'receipt': receipt
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating Razorpay order: {e}")
        return Response({
            'error': 'Failed to create payment order'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_payment(request):
    """
    Verify payment after successful Razorpay payment
    """
    try:
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')
        user_email = request.data.get('email', '')
        plan_id = request.data.get('plan_id')
        
        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return Response({
                'error': 'Missing payment verification data'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initialize Razorpay service and verify signature
        razorpay_service = RazorpayService()
        is_valid = razorpay_service.verify_payment_signature(
            razorpay_order_id, 
            razorpay_payment_id, 
            razorpay_signature
        )
        
        if not is_valid:
            return Response({
                'error': 'Payment verification failed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get payment details from Razorpay
        payment_details, error = razorpay_service.get_payment_details(razorpay_payment_id)
        if error:
            logger.error(f"Error fetching payment details: {error}")
            return Response({
                'error': 'Failed to fetch payment details'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get plan details
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            return Response({
                'error': 'Invalid plan'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Store payment success information for later subscription creation
        # User can create account after payment with this verification
        verification_data = {
            'payment_verified': True,
            'payment_id': razorpay_payment_id,
            'order_id': razorpay_order_id,
            'plan_id': plan_id,
            'plan_name': plan.name,
            'amount_paid': payment_details.get('amount', 0) / 100,  # Convert from paise
            'currency': payment_details.get('currency', 'USD'),
            'user_email': user_email,
            'payment_method': payment_details.get('method', 'unknown'),
            'paid_at': timezone.now().isoformat()
        }
        
        return Response(verification_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error verifying payment: {e}")
        return Response({
            'error': 'Payment verification failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def create_user_from_payment(request):
    """
    Create user account automatically after successful payment verification
    This is the missing link - users who pay should get accounts automatically!
    """
    try:
        logger.info("=== create_user_from_payment called ===")
        logger.info(f"Request data: {request.data}")
        
        # Get payment verification data and user info
        payment_data = request.data.get('payment_data', {})
        customer_info = request.data.get('customer_info', {})
        password = request.data.get('password', 'temp123')  # Temporary password
        
        logger.info(f"Payment data: {payment_data}")
        logger.info(f"Customer info: {customer_info}")
        
        # Validate required data
        if not payment_data.get('payment_verified'):
            return Response({
                'error': 'Payment verification required'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        user_email = customer_info.get('email') or payment_data.get('user_email')
        user_name = customer_info.get('name') or customer_info.get('full_name', 'Customer')
        
        if not user_email:
            return Response({
                'error': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user already exists
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if User.objects.filter(email=user_email).exists():
            return Response({
                'error': 'User already exists with this email'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get plan details
        plan_id = payment_data.get('plan_id')
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            return Response({
                'error': 'Invalid plan'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create user account with minimal required info
        with transaction.atomic():
            # Generate secure temporary password
            import secrets
            temp_password = secrets.token_urlsafe(12)
            
            # Create user with auto-generated username
            username_base = user_email.split('@')[0]
            username = username_base
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{username_base}{counter}"
                counter += 1
            
            # Create user
            user = User.objects.create_user(
                email=user_email,
                username=username,
                password=temp_password,
                full_name=user_name,
                phone_number=customer_info.get('phone', ''),
                role='patient',  # Default role for paying customers
                is_verified=True  # Auto-verify since they paid
            )
            
            # Create subscription
            user_subscription = UserSubscription.objects.create(
                user=user,
                plan=plan,
                start_date=timezone.now().date(),
                end_date=timezone.now().date() + timezone.timedelta(days=30),  # 30 days
                status='active',
                payment_gateway_subscription_id=payment_data.get('payment_id'),
                auto_renew=True
            )
            
            # Create billing history record
            BillingHistory.objects.create(
                user=user,
                user_subscription=user_subscription,
                payment_gateway_invoice_id=payment_data.get('order_id'),
                payment_gateway_charge_id=payment_data.get('payment_id'),
                date_created=timezone.now(),
                date_paid=timezone.now(),
                plan_name_snapshot=plan.name,
                amount_due=payment_data.get('amount_paid', 0),
                amount_paid=payment_data.get('amount_paid', 0),
                currency=payment_data.get('currency', 'USD'),
                status='succeeded',
                description=f'Initial subscription to {plan.name}'
            )
            
            # Generate tokens for auto-login
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            
            logger.info(f"Auto-created user account for payment: {user_email}, plan: {plan.name}")
            
            return Response({
                'success': True,
                'message': 'Account created successfully from payment',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role
                },
                'subscription': {
                    'plan_name': plan.name,
                    'status': user_subscription.status,
                    'end_date': user_subscription.end_date
                },
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                },
                                 'temp_password': temp_password  # Send temp password so user can login
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        logger.error(f"Error creating user from payment: {e}")
        return Response({
            'error': 'Failed to create user account'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# === ADMIN VIEWS FOR SUBSCRIPTION MANAGEMENT ===

class AdminOverviewView(views.APIView):
    """
    Admin overview statistics for subscription dashboard
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # Check if user is admin/superuser
        if not (request.user.is_superuser or getattr(request.user, 'role', None) == 'admin'):
            return Response(
                {'error': 'Admin access required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Total users
        total_users = UserSubscription.objects.values('user').distinct().count()
        
        # Active subscriptions
        active_subscriptions = UserSubscription.objects.filter(
            status__in=['active', 'trial'],
            end_date__gte=timezone.now().date()
        ).count()
        
        # Revenue calculation
        total_revenue = BillingHistory.objects.filter(
            status='succeeded',
            date_paid__gte=start_date,
            date_paid__lte=end_date
        ).aggregate(total=models.Sum('amount_paid'))['total'] or 0
        
        # New subscriptions in period
        new_subscriptions = UserSubscription.objects.filter(
            start_date__gte=start_date,
            start_date__lte=end_date
        ).count()
        
        # Cancelled subscriptions in period
        cancelled_subscriptions = UserSubscription.objects.filter(
            status='cancelled',
            updated_at__gte=start_date,
            updated_at__lte=end_date
        ).count()
        
        # Calculate churn rate
        churn_rate = 0
        if active_subscriptions > 0:
            churn_rate = (cancelled_subscriptions / (active_subscriptions + cancelled_subscriptions)) * 100
        
        # Calculate conversion rate (trial to active)
        trial_count = UserSubscription.objects.filter(status='trial').count()
        conversion_rate = 0
        if trial_count > 0:
            active_from_trial = UserSubscription.objects.filter(
                status='active',
                start_date__gte=start_date
            ).count()
            conversion_rate = (active_from_trial / (trial_count + active_from_trial)) * 100
        
        # Revenue growth (compare with previous period)
        prev_start_date = start_date - timedelta(days=days)
        prev_revenue = BillingHistory.objects.filter(
            status='succeeded',
            date_paid__gte=prev_start_date,
            date_paid__lt=start_date
        ).aggregate(total=models.Sum('amount_paid'))['total'] or 0
        
        revenue_growth = 0
        if prev_revenue > 0:
            revenue_growth = ((total_revenue - prev_revenue) / prev_revenue) * 100
        
        return Response({
            'totalUsers': total_users,
            'activeSubscriptions': active_subscriptions,
            'totalRevenue': float(total_revenue),
            'churnRate': round(churn_rate, 1),
            'revenueGrowth': round(revenue_growth, 1),
            'newSubscriptions': new_subscriptions,
            'cancelledSubscriptions': cancelled_subscriptions,
            'conversionRate': round(conversion_rate, 1)
        })


class AdminSubscriptionsListView(generics.ListAPIView):
    """
    Admin view of all subscriptions with filtering
    """
    serializer_class = UserSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Check if user is admin/superuser
        if not (self.request.user.is_superuser or getattr(self.request.user, 'role', None) == 'admin'):
            return UserSubscription.objects.none()
        
        queryset = UserSubscription.objects.all().select_related('user', 'plan')
        
        # Apply filters
        status = self.request.query_params.get('status')
        if status and status != 'all':
            queryset = queryset.filter(status=status)
        
        plan_id = self.request.query_params.get('plan')
        if plan_id and plan_id != 'all':
            queryset = queryset.filter(plan_id=plan_id)
        
        days = self.request.query_params.get('days')
        if days:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=int(days))
            queryset = queryset.filter(start_date__gte=start_date)
        
        return queryset.order_by('-start_date')


class AdminUsersListView(generics.ListAPIView):
    """
    Admin view of all users with subscription info
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # Check if user is admin/superuser
        if not (request.user.is_superuser or getattr(request.user, 'role', None) == 'admin'):
            return Response(
                {'error': 'Admin access required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        users = User.objects.all().prefetch_related('user_subscriptions')
        
        user_data = []
        for user in users:
            active_sub = user.user_subscriptions.filter(
                status__in=['active', 'trial'],
                end_date__gte=timezone.now().date()
            ).first()
            
            user_data.append({
                'id': user.id,
                'email': user.email,
                'first_name': getattr(user, 'first_name', ''),
                'last_name': getattr(user, 'last_name', ''),
                'full_name': getattr(user, 'full_name', ''),
                'date_joined': user.date_joined,
                'last_login': user.last_login,
                'is_active': user.is_active,
                'subscription_status': active_sub.status if active_sub else 'none',
                'plan_name': active_sub.plan.name if active_sub else None
            })
        
        return Response({'results': user_data})


class AdminPlansListView(generics.ListAPIView):
    """
    Admin view of all subscription plans with stats
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # Check if user is admin/superuser
        if not (request.user.is_superuser or getattr(request.user, 'role', None) == 'admin'):
            return Response(
                {'error': 'Admin access required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        plans = SubscriptionPlan.objects.all()
        plan_data = []
        
        for plan in plans:
            subscriber_count = UserSubscription.objects.filter(
                plan=plan,
                status__in=['active', 'trial'],
                end_date__gte=timezone.now().date()
            ).count()
            
            services = list(plan.services.values_list('name', flat=True))
            
            plan_data.append({
                'id': plan.id,
                'name': plan.name,
                'price_monthly': float(plan.price_monthly),
                'currency': plan.currency,
                'is_active': plan.is_active,
                'subscriber_count': subscriber_count,
                'services': services,
                'description': plan.description
            })
        
        return Response(plan_data)


class AdminBillingHistoryView(generics.ListAPIView):
    """
    Admin view of all billing history
    """
    serializer_class = BillingHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Check if user is admin/superuser
        if not (self.request.user.is_superuser or getattr(self.request.user, 'role', None) == 'admin'):
            return BillingHistory.objects.none()
        
        queryset = BillingHistory.objects.all().select_related('user', 'user_subscription')
        
        days = self.request.query_params.get('days')
        if days:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=int(days))
            queryset = queryset.filter(date_created__gte=start_date)
        
        return queryset.order_by('-date_created')


class AdminUsageStatsView(views.APIView):
    """
    Admin view of service usage statistics
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # Check if user is admin/superuser
        if not (request.user.is_superuser or getattr(request.user, 'role', None) == 'admin'):
            return Response(
                {'error': 'Admin access required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        services = Service.objects.all()
        usage_data = []
        
        for service in services:
            total_usage = ServiceUsage.objects.filter(
                service=service,
                period_start_date__gte=start_date
            ).aggregate(total=models.Sum('usage_count'))['total'] or 0
            
            # Count limit breaches
            limit_breaches = 0
            if service.name == "Dr. Max AI Chatbot":
                limit_breaches = ServiceUsage.objects.filter(
                    service=service,
                    period_start_date__gte=start_date,
                    user_subscription__plan__limit_chatbot_messages__isnull=False,
                    usage_count__gt=models.F('user_subscription__plan__limit_chatbot_messages')
                ).count()
            elif service.name == "Intelligent MCQ Generator":
                limit_breaches = ServiceUsage.objects.filter(
                    service=service,
                    period_start_date__gte=start_date,
                    user_subscription__plan__limit_mcq_generations__isnull=False,
                    usage_count__gt=models.F('user_subscription__plan__limit_mcq_generations')
                ).count()
            # Add other services as needed
            
            usage_data.append({
                'service': service.name,
                'total_usage': total_usage,
                'limit_breaches': limit_breaches
            })
        
        return Response(usage_data)


class AdminRevenueDataView(views.APIView):
    """
    Admin view of revenue data over time
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # Check if user is admin/superuser
        if not (request.user.is_superuser or getattr(request.user, 'role', None) == 'admin'):
            return Response(
                {'error': 'Admin access required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        days = int(request.query_params.get('days', 365))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Group by month for the chart
        from django.db.models import Count
        from django.db.models.functions import TruncMonth
        
        revenue_by_month = BillingHistory.objects.filter(
            status='succeeded',
            date_paid__gte=start_date,
            date_paid__lte=end_date
        ).annotate(
            month=TruncMonth('date_paid')
        ).values('month').annotate(
            revenue=models.Sum('amount_paid'),
            subscriptions=Count('id')
        ).order_by('month')
        
        # Format for chart
        chart_data = []
        for item in revenue_by_month:
            chart_data.append({
                'month': item['month'].strftime('%b'),
                'revenue': float(item['revenue'] or 0),
                'subscriptions': item['subscriptions']
            })
        
        return Response(chart_data)


class AdminSubscriptionActionView(views.APIView):
    """
    Admin actions on subscriptions (cancel, update, etc.)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request, *args, **kwargs):
        # Check if user is admin/superuser
        if not (request.user.is_superuser or getattr(request.user, 'role', None) == 'admin'):
            return Response(
                {'error': 'Admin access required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        subscription_id = request.data.get('subscription_id')
        try:
            subscription = UserSubscription.objects.get(id=subscription_id)
        except UserSubscription.DoesNotExist:
            return Response(
                {'error': 'Subscription not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update subscription fields
        updates = request.data
        for field in ['status', 'auto_renew', 'end_date']:
            if field in updates:
                setattr(subscription, field, updates[field])
        
        subscription.save()
        return Response(UserSubscriptionSerializer(subscription).data)
    
    def post(self, request, *args, **kwargs):
        # Check if user is admin/superuser
        if not (request.user.is_superuser or getattr(request.user, 'role', None) == 'admin'):
            return Response(
                {'error': 'Admin access required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        action = request.data.get('action')
        
        # Handle subscription actions
        if action in ['cancel', 'reactivate', 'update']:
            subscription_id = request.data.get('subscription_id')
            try:
                subscription = UserSubscription.objects.get(id=subscription_id)
            except UserSubscription.DoesNotExist:
                return Response(
                    {'error': 'Subscription not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if action == 'cancel':
                subscription.status = 'cancelled'
                subscription.auto_renew = False
                subscription.save()
                return Response({'message': 'Subscription cancelled successfully'})
            
            elif action == 'reactivate':
                subscription.status = 'active'
                subscription.save()
                return Response({'message': 'Subscription reactivated successfully'})
                
            elif action == 'update':
                # Update subscription fields
                for field in ['status', 'auto_renew', 'end_date']:
                    if field in request.data:
                        setattr(subscription, field, request.data[field])
                subscription.save()
                return Response(UserSubscriptionSerializer(subscription).data)
        
        # Handle plan actions
        elif action == 'create_plan':
            # Create new plan
            plan_data = {
                'name': request.data.get('name'),
                'price_monthly': request.data.get('price_monthly'),
                'currency': request.data.get('currency', 'USD'),
                'is_active': request.data.get('is_active', True),
                'description': request.data.get('description', ''),
            }
            
            # Validate required fields
            if not plan_data['name'] or not plan_data['price_monthly']:
                return Response(
                    {'error': 'Plan name and price are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                plan = SubscriptionPlan.objects.create(**plan_data)
                
                # Handle services if provided
                services = request.data.get('services', [])
                if services:
                    # Create services for this plan (you may need to adjust based on your Service model)
                    for service_name in services:
                        if service_name.strip():
                            # This assumes you have a way to associate services with plans
                            # You may need to adjust this based on your actual model structure
                            pass
                
                return Response({
                    'message': 'Plan created successfully',
                    'plan_id': plan.id
                })
                
            except Exception as e:
                return Response(
                    {'error': f'Failed to create plan: {str(e)}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        elif action == 'update_plan':
            plan_id = request.data.get('plan_id')
            try:
                plan = SubscriptionPlan.objects.get(id=plan_id)
            except SubscriptionPlan.DoesNotExist:
                return Response(
                    {'error': 'Plan not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Update plan fields
            for field in ['name', 'price_monthly', 'currency', 'is_active', 'description']:
                if field in request.data:
                    setattr(plan, field, request.data[field])
            
            plan.save()
            return Response({'message': 'Plan updated successfully'})
        
        elif action == 'delete_plan':
            plan_id = request.data.get('plan_id')
            try:
                plan = SubscriptionPlan.objects.get(id=plan_id)
                
                # Check if any active subscriptions use this plan
                active_subscriptions = UserSubscription.objects.filter(
                    plan=plan, 
                    status__in=['active', 'trial']
                ).count()
                
                if active_subscriptions > 0:
                    return Response(
                        {'error': f'Cannot delete plan. {active_subscriptions} active subscriptions are using this plan.'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                plan.delete()
                return Response({'message': 'Plan deleted successfully'})
                
            except SubscriptionPlan.DoesNotExist:
                return Response(
                    {'error': 'Plan not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        else:
            return Response(
                {'error': 'Invalid action'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class AdminDashboardStatsView(views.APIView):
    """
    Comprehensive admin dashboard statistics with real-time data
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # Check if user is admin/superuser
        if not (request.user.is_superuser or getattr(request.user, 'role', None) == 'admin'):
            return Response(
                {'error': 'Admin access required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            from django.contrib.auth import get_user_model
            from django.db.models import Count, Sum, Q
            from django.utils import timezone
            from datetime import timedelta
            
            User = get_user_model()
            today = timezone.now().date()
            yesterday = today - timedelta(days=1)
            last_30_days = today - timedelta(days=30)
            
            # Total Users
            total_users = User.objects.count()
            
            # New users today
            new_users_today = User.objects.filter(
                date_joined__date=today
            ).count()
            
            # Active users (with active subscriptions)
            active_users = User.objects.filter(
                user_subscriptions__status__in=['active', 'trial'],
                user_subscriptions__end_date__gte=today
            ).distinct().count()
            
            # Total Revenue (from successful payments)
            total_revenue = BillingHistory.objects.filter(
                status='succeeded'
            ).aggregate(total=Sum('amount_paid'))['total'] or 0
            
            # Revenue this month
            revenue_this_month = BillingHistory.objects.filter(
                status='succeeded',
                date_paid__month=today.month,
                date_paid__year=today.year
            ).aggregate(total=Sum('amount_paid'))['total'] or 0
            
            # Revenue last month for growth calculation
            last_month = today.replace(day=1) - timedelta(days=1)
            revenue_last_month = BillingHistory.objects.filter(
                status='succeeded',
                date_paid__month=last_month.month,
                date_paid__year=last_month.year
            ).aggregate(total=Sum('amount_paid'))['total'] or 0
            
            # Revenue growth percentage
            revenue_growth = 0
            if revenue_last_month > 0:
                revenue_growth = ((revenue_this_month - revenue_last_month) / revenue_last_month) * 100
            
            # Active Subscriptions
            active_subscriptions = UserSubscription.objects.filter(
                status__in=['active', 'trial'],
                end_date__gte=today
            ).count()
            
            # New subscriptions today
            new_subscriptions_today = UserSubscription.objects.filter(
                start_date=today
            ).count()
            
            # Subscription plans distribution
            subscription_plans = UserSubscription.objects.filter(
                status__in=['active', 'trial'],
                end_date__gte=today
            ).values('plan__name').annotate(count=Count('id')).order_by('-count')
            
            # Churn rate (last 30 days)
            churned_subscriptions = UserSubscription.objects.filter(
                status__in=['cancelled', 'expired'],
                end_date__gte=last_30_days,
                end_date__lt=today
            ).count()
            
            churn_rate = 0
            if active_subscriptions > 0:
                churn_rate = (churned_subscriptions / (active_subscriptions + churned_subscriptions)) * 100
            
            # Recent Activity (last 10 activities)
            recent_registrations = User.objects.filter(
                date_joined__gte=last_30_days
            ).order_by('-date_joined')[:5]
            
            recent_subscriptions = UserSubscription.objects.filter(
                start_date__gte=last_30_days
            ).order_by('-start_date')[:5]
            
            recent_activity = []
            
            # Add recent registrations
            for user in recent_registrations:
                recent_activity.append({
                    'id': f'user_{user.id}',
                    'type': 'user_registration',
                    'message': f'New user registered: {user.email}',
                    'timestamp': user.date_joined.strftime('%Y-%m-%d %H:%M'),
                    'icon': 'ri-user-add-line'
                })
            
            # Add recent subscriptions
            for sub in recent_subscriptions:
                recent_activity.append({
                    'id': f'sub_{sub.id}',
                    'type': 'subscription',
                    'message': f'New subscription: {sub.plan.name} by {sub.user.email}',
                    'timestamp': sub.start_date.strftime('%Y-%m-%d'),
                    'icon': 'ri-vip-crown-line'
                })
            
            # Sort by timestamp
            recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
            recent_activity = recent_activity[:10]
            
            # System health metrics
            server_uptime = 99.8  # This would come from monitoring system
            database_health = 100.0  # This would come from database monitoring
            
            # Prepare response data
            dashboard_stats = {
                'totalUsers': total_users,
                'activeUsers': active_users,
                'newUsersToday': new_users_today,
                'totalRevenue': float(total_revenue),
                'revenueThisMonth': float(revenue_this_month),
                'revenueGrowth': round(revenue_growth, 1),
                'activeSubscriptions': active_subscriptions,
                'newSubscriptionsToday': new_subscriptions_today,
                'churnRate': round(churn_rate, 1),
                'serverUptime': server_uptime,
                'databaseHealth': database_health,
                'subscriptionPlans': list(subscription_plans),
                'recentActivity': recent_activity,
                'lastUpdated': timezone.now().isoformat()
            }
            
            return Response(dashboard_stats)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to load dashboard statistics: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
