from functools import wraps
from django.http import JsonResponse
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import UserSubscription, ServiceUsage, Service
from rest_framework.response import Response
from rest_framework import status


def require_subscription(required_plans=None, required_service=None):
    """
    Decorator to check if user has required subscription plan or service access
    
    Args:
        required_plans (list): List of plan names that allow access
        required_service (str): Service name that must be included in user's plan
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({
                    'error': 'Authentication required'
                }, status=401)
                
            try:
                # Get user's active subscription
                user_subscription = UserSubscription.objects.filter(
                    user=request.user,
                    status__in=['active', 'trial'],
                    end_date__gte=timezone.now().date()
                ).order_by('-start_date').first()
                
                if not user_subscription:
                    return JsonResponse({
                        'error': 'Active subscription required',
                        'message': 'This feature requires an active subscription.',
                        'subscription_url': '/subscription/'
                    }, status=402)
                
                # Check plan requirements
                if required_plans and user_subscription.plan.name not in required_plans:
                    return JsonResponse({
                        'error': 'Subscription plan insufficient',
                        'message': f'Your current plan "{user_subscription.plan.name}" does not include access to this feature.',
                        'current_plan': user_subscription.plan.name,
                        'required_plans': required_plans,
                        'subscription_url': '/subscription/'
                    }, status=403)
                
                # Check service requirements
                if required_service:
                    try:
                        service = Service.objects.get(name=required_service)
                        if service not in user_subscription.plan.services.all():
                            return JsonResponse({
                                'error': 'Service not included in plan',
                                'message': f'Your current plan does not include "{required_service}" service.',
                                'current_plan': user_subscription.plan.name,
                                'required_service': required_service,
                                'subscription_url': '/subscription/'
                            }, status=403)
                    except Service.DoesNotExist:
                        return JsonResponse({
                            'error': 'Service configuration error',
                            'message': 'Required service not found in system.'
                        }, status=500)
                
                # Add subscription context to request
                request.user_subscription = user_subscription
                
            except Exception as e:
                return JsonResponse({
                    'error': 'Subscription validation error',
                    'message': 'Unable to validate subscription status.'
                }, status=500)
                
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def track_usage(service_name, usage_count=1):
    """
    Decorator to track service usage and enforce limits
    
    Args:
        service_name (str): Name of the service being used
        usage_count (int): Number of usage units to record
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
                
            try:
                # Record usage and check limits
                usage = ServiceUsage.record_usage(
                    user=request.user,
                    service_name=service_name,
                    count=usage_count
                )
                
                # Add usage context to request
                if usage:
                    request.service_usage = usage
                    
            except ValidationError as e:
                return JsonResponse({
                    'error': 'Usage limit exceeded',
                    'message': str(e),
                    'service': service_name,
                    'subscription_url': '/subscription/'
                }, status=429)  # Too Many Requests
            except Exception as e:
                # Log error but don't block the request
                print(f"Usage tracking error for {service_name}: {e}")
                
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_active_subscription(view_func):
    """
    Simple decorator to require any active subscription
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'error': 'Authentication required'
            }, status=401)
            
        try:
            user_subscription = UserSubscription.objects.filter(
                user=request.user,
                status__in=['active', 'trial'],
                end_date__gte=timezone.now().date()
            ).exists()
            
            if not user_subscription:
                return JsonResponse({
                    'error': 'Active subscription required',
                    'message': 'This feature requires an active subscription.',
                    'subscription_url': '/subscription/'
                }, status=402)
                
        except Exception as e:
            return JsonResponse({
                'error': 'Subscription validation error',
                'message': 'Unable to validate subscription status.'
            }, status=500)
            
        return view_func(request, *args, **kwargs)
    return wrapper


# DRF-specific decorators for class-based views
def subscription_required(required_plans=None, required_service=None):
    """
    DRF-compatible decorator for class-based views
    """
    def decorator(view_class):
        original_dispatch = view_class.dispatch
        
        @wraps(original_dispatch)
        def dispatch_with_subscription_check(self, request, *args, **kwargs):
            if not request.user.is_authenticated:
                return Response({
                    'error': 'Authentication required'
                }, status=status.HTTP_401_UNAUTHORIZED)
                
            try:
                user_subscription = UserSubscription.objects.filter(
                    user=request.user,
                    status__in=['active', 'trial'],
                    end_date__gte=timezone.now().date()
                ).order_by('-start_date').first()
                
                if not user_subscription:
                    return Response({
                        'error': 'Active subscription required',
                        'message': 'This feature requires an active subscription.',
                        'subscription_url': '/subscription/'
                    }, status=status.HTTP_402_PAYMENT_REQUIRED)
                
                if required_plans and user_subscription.plan.name not in required_plans:
                    return Response({
                        'error': 'Subscription plan insufficient',
                        'message': f'Your current plan "{user_subscription.plan.name}" does not include access to this feature.',
                        'current_plan': user_subscription.plan.name,
                        'required_plans': required_plans,
                        'subscription_url': '/subscription/'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                if required_service:
                    try:
                        service = Service.objects.get(name=required_service)
                        if service not in user_subscription.plan.services.all():
                            return Response({
                                'error': 'Service not included in plan',
                                'message': f'Your current plan does not include "{required_service}" service.',
                                'current_plan': user_subscription.plan.name,
                                'required_service': required_service,
                                'subscription_url': '/subscription/'
                            }, status=status.HTTP_403_FORBIDDEN)
                    except Service.DoesNotExist:
                        return Response({
                            'error': 'Service configuration error',
                            'message': 'Required service not found in system.'
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                request.user_subscription = user_subscription
                
            except Exception as e:
                return Response({
                    'error': 'Subscription validation error',
                    'message': 'Unable to validate subscription status.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            return original_dispatch(self, request, *args, **kwargs)
            
        view_class.dispatch = dispatch_with_subscription_check
        return view_class
    return decorator