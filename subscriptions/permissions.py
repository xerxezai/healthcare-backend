# backend/subscriptions/permissions.py
from rest_framework import permissions
from django.contrib.auth import get_user_model
from .utils import SubscriptionChecker

User = get_user_model()

class SuperAdminPermission(permissions.BasePermission):
    """
    Custom permission to grant full access to super administrators
    """
    
    def has_permission(self, request, view):
        """
        Super admins get full read/write access to everything
        """
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Check if user is super admin
        return SubscriptionChecker.is_super_admin(request.user)

class SuperAdminOrOwnerPermission(permissions.BasePermission):
    """
    Custom permission that allows super admins to access everything,
    but limits regular users to their own objects
    """
    
    def has_permission(self, request, view):
        """
        Allow access if user is authenticated
        """
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Super admins can access any object, others only their own
        """
        # Super admins get full access
        if SubscriptionChecker.is_super_admin(request.user):
            return True
            
        # Regular users can only access their own objects
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'patient') and hasattr(obj.patient, 'user'):
            return obj.patient.user == request.user
        elif hasattr(obj, 'doctor') and hasattr(obj.doctor, 'user'):
            return obj.doctor.user == request.user
        
        # Default: allow access
        return True

class SubscriptionOrSuperAdminPermission(permissions.BasePermission):
    """
    Custom permission that checks subscription requirements unless user is super admin
    """
    
    def __init__(self, required_service=None):
        self.required_service = required_service
    
    def has_permission(self, request, view):
        """
        Check if user has subscription or is super admin
        """
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Super admins bypass subscription requirements
        if SubscriptionChecker.is_super_admin(request.user):
            return True
            
        # Check subscription if service is specified
        if self.required_service:
            return SubscriptionChecker.has_access_to_service(request.user, self.required_service)
            
        # Default: allow access for authenticated users
        return True

class ReadWritePermission(permissions.BasePermission):
    """
    Permission that grants full read/write access to super admins
    and read-only to others
    """
    
    def has_permission(self, request, view):
        """
        Allow authenticated users to read, super admins to write
        """
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Super admins get full read/write access
        if SubscriptionChecker.is_super_admin(request.user):
            return True
            
        # Others get read-only access
        return request.method in permissions.SAFE_METHODS

class AdminManagementPermission(permissions.BasePermission):
    """
    Permission for admin management features
    """
    
    def has_permission(self, request, view):
        """
        Only super admins can access admin management
        """
        if not request.user or not request.user.is_authenticated:
            return False
            
        return SubscriptionChecker.is_super_admin(request.user)

class DynamicServicePermission(permissions.BasePermission):
    """
    Dynamic permission that checks service access based on view configuration
    """
    
    def has_permission(self, request, view):
        """
        Check service permission based on view's service_name attribute
        """
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Super admins bypass all checks
        if SubscriptionChecker.is_super_admin(request.user):
            return True
            
        # Check if view specifies a required service
        service_name = getattr(view, 'required_service', None)
        if service_name:
            return SubscriptionChecker.has_access_to_service(request.user, service_name)
            
        # Default: allow access
        return True

# Convenience functions for common permission combinations
def get_super_admin_permission():
    """Get super admin only permission"""
    return [SuperAdminPermission]

def get_subscription_permission(service_name):
    """Get subscription or super admin permission for specific service"""
    class ServicePermission(SubscriptionOrSuperAdminPermission):
        def __init__(self):
            super().__init__(required_service=service_name)
    
    return [ServicePermission]

def get_read_write_permission():
    """Get read/write permission (super admin write, others read)"""
    return [ReadWritePermission]

def get_admin_management_permission():
    """Get admin management permission (super admin only)"""
    return [AdminManagementPermission]
