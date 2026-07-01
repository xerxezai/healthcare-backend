"""
User Management URLs
Routes for comprehensive user management system
"""
from django.urls import path
from . import user_management_views
from . import admin_permission_views

urlpatterns = [
    
    # User listing and search
    path('users/', user_management_views.list_users, name='list_users'),
    
    # User CRUD operations
    path('users/create/', user_management_views.create_user, name='create_user'),
    path('users/create-admin/', user_management_views.create_admin_user, name='create_admin_user'),
    path('users/<int:user_id>/', user_management_views.get_user_details, name='get_user_details'),
    path('users/<int:user_id>/update/', user_management_views.update_user, name='update_user'),
    path('users/<int:user_id>/delete/', user_management_views.delete_user, name='delete_user'),
    path('users/verify/<int:user_id>/', user_management_views.verify_user_exists, name='verify_user_exists'),
    
    # Statistics and management
    path('users/stats/', user_management_views.get_user_management_stats, name='user_management_stats'),
    
    # Feature management
    path('features/', user_management_views.get_available_features, name='get_available_features'),
    path('users/<int:user_id>/features/', user_management_views.get_user_features, name='get_user_features'),
    path('users/<int:user_id>/features/update/', user_management_views.update_user_features, name='update_user_features'),
    
    # Current user permissions and features
    path('me/permissions/', user_management_views.get_current_user_permissions, name='get_current_user_permissions'),
    
    # Admin Permission Management (Super Admin Only)
    path('admin-users/', admin_permission_views.list_admin_users, name='list_admin_users'),
    path('users/<int:admin_id>/permissions/', admin_permission_views.get_admin_permissions, name='get_admin_permissions'),
    path('users/<int:admin_id>/permissions/', admin_permission_views.update_admin_permissions, name='update_admin_permissions'),
    path('users/<int:admin_id>/permissions/reset/', admin_permission_views.reset_admin_permissions, name='reset_admin_permissions'),
]
