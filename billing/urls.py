"""
Manual Billing URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BillingRequestViewSet,
    ServicePricingViewSet,
    ManualBillingAccountViewSet,
    UsageRecordViewSet,
    InvoiceViewSet
)

# Create router for API endpoints
router = DefaultRouter()
router.register(r'requests', BillingRequestViewSet, basename='billing-requests')
router.register(r'pricing', ServicePricingViewSet, basename='service-pricing')
router.register(r'accounts', ManualBillingAccountViewSet, basename='billing-accounts')
router.register(r'usage', UsageRecordViewSet, basename='usage-records')
router.register(r'invoices', InvoiceViewSet, basename='invoices')

app_name = 'billing'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Additional custom endpoints can be added here
]
