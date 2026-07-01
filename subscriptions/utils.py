from django.utils import timezone
from .models import UserSubscription, Service, ServiceUsage


class SubscriptionChecker:
    """
    Utility class for checking subscription status and usage limits
    """
    
    @staticmethod
    def is_super_admin(user):
        """
        Check if user is a super administrator with full access
        """
        return (getattr(user, 'is_superuser', False) or 
                getattr(user, 'role', None) == 'super_admin' or
                getattr(user, 'role', None) == 'admin')
    
    @staticmethod
    def get_user_active_subscription(user):
        """
        Get the user's active subscription
        Super admins get virtual unlimited subscription
        """
        # Super admins bypass subscription requirements
        if SubscriptionChecker.is_super_admin(user):
            return 'SUPER_ADMIN_ACCESS'
            
        try:
            return UserSubscription.objects.filter(
                user=user,
                status__in=['active', 'trial'],
                end_date__gte=timezone.now().date()
            ).order_by('-start_date').first()
        except Exception:
            return None
    
    @staticmethod
    def has_access_to_service(user, service_name):
        """
        Check if user has access to a specific service
        Super admins have access to all services
        """
        # Super admins have access to all services
        if SubscriptionChecker.is_super_admin(user):
            return True
            
        subscription = SubscriptionChecker.get_user_active_subscription(user)
        if not subscription:
            return False
            
        try:
            service = Service.objects.get(name=service_name)
            return service in subscription.plan.services.all()
        except Service.DoesNotExist:
            return False
    
    @staticmethod
    def check_usage_limit(user, service_name):
        """
        Check if user has exceeded usage limits for a service
        Super admins have unlimited usage
        Returns: (within_limit: bool, usage_data: dict)
        """
        # Super admins have unlimited usage
        if SubscriptionChecker.is_super_admin(user):
            return True, {
                'unlimited': True,
                'super_admin_access': True,
                'current_usage': 0,
                'limit': 'Unlimited',
                'remaining': 'Unlimited',
                'percentage_used': 0
            }
            
        subscription = SubscriptionChecker.get_user_active_subscription(user)
        if not subscription:
            return False, {'error': 'No active subscription'}
            
        try:
            service = Service.objects.get(name=service_name)
            if not service.is_metered:
                return True, {'unlimited': True}
                
            # Get current usage
            current_usage = ServiceUsage.objects.filter(
                user_subscription=subscription,
                service=service,
                period_start_date=subscription.start_date
            ).first()
            
            usage_count = current_usage.usage_count if current_usage else 0
            
            # Get limit from subscription plan
            limit = None
            if service_name == "Dr. Max AI Chatbot":
                limit = subscription.plan.limit_chatbot_messages
            elif service_name == "Intelligent MCQ Generator":
                limit = subscription.plan.limit_mcq_generations
            elif service_name == "Radiology Report Analysis":
                limit = subscription.plan.limit_report_analyses
            elif service_name == "Data Anonymization Tool":
                limit = subscription.plan.limit_document_anonymizations
                
            if limit is None:
                return True, {'unlimited': True}
                
            within_limit = usage_count < limit
            
            return within_limit, {
                'current_usage': usage_count,
                'limit': limit,
                'remaining': max(0, limit - usage_count),
                'percentage_used': (usage_count / limit) * 100 if limit > 0 else 0
            }
            
        except Service.DoesNotExist:
            return False, {'error': 'Service not found'}
        except Exception as e:
            return False, {'error': str(e)}
    
    @staticmethod
    def get_subscription_info(user):
        """
        Get comprehensive subscription information for a user
        Super admins get virtual unlimited subscription info
        """
        # Super admins get virtual unlimited subscription
        if SubscriptionChecker.is_super_admin(user):
            return {
                'has_subscription': True,
                'subscription': {
                    'id': 'SUPER_ADMIN',
                    'plan_name': 'Super Administrator - Unlimited Access',
                    'status': 'active',
                    'start_date': timezone.now().date(),
                    'end_date': None,  # No expiration
                    'days_remaining': 'Unlimited',
                    'auto_renew': False,
                    'is_trial': False,
                    'super_admin_access': True
                },
                'services': [
                    {'name': 'All Services', 'description': 'Complete access to all system features', 'is_metered': False}
                ],
                'usage': {
                    'unlimited_access': {
                        'within_limit': True,
                        'unlimited': True,
                        'super_admin_access': True
                    }
                }
            }
            
        subscription = SubscriptionChecker.get_user_active_subscription(user)
        if not subscription:
            return {
                'has_subscription': False,
                'subscription': None,
                'services': [],
                'usage': {}
            }
            
        # Get all services in the plan
        services = list(subscription.plan.services.values('name', 'description', 'is_metered'))
        
        # Get usage information for metered services
        usage_info = {}
        for service in services:
            if service['is_metered']:
                within_limit, usage_data = SubscriptionChecker.check_usage_limit(
                    user, service['name']
                )
                usage_info[service['name']] = {
                    'within_limit': within_limit,
                    **usage_data
                }
        
        days_remaining = (subscription.end_date - timezone.now().date()).days
        
        return {
            'has_subscription': True,
            'subscription': {
                'id': subscription.id,
                'plan_name': subscription.plan.name,
                'status': subscription.status,
                'start_date': subscription.start_date,
                'end_date': subscription.end_date,
                'days_remaining': max(0, days_remaining),
                'auto_renew': subscription.auto_renew,
                'is_trial': subscription.status == 'trial'
            },
            'services': services,
            'usage': usage_info
        }
    
    @staticmethod
    def can_access_feature(user, feature_path):
        """
        Check if user can access a specific feature based on path
        Super admins can access all features
        """
        # Super admins can access all features
        if SubscriptionChecker.is_super_admin(user):
            return True, "Super Administrator - Full Access Granted"
            
        subscription = SubscriptionChecker.get_user_active_subscription(user)
        if not subscription:
            return False, "No active subscription"
            
        # Define feature to plan mapping
        feature_requirements = {
            'secureneat': ['SecureNeat', 'Full Admin Access'],
            'radiology': ['Radiology', 'Full Admin Access'],
            'chatbot': ['SecureNeat', 'Full Admin Access'],
            'mcq': ['SecureNeat', 'Full Admin Access'],
            'osce': ['SecureNeat', 'Full Admin Access'],
        }
        
        for feature, required_plans in feature_requirements.items():
            if feature in feature_path.lower():
                if subscription.plan.name not in required_plans:
                    return False, f"Feature requires one of: {', '.join(required_plans)}"
                return True, "Access granted"
                
        return True, "No specific requirements"  # Default allow for unspecified features