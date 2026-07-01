# backend/subscriptions/urls.py
from django.urls import path
from .views import (
    SubscriptionPlanListView, UserSubscriptionDetailView, ServiceListView,
    UsageStatsView, BillingHistoryListView, 
    PaymentMethodListView, CreatePaymentMethodView, PaymentMethodDetailView, SetDefaultPaymentMethodView,
    ChangePlanView, CancelSubscriptionView,
    RazorpayCreatePaymentLinkView, RazorpayPaymentSuccessView, RazorpayWebhookView, RazorpayCreateCustomerView,
    create_razorpay_order, verify_payment, create_user_from_payment,
    # Admin views
    AdminOverviewView, AdminSubscriptionsListView, AdminUsersListView, 
    AdminPlansListView, AdminBillingHistoryView, AdminUsageStatsView,
    AdminRevenueDataView, AdminSubscriptionActionView, AdminDashboardStatsView
)
from .super_admin_views import super_admin_access_check, test_super_admin_write

app_name = 'subscriptions'

urlpatterns = [
    path('services/', ServiceListView.as_view(), name='service-list'),
    path('plans/', SubscriptionPlanListView.as_view(), name='plan-list'),
    path('my-subscription/', UserSubscriptionDetailView.as_view(), name='user-subscription-detail'),

    path('usage-stats/', UsageStatsView.as_view(), name='usage-stats'),
    path('billing-history/', BillingHistoryListView.as_view(), name='billing-history-list'),
    
    path('payment-methods/', PaymentMethodListView.as_view(), name='payment-method-list'),
    path('payment-methods/create/', CreatePaymentMethodView.as_view(), name='payment-method-create'),
    path('payment-methods/<int:pk>/', PaymentMethodDetailView.as_view(), name='payment-method-detail-delete'),
    path('payment-methods/<int:pk>/set-default/', SetDefaultPaymentMethodView.as_view(), name='payment-method-set-default'),
    
    path('change-plan/', ChangePlanView.as_view(), name='change-plan'),
    path('cancel-subscription/', CancelSubscriptionView.as_view(), name='cancel-subscription'),
    
    # Razorpay integration endpoints
    path('razorpay/create-payment-link/', RazorpayCreatePaymentLinkView.as_view(), name='razorpay-create-payment-link'),
    path('razorpay/create-order/', create_razorpay_order, name='razorpay-create-order'),
    path('razorpay/verify-payment/', verify_payment, name='razorpay-verify-payment'),
    path('razorpay/payment-success/', RazorpayPaymentSuccessView.as_view(), name='razorpay-payment-success'),
    path('razorpay/webhook/', RazorpayWebhookView.as_view(), name='razorpay-webhook'),
    path('razorpay/create-customer/', RazorpayCreateCustomerView.as_view(), name='razorpay-create-customer'),
    
    # Auto-create user from payment (CRITICAL FIX)
    path('create-user-from-payment/', create_user_from_payment, name='create-user-from-payment'),
    
    # Admin endpoints
    path('admin/overview/', AdminOverviewView.as_view(), name='admin-overview'),
    path('admin/dashboard-stats/', AdminDashboardStatsView.as_view(), name='admin-dashboard-stats'),
    path('admin/subscriptions/', AdminSubscriptionsListView.as_view(), name='admin-subscriptions'),
    path('admin/users/', AdminUsersListView.as_view(), name='admin-users'),
    path('admin/plans/', AdminPlansListView.as_view(), name='admin-plans'),
    path('admin/billing/', AdminBillingHistoryView.as_view(), name='admin-billing'),
    path('admin/usage-stats/', AdminUsageStatsView.as_view(), name='admin-usage-stats'),
    path('admin/revenue/', AdminRevenueDataView.as_view(), name='admin-revenue'),
    path('admin/subscription-action/', AdminSubscriptionActionView.as_view(), name='admin-subscription-action'),
    
    # Super Admin Access Endpoints
    path('super-admin/access-check/', super_admin_access_check, name='super-admin-access-check'),
    path('super-admin/test-write/', test_super_admin_write, name='super-admin-test-write'),
]