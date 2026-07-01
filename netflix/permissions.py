# Netflix app permissions
from rest_framework import permissions
from django.contrib.auth import get_user_model
from .models import UserRoleAssignment

User = get_user_model()


class NetflixPermissionMixin:
    """
    Mixin for Netflix-specific permission checking based on enhanced roles
    """
    required_scope = None  # Tuple: (scope, action) e.g., ('content', 'read')
    required_scope_write = None  # For write operations
    required_scope_delete = None  # For delete operations
    
    def check_permissions(self, request):
        """Check if user has required permissions"""
        super().check_permissions(request)
        
        if not request.user.is_authenticated:
            return
        
        # Super admin bypass
        if request.user.is_superuser:
            return
        
        # Determine required scope based on HTTP method
        required_scope = self.get_required_scope(request.method)
        
        if required_scope and not self.has_netflix_permission(request.user, required_scope):
            self.permission_denied(
                request,
                message=f"Netflix permission required: {required_scope[0]}.{required_scope[1]}"
            )
    
    def get_required_scope(self, method):
        """Get the required scope based on HTTP method"""
        if method in ['POST'] and self.required_scope_write:
            return self.required_scope_write
        elif method in ['DELETE'] and self.required_scope_delete:
            return self.required_scope_delete
        elif method in ['PUT', 'PATCH'] and self.required_scope_write:
            return self.required_scope_write
        else:
            return self.required_scope
    
    def has_netflix_permission(self, user, required_scope):
        """Check if user has the required Netflix permission"""
        if not required_scope:
            return True
        
        scope, action = required_scope
        
        # Check user's role assignments
        assignments = UserRoleAssignment.objects.filter(
            user=user,
            is_active=True
        ).select_related('role')
        
        for assignment in assignments:
            role = assignment.role
            if scope in role.scopes:
                allowed_actions = role.scopes[scope]
                if action in allowed_actions or 'all' in allowed_actions:
                    return True
        
        return False


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Permission to only allow owners of an object or staff to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only to the owner or staff
        if hasattr(obj, 'user'):
            return obj.user == request.user or request.user.is_staff
        elif hasattr(obj, 'profile'):
            return obj.profile.user == request.user or request.user.is_staff
        
        return request.user.is_staff


class IsStaffOrOwner(permissions.BasePermission):
    """
    Permission for staff or resource owner
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        
        # Check if user owns the resource
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'profile') and hasattr(obj.profile, 'user'):
            return obj.profile.user == request.user
        
        return False


class DeviceOwnerPermission(permissions.BasePermission):
    """
    Permission to only allow device owners to manage their devices
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_staff


class ProfileOwnerPermission(permissions.BasePermission):
    """
    Permission to only allow profile owners to manage their profiles
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_staff


class EntitlementsPermission(permissions.BasePermission):
    """
    Permission for managing user entitlements
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Staff can manage all entitlements
        if request.user.is_staff:
            return True
        
        # Users can only view their own entitlements
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        
        # Users can only view their own entitlements
        if request.method in permissions.SAFE_METHODS:
            return obj.user == request.user
        
        return False
