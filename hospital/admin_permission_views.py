"""
Admin Permission Management Views
API endpoints for super admin to manage individual admin permissions
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import transaction
from hospital.models import AdminPermissions, AdminDashboardFeatures
import json
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

def require_super_admin(view_func):
    """Decorator to ensure only super admins can access these views"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
        
        if request.user.role != 'super_admin' and not request.user.is_superuser:
            return JsonResponse({'success': False, 'error': 'Super admin access required'}, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper

@csrf_exempt
@require_http_methods(["GET"])
@login_required
@require_super_admin
def get_admin_permissions(request, admin_id):
    """Get permissions and dashboard features for a specific admin"""
    try:
        admin_user = User.objects.get(id=admin_id, role='admin')
        
        # Get or create admin permissions
        admin_permissions, created = AdminPermissions.objects.get_or_create(
            user=admin_user,
            defaults={
                'can_manage_users': True,
                'can_view_reports': True,
                'can_manage_departments': True,
                'can_access_billing': False,
                'can_manage_inventory': False,
                'can_access_emergency': False,
            }
        )
        
        # Get or create dashboard features
        dashboard_features, created = AdminDashboardFeatures.objects.get_or_create(
            user=admin_user,
            defaults={
                'user_management': True,
                'patient_management': True,
                'doctor_management': False,
                'nurse_management': False,
                'pharmacist_management': False,
                'medicine_module': False,
                'dentistry_module': False,
                'dermatology_module': False,
                'pathology_module': False,
                'radiology_module': False,
                'subscription_management': False,
                'billing_reports': False,
                'financial_dashboard': False,
                'system_settings': False,
                'audit_logs': False,
                'user_analytics': True,
                'medical_reports': False,
                'revenue_reports': False,
                'appointment_analytics': False,
                'inventory_reports': False,
                'create_user': True,
                'schedule_appointment': False,
                'generate_report': True,
                'backup_system': False,
                'send_notifications': False,
            }
        )
        
        # Convert to dictionary format
        permissions_data = {
            'can_manage_users': admin_permissions.can_manage_users,
            'can_view_reports': admin_permissions.can_view_reports,
            'can_manage_departments': admin_permissions.can_manage_departments,
            'can_access_billing': admin_permissions.can_access_billing,
            'can_manage_inventory': admin_permissions.can_manage_inventory,
            'can_access_emergency': admin_permissions.can_access_emergency,
        }
        
        features_data = {
            'user_management': dashboard_features.user_management,
            'patient_management': dashboard_features.patient_management,
            'doctor_management': dashboard_features.doctor_management,
            'nurse_management': dashboard_features.nurse_management,
            'pharmacist_management': dashboard_features.pharmacist_management,
            'medicine_module': dashboard_features.medicine_module,
            'dentistry_module': dashboard_features.dentistry_module,
            'dermatology_module': dashboard_features.dermatology_module,
            'pathology_module': dashboard_features.pathology_module,
            'radiology_module': dashboard_features.radiology_module,
            'homeopathy_module': dashboard_features.homeopathy_module,
            'allopathy_module': dashboard_features.allopathy_module,
            'dna_sequencing_module': dashboard_features.dna_sequencing_module,
            'secureneat_module': dashboard_features.secureneat_module,
            'subscription_management': dashboard_features.subscription_management,
            'billing_reports': dashboard_features.billing_reports,
            'financial_dashboard': dashboard_features.financial_dashboard,
            'system_settings': dashboard_features.system_settings,
            'audit_logs': dashboard_features.audit_logs,
            'user_analytics': dashboard_features.user_analytics,
            'medical_reports': dashboard_features.medical_reports,
            'revenue_reports': dashboard_features.revenue_reports,
            'appointment_analytics': dashboard_features.appointment_analytics,
            'inventory_reports': dashboard_features.inventory_reports,
            'create_user': dashboard_features.create_user,
            'schedule_appointment': dashboard_features.schedule_appointment,
            'generate_report': dashboard_features.generate_report,
            'backup_system': dashboard_features.backup_system,
            'send_notifications': dashboard_features.send_notifications,
        }
        
        return JsonResponse({
            'success': True,
            'permissions': permissions_data,
            'dashboard_features': features_data,
            'admin_info': {
                'id': admin_user.id,
                'email': admin_user.email,
                'full_name': admin_user.full_name,
                'is_active': admin_user.is_active,
            }
        })
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Admin user not found'}, status=404)
    except Exception as e:
        logger.error(f"Error getting admin permissions: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
@login_required
@require_super_admin
def update_admin_permissions(request, admin_id):
    """Update permissions and dashboard features for a specific admin"""
    try:
        with transaction.atomic():
            admin_user = User.objects.get(id=admin_id, role='admin')
            
            # Parse request data
            data = json.loads(request.body)
            permissions_data = data.get('permissions', {})
            features_data = data.get('dashboard_features', {})
            
            # Update AdminPermissions
            admin_permissions, created = AdminPermissions.objects.get_or_create(user=admin_user)
            
            # Update each permission field
            admin_permissions.can_manage_users = permissions_data.get('can_manage_users', True)
            admin_permissions.can_view_reports = permissions_data.get('can_view_reports', True)
            admin_permissions.can_manage_departments = permissions_data.get('can_manage_departments', True)
            admin_permissions.can_access_billing = permissions_data.get('can_access_billing', False)
            admin_permissions.can_manage_inventory = permissions_data.get('can_manage_inventory', False)
            admin_permissions.can_access_emergency = permissions_data.get('can_access_emergency', False)
            admin_permissions.save()
            
            # Update AdminDashboardFeatures
            dashboard_features, created = AdminDashboardFeatures.objects.get_or_create(user=admin_user)
            
            # Update each feature field
            dashboard_features.user_management = features_data.get('user_management', True)
            dashboard_features.patient_management = features_data.get('patient_management', True)
            dashboard_features.doctor_management = features_data.get('doctor_management', False)
            dashboard_features.nurse_management = features_data.get('nurse_management', False)
            dashboard_features.pharmacist_management = features_data.get('pharmacist_management', False)
            dashboard_features.medicine_module = features_data.get('medicine_module', False)
            dashboard_features.dentistry_module = features_data.get('dentistry_module', False)
            dashboard_features.dermatology_module = features_data.get('dermatology_module', False)
            dashboard_features.pathology_module = features_data.get('pathology_module', False)
            dashboard_features.radiology_module = features_data.get('radiology_module', False)
            dashboard_features.subscription_management = features_data.get('subscription_management', False)
            dashboard_features.billing_reports = features_data.get('billing_reports', False)
            dashboard_features.financial_dashboard = features_data.get('financial_dashboard', False)
            dashboard_features.system_settings = features_data.get('system_settings', False)
            dashboard_features.audit_logs = features_data.get('audit_logs', False)
            dashboard_features.user_analytics = features_data.get('user_analytics', True)
            dashboard_features.medical_reports = features_data.get('medical_reports', False)
            dashboard_features.revenue_reports = features_data.get('revenue_reports', False)
            dashboard_features.appointment_analytics = features_data.get('appointment_analytics', False)
            dashboard_features.inventory_reports = features_data.get('inventory_reports', False)
            dashboard_features.create_user = features_data.get('create_user', True)
            dashboard_features.schedule_appointment = features_data.get('schedule_appointment', False)
            dashboard_features.generate_report = features_data.get('generate_report', True)
            dashboard_features.backup_system = features_data.get('backup_system', False)
            dashboard_features.send_notifications = features_data.get('send_notifications', False)
            dashboard_features.save()
            
            logger.info(f"Super admin {request.user.email} updated permissions for admin {admin_user.email}")
            
            return JsonResponse({
                'success': True,
                'message': f'Permissions updated successfully for {admin_user.full_name}',
                'updated_permissions': permissions_data,
                'updated_features': features_data
            })
            
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Admin user not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error updating admin permissions: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@login_required
@require_super_admin
def list_admin_users(request):
    """Get list of all admin users with their current permission status"""
    try:
        # Get all admin users
        admin_users = User.objects.filter(role='admin').select_related(
            'admin_permissions', 'dashboard_features'
        )
        
        admin_list = []
        for admin in admin_users:
            # Get permission info
            admin_permissions = getattr(admin, 'admin_permissions', None)
            dashboard_features = getattr(admin, 'dashboard_features', None)
            
            admin_data = {
                'id': admin.id,
                'email': admin.email,
                'full_name': admin.full_name,
                'phone_number': admin.phone_number,
                'is_active': admin.is_active,
                'date_joined': admin.date_joined.isoformat() if admin.date_joined else None,
                'admin_permissions': {
                    'can_manage_users': admin_permissions.can_manage_users if admin_permissions else True,
                    'can_view_reports': admin_permissions.can_view_reports if admin_permissions else True,
                    'can_manage_departments': admin_permissions.can_manage_departments if admin_permissions else True,
                    'can_access_billing': admin_permissions.can_access_billing if admin_permissions else False,
                    'can_manage_inventory': admin_permissions.can_manage_inventory if admin_permissions else False,
                    'can_access_emergency': admin_permissions.can_access_emergency if admin_permissions else False,
                    'updated_at': admin_permissions.updated_at.isoformat() if admin_permissions else None,
                } if admin_permissions else None,
                'dashboard_features': {
                    'user_management': dashboard_features.user_management if dashboard_features else True,
                    'patient_management': dashboard_features.patient_management if dashboard_features else True,
                    'subscription_management': dashboard_features.subscription_management if dashboard_features else False,
                    'system_settings': dashboard_features.system_settings if dashboard_features else False,
                    'updated_at': dashboard_features.updated_at.isoformat() if dashboard_features else None,
                } if dashboard_features else None,
            }
            admin_list.append(admin_data)
        
        return JsonResponse({
            'success': True,
            'users': admin_list,
            'total_count': len(admin_list)
        })
        
    except Exception as e:
        logger.error(f"Error listing admin users: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
@require_super_admin
def reset_admin_permissions(request, admin_id):
    """Reset admin permissions to default values"""
    try:
        with transaction.atomic():
            admin_user = User.objects.get(id=admin_id, role='admin')
            
            # Reset to default permissions
            admin_permissions, created = AdminPermissions.objects.get_or_create(user=admin_user)
            admin_permissions.can_manage_users = True
            admin_permissions.can_view_reports = True
            admin_permissions.can_manage_departments = True
            admin_permissions.can_access_billing = False
            admin_permissions.can_manage_inventory = False
            admin_permissions.can_access_emergency = False
            admin_permissions.save()
            
            # Reset to default dashboard features
            dashboard_features, created = AdminDashboardFeatures.objects.get_or_create(user=admin_user)
            dashboard_features.user_management = True
            dashboard_features.patient_management = True
            dashboard_features.doctor_management = False
            dashboard_features.nurse_management = False
            dashboard_features.pharmacist_management = False
            dashboard_features.medicine_module = False
            dashboard_features.dentistry_module = False
            dashboard_features.dermatology_module = False
            dashboard_features.pathology_module = False
            dashboard_features.radiology_module = False
            dashboard_features.subscription_management = False
            dashboard_features.billing_reports = False
            dashboard_features.financial_dashboard = False
            dashboard_features.system_settings = False
            dashboard_features.audit_logs = False
            dashboard_features.user_analytics = True
            dashboard_features.medical_reports = False
            dashboard_features.revenue_reports = False
            dashboard_features.appointment_analytics = False
            dashboard_features.inventory_reports = False
            dashboard_features.create_user = True
            dashboard_features.schedule_appointment = False
            dashboard_features.generate_report = True
            dashboard_features.backup_system = False
            dashboard_features.send_notifications = False
            dashboard_features.save()
            
            logger.info(f"Super admin {request.user.email} reset permissions for admin {admin_user.email}")
            
            return JsonResponse({
                'success': True,
                'message': f'Permissions reset to defaults for {admin_user.full_name}'
            })
            
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Admin user not found'}, status=404)
    except Exception as e:
        logger.error(f"Error resetting admin permissions: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
