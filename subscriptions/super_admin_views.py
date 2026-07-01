# backend/subscriptions/views.py - Add this new view

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .utils import SubscriptionChecker
from .permissions import SuperAdminPermission

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def super_admin_access_check(request):
    """
    Comprehensive access check for super admin
    """
    user = request.user
    
    # Check if user is super admin
    is_super_admin = SubscriptionChecker.is_super_admin(user)
    
    # Get comprehensive subscription info (super admin gets virtual unlimited)
    subscription_info = SubscriptionChecker.get_subscription_info(user)
    
    # Define all available features and their access status
    features = {
        'user_management': {
            'name': 'User Management',
            'access': is_super_admin,
            'permissions': ['read', 'write', 'delete'] if is_super_admin else []
        },
        'subscription_management': {
            'name': 'Subscription Management', 
            'access': is_super_admin,
            'permissions': ['read', 'write', 'delete'] if is_super_admin else []
        },
        'medical_records': {
            'name': 'Medical Records Access',
            'access': is_super_admin,
            'permissions': ['read', 'write', 'delete'] if is_super_admin else []
        },
        'system_settings': {
            'name': 'System Configuration',
            'access': is_super_admin,
            'permissions': ['read', 'write'] if is_super_admin else []
        },
        'analytics_reports': {
            'name': 'Analytics & Reports',
            'access': is_super_admin,
            'permissions': ['read', 'write', 'export'] if is_super_admin else []
        },
        'api_access': {
            'name': 'Full API Access',
            'access': is_super_admin,
            'permissions': ['unlimited'] if is_super_admin else []
        },
        'security_management': {
            'name': 'Security Management',
            'access': is_super_admin,
            'permissions': ['read', 'write', 'admin'] if is_super_admin else []
        },
        'backup_recovery': {
            'name': 'Backup & Recovery',
            'access': is_super_admin,
            'permissions': ['read', 'write', 'execute'] if is_super_admin else []
        }
    }
    
    # Check specific service access
    services = [
        'Dr. Max AI Chatbot',
        'Intelligent MCQ Generator', 
        'Radiology Report Analysis',
        'Data Anonymization Tool'
    ]
    
    service_access = {}
    for service in services:
        has_access = SubscriptionChecker.has_access_to_service(user, service)
        within_limit, usage_data = SubscriptionChecker.check_usage_limit(user, service)
        
        service_access[service] = {
            'has_access': has_access,
            'within_limit': within_limit,
            'usage_data': usage_data
        }
    
    return Response({
        'user_info': {
            'email': user.email,
            'role': getattr(user, 'role', None),
            'is_superuser': getattr(user, 'is_superuser', False),
            'is_staff': getattr(user, 'is_staff', False),
            'is_super_admin': is_super_admin
        },
        'access_summary': {
            'full_access': is_super_admin,
            'subscription_bypass': is_super_admin,
            'unlimited_usage': is_super_admin,
            'admin_privileges': is_super_admin
        },
        'subscription_info': subscription_info,
        'feature_access': features,
        'service_access': service_access,
        'permissions_summary': {
            'total_features_accessible': sum(1 for f in features.values() if f['access']),
            'total_services_accessible': sum(1 for s in service_access.values() if s['has_access']),
            'permission_level': 'Super Administrator' if is_super_admin else 'Regular User'
        }
    })

@api_view(['POST'])
@permission_classes([SuperAdminPermission])
def test_super_admin_write(request):
    """
    Test endpoint for super admin write operations
    """
    return Response({
        'message': 'Super Admin write access confirmed',
        'user': request.user.email,
        'operation': 'write_test_successful',
        'timestamp': timezone.now().isoformat(),
        'permissions': 'full_access_granted'
    })
