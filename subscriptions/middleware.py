from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from .models import UserSubscription, Service
import re
from django.utils import timezone


class SubscriptionMiddleware(MiddlewareMixin):
    """
    Middleware to check subscription requirements for protected endpoints
    """
    
    # Define protected paths and their required subscription plans
    PROTECTED_PATHS = {
        r'^/api/secureneat/': ['SecureNeat Basic', 'SecureNeat Pro'],
        r'^/api/radiology/': ['Radiology Suite Standard'],
        r'^/api/chatbot/': ['SecureNeat Basic', 'SecureNeat Pro'],
    }
    
    # Paths that are exempt from subscription checks
    EXEMPT_PATHS = [
        r'^/api/auth/',
        r'^/api/subscriptions/',
        r'^/admin/',
        r'^/static/',
        r'^/media/',
    ]
    
    def process_request(self, request):
        # Skip subscription checks in debug mode for development
        if settings.DEBUG and request.GET.get('skip_subscription_check') == 'true':
            return None
            
        # Skip for non-API requests
        if not request.path.startswith('/api/'):
            return None
            
        # Check if path is exempt
        for exempt_pattern in self.EXEMPT_PATHS:
            if re.match(exempt_pattern, request.path):
                return None
                
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return None  # Let authentication middleware handle this
        
        # Bypass subscription check for superusers, admin role, or super_admin role
        if (getattr(request.user, 'is_superuser', False) or 
            getattr(request.user, 'role', None) == 'admin' or 
            getattr(request.user, 'role', None) == 'super_admin'):
            return None
            
        # Check if path requires subscription
        required_plans = None
        for path_pattern, plans in self.PROTECTED_PATHS.items():
            if re.match(path_pattern, request.path):
                required_plans = plans
                break
                
        if not required_plans:
            return None  # No subscription required for this path
            
        # Check user's subscription
        try:
            user_subscription = UserSubscription.objects.filter(
                user=request.user,
                status__in=['active', 'trial'],
                end_date__gte=timezone.now().date()
            ).order_by('-start_date').first()
            
            if not user_subscription:
                return JsonResponse({
                    'error': 'Active subscription required',
                    'message': f'This feature requires an active subscription to one of: {", ".join(required_plans)}',
                    'required_plans': required_plans,
                    'subscription_url': '/subscription/'
                }, status=402)
                
            if user_subscription.plan.name not in required_plans:
                return JsonResponse({
                    'error': 'Subscription plan insufficient',
                    'message': f'Your current plan "{user_subscription.plan.name}" does not include access to this feature. Required plans: {", ".join(required_plans)}',
                    'current_plan': user_subscription.plan.name,
                    'required_plans': required_plans,
                    'subscription_url': '/subscription/'
                }, status=403)
                
        except Exception as e:
            # Log the error but don't block the request
            print(f"Subscription middleware error: {e}")
            
        return None