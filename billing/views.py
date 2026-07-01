"""
Manual Billing Views

API endpoints for managing manual billing accounts, usage tracking,
and invoice generation for healthcare providers.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Sum, F
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from .models import (
    ManualBillingAccount, 
    ServicePricing, 
    UsageRecord, 
    Invoice, 
    BillingRequest
)
from .serializers import (
    ManualBillingAccountSerializer,
    ServicePricingSerializer,
    UsageRecordSerializer,
    InvoiceSerializer,
    BillingRequestSerializer
)

logger = logging.getLogger(__name__)


class BillingRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling billing setup requests
    """
    queryset = BillingRequest.objects.all()
    serializer_class = BillingRequestSerializer
    permission_classes = [AllowAny]  # Allow anyone to submit billing requests
    
    def create(self, request):
        """
        Submit a new manual billing request
        """
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                billing_request = serializer.save()
                
                # Log the request
                logger.info(f"New billing request submitted: {billing_request.doctor_name} - {billing_request.email}")
                
                # TODO: Send notification email to billing team
                # TODO: Send confirmation email to requester
                
                return Response({
                    'status': 'success',
                    'message': 'Your billing request has been submitted successfully. Our team will contact you within 24 hours.',
                    'request_id': billing_request.id
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'status': 'error',
                    'message': 'Please check your submission for errors.',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error creating billing request: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while processing your request. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ServicePricingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for retrieving service pricing information
    """
    queryset = ServicePricing.objects.filter(is_active=True)
    serializer_class = ServicePricingSerializer
    permission_classes = [AllowAny]  # Allow public access to pricing
    
    @action(detail=False, methods=['get'])
    def calculate_estimate(self, request):
        """
        Calculate cost estimate based on expected usage
        """
        try:
            # Expected usage format: {'service_type': quantity, ...}
            usage_data = request.query_params.get('usage', '{}')
            import json
            usage = json.loads(usage_data) if usage_data else {}
            
            estimate = []
            total_cost = 0
            
            for service_type, quantity in usage.items():
                try:
                    quantity = int(quantity)
                    pricing = ServicePricing.objects.get(service_type=service_type, is_active=True)
                    
                    cost = pricing.calculate_price(quantity)
                    total_cost += cost
                    
                    estimate.append({
                        'service': pricing.service_name,
                        'quantity': quantity,
                        'unit_price': float(pricing.base_price),
                        'total_cost': float(cost),
                        'unit_description': pricing.unit_description
                    })
                    
                except (ServicePricing.DoesNotExist, ValueError):
                    continue
            
            return Response({
                'status': 'success',
                'estimate': estimate,
                'total_monthly_cost': float(total_cost),
                'note': 'This is an estimate based on provided usage. Actual costs may vary based on volume discounts and specific usage patterns.'
            })
            
        except Exception as e:
            logger.error(f"Error calculating estimate: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Error calculating estimate'
            }, status=status.HTTP_400_BAD_REQUEST)


class ManualBillingAccountViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing manual billing accounts
    """
    queryset = ManualBillingAccount.objects.all()
    serializer_class = ManualBillingAccountSerializer
    permission_classes = [IsAuthenticated]  # Require authentication for account access
    
    def get_queryset(self):
        """
        Filter accounts based on user permissions
        """
        user = self.request.user
        if user.is_staff:
            return ManualBillingAccount.objects.all()
        else:
            # Regular users can only see their own accounts
            return ManualBillingAccount.objects.filter(email=user.email)
    
    @action(detail=True, methods=['get'])
    def usage_summary(self, request, pk=None):
        """
        Get usage summary for an account
        """
        try:
            account = self.get_object()
            
            # Get usage for current month
            current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = (current_month + timedelta(days=32)).replace(day=1)
            
            monthly_usage = UsageRecord.objects.filter(
                account=account,
                usage_date__gte=current_month,
                usage_date__lt=next_month
            ).values('service__service_name').annotate(
                total_quantity=Sum('quantity'),
                total_amount=Sum('total_amount')
            )
            
            # Get total unbilled usage
            unbilled_usage = UsageRecord.objects.filter(
                account=account,
                billed=False
            ).aggregate(
                total_amount=Sum('total_amount'),
                total_records=models.Count('id')
            )
            
            return Response({
                'status': 'success',
                'account_summary': {
                    'total_usage_amount': float(account.total_usage_amount),
                    'total_paid_amount': float(account.total_paid_amount),
                    'outstanding_balance': float(account.outstanding_balance),
                    'credit_limit': float(account.credit_limit)
                },
                'monthly_usage': list(monthly_usage),
                'unbilled_usage': {
                    'total_amount': float(unbilled_usage['total_amount'] or 0),
                    'total_records': unbilled_usage['total_records']
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting usage summary: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Error retrieving usage summary'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UsageRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing usage records
    """
    queryset = UsageRecord.objects.all()
    serializer_class = UsageRecordSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter usage records based on user permissions
        """
        user = self.request.user
        if user.is_staff:
            return UsageRecord.objects.all()
        else:
            # Regular users can only see their own usage
            return UsageRecord.objects.filter(account__email=user.email)
    
    def create(self, request):
        """
        Record new usage
        """
        try:
            # Auto-detect account from user email if not provided
            if 'account' not in request.data:
                try:
                    account = ManualBillingAccount.objects.get(email=request.user.email, status='active')
                    request.data['account'] = account.id
                except ManualBillingAccount.DoesNotExist:
                    return Response({
                        'status': 'error',
                        'message': 'No active billing account found for your email address.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                usage_record = serializer.save()
                
                # Update account total usage
                account = usage_record.account
                account.total_usage_amount = F('total_usage_amount') + usage_record.total_amount
                account.outstanding_balance = F('outstanding_balance') + usage_record.total_amount
                account.save()
                
                logger.info(f"Usage recorded: {usage_record}")
                
                return Response({
                    'status': 'success',
                    'message': 'Usage recorded successfully',
                    'usage_record': UsageRecordSerializer(usage_record).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'status': 'error',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error recording usage: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Error recording usage'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InvoiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing invoices
    """
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter invoices based on user permissions
        """
        user = self.request.user
        if user.is_staff:
            return Invoice.objects.all()
        else:
            # Regular users can only see their own invoices
            return Invoice.objects.filter(account__email=user.email)
    
    @action(detail=False, methods=['post'])
    def generate_invoice(self, request):
        """
        Generate invoice for unbilled usage
        """
        try:
            account_id = request.data.get('account_id')
            if not account_id:
                return Response({
                    'status': 'error',
                    'message': 'Account ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get account
            try:
                account = ManualBillingAccount.objects.get(id=account_id)
            except ManualBillingAccount.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Account not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check permissions
            if not request.user.is_staff and account.email != request.user.email:
                return Response({
                    'status': 'error',
                    'message': 'Permission denied'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get unbilled usage
            unbilled_usage = UsageRecord.objects.filter(account=account, billed=False)
            
            if not unbilled_usage.exists():
                return Response({
                    'status': 'error',
                    'message': 'No unbilled usage found'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Calculate invoice totals
            subtotal = unbilled_usage.aggregate(total=Sum('total_amount'))['total'] or 0
            
            # Create invoice
            invoice = Invoice.objects.create(
                account=account,
                period_start=unbilled_usage.earliest('usage_date').usage_date.date(),
                period_end=timezone.now().date(),
                subtotal=subtotal,
                total_amount=subtotal  # No tax for now
            )
            
            # Mark usage as billed
            unbilled_usage.update(billed=True, invoice=invoice)
            
            logger.info(f"Invoice generated: {invoice.invoice_number} for {account.doctor_name}")
            
            return Response({
                'status': 'success',
                'message': 'Invoice generated successfully',
                'invoice': InvoiceSerializer(invoice).data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error generating invoice: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Error generating invoice'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """
        Mark invoice as paid
        """
        try:
            invoice = self.get_object()
            
            if invoice.status == 'paid':
                return Response({
                    'status': 'error',
                    'message': 'Invoice is already marked as paid'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            payment_method = request.data.get('payment_method', '')
            payment_reference = request.data.get('payment_reference', '')
            
            invoice.mark_as_paid(payment_method, payment_reference)
            
            logger.info(f"Invoice marked as paid: {invoice.invoice_number}")
            
            return Response({
                'status': 'success',
                'message': 'Invoice marked as paid successfully',
                'invoice': InvoiceSerializer(invoice).data
            })
            
        except Exception as e:
            logger.error(f"Error marking invoice as paid: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Error processing payment'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
