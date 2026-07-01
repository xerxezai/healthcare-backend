"""
User Management Views for Super Admin
Provides comprehensive user management functionality
"""
import json
import logging
import boto3
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, Permission
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime, timedelta
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import CustomUser as User, StaffProfile, PatientProfile, AdminPermissions, AdminDashboardFeatures, UserCreationQuota
from .password_manager import PasswordManager, AdminPasswordManager
from .password_config import DEPLOYMENT_CONFIG, get_policy_for_user_type, should_force_password_change

logger = logging.getLogger(__name__)

def send_admin_account_email(admin_user, temp_password, created_by_user, extra_context=None):
    """Send admin account creation email directly using AWS SES with enhanced context"""
    try:
        # Initialize AWS SES client
        ses_client = boto3.client(
            'ses',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_SES_REGION
        )
        
        # Base context for the email template
        context = {
            'admin_name': admin_user.full_name,
            'admin_email': admin_user.email,
            'temp_password': temp_password,  # This is guaranteed to be the actual password
            'department': getattr(admin_user, 'department', 'Administration'),
            'creation_date': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'created_by': created_by_user.full_name if hasattr(created_by_user, 'full_name') else created_by_user.email,
            'platform_name': DEPLOYMENT_CONFIG['platform_name'],
            'support_email': DEPLOYMENT_CONFIG['support_email'],
            'login_url': DEPLOYMENT_CONFIG['login_url'],
            'dashboard_url': DEPLOYMENT_CONFIG['dashboard_url'],
            'frontend_url': DEPLOYMENT_CONFIG['frontend_url'],
            'first_login_required': should_force_password_change(admin_user.role)
        }
        
        # Add extra context if provided (password strength, auto-generation info, etc.)
        if extra_context:
            context.update(extra_context)
        
        # Add password security information to context
        if 'password_strength' in context:
            strength_info = context['password_strength']
            context.update({
                'password_strength_score': strength_info.get('score', 0),
                'password_strength_level': strength_info.get('strength', 'Unknown'),
                'password_feedback': strength_info.get('feedback', [])
            })
        
        # Render the email template with enhanced context
        html_content = render_to_string('notifications/email/admin_account_created.html', context)
        
        # Send email via AWS SES
        response = ses_client.send_email(
            Source=settings.AWS_SES_FROM_EMAIL,
            Destination={'ToAddresses': [admin_user.email]},
            Message={
                'Subject': {'Data': f"🎉 Admin Account Created - Welcome to {context['platform_name']}", 'Charset': 'UTF-8'},
                'Body': {'Html': {'Data': html_content, 'Charset': 'UTF-8'}}
            }
        )
        
        auto_gen_msg = " (auto-generated)" if extra_context and extra_context.get('auto_generated') else " (manual)"
        logger.info(f"Admin account creation email sent to {admin_user.email}{auto_gen_msg}, Message ID: {response['MessageId']}")
        return {'success': True, 'message_id': response['MessageId']}
        
    except Exception as e:
        logger.error(f"Failed to send admin account creation email to {admin_user.email}: {e}")
        return {'success': False, 'error': str(e)}


def jwt_required(view_func):
    """Decorator to require JWT authentication"""
    def wrapper(request, *args, **kwargs):
        jwt_authenticator = JWTAuthentication()
        try:
            # Try to authenticate using JWT
            auth_result = jwt_authenticator.authenticate(request)
            if auth_result is not None:
                user, token = auth_result
                request.user = user
            # If no JWT provided, we'll check session auth below
        except AuthenticationFailed:
            # If JWT is present but invalid/expired, try session fallback
            try:
                if getattr(request, 'user', None) and request.user.is_authenticated:
                    pass  # session-authenticated user
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid or expired token'
                    }, status=401)
            except Exception:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid or expired token'
                }, status=401)
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Authentication failed'
            }, status=401)
        
        # Fall back to session authentication if no valid JWT and user is not authenticated
        if not getattr(request, 'user', None) or not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required'
            }, status=401)
        
        return view_func(request, *args, **kwargs)
    return wrapper


def require_super_admin_session(view_func):
    """Decorator to require super admin access with session support"""
    def wrapper(request, *args, **kwargs):
        # Check if user is authenticated via session
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required'
            }, status=401)
            
        # Allow both super_admin role and Django superusers
        if request.user.role != 'super_admin' and not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'error': 'Super admin access required',
                'debug_info': {
                    'user_role': request.user.role,
                    'is_superuser': request.user.is_superuser,
                    'user_email': request.user.email
                }
            }, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper


def require_super_admin(view_func):
    """Decorator to require super admin access with JWT or session support"""
    def wrapper(request, *args, **kwargs):
        # Try JWT authentication first
        jwt_authenticator = JWTAuthentication()
        jwt_user = None
        try:
            auth_result = jwt_authenticator.authenticate(request)
            if auth_result is not None:
                jwt_user, token = auth_result
                request.user = jwt_user
        except AuthenticationFailed:
            # JWT failed, continue to check session auth
            pass
        except Exception as e:
            logger.error(f"JWT Authentication error: {str(e)}")
        
        # Check if user is authenticated (either via JWT or session)
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required'
            }, status=401)
        
        # Check if user is super admin
        if request.user.role != 'super_admin':
            return JsonResponse({
                'success': False,
                'error': 'Super admin access required',
                'debug_info': {
                    'user_role': getattr(request.user, 'role', None),
                    'is_superuser': getattr(request.user, 'is_superuser', False),
                    'user_email': getattr(request.user, 'email', None),
                    'authenticated': request.user.is_authenticated
                }
            }, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper


def require_admin_or_super_admin_session(view_func):
    """Decorator to require admin or super admin access with session support"""
    def wrapper(request, *args, **kwargs):
        # Check if user is authenticated via session
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required'
            }, status=401)
            
        if request.user.role not in ['admin', 'super_admin']:
            return JsonResponse({
                'success': False,
                'error': 'Admin access required'
            }, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper


def require_admin_or_super_admin(view_func):
    """Decorator to require admin or super admin access with JWT support"""
    @jwt_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in ['admin', 'super_admin']:
            return JsonResponse({
                'success': False,
                'error': 'Admin access required'
            }, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper


@csrf_exempt
@require_super_admin
@require_http_methods(["GET"])
def list_users(request):
    """List all users with pagination and filtering"""
    try:
        # Get query parameters
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        search = request.GET.get('search', '')
        role_filter = request.GET.get('role', '')
        status_filter = request.GET.get('status', '')
        sort_by = request.GET.get('sort_by', '-date_joined')
        
        # Build query
        queryset = User.objects.all()
        
        # Apply search filter
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(full_name__icontains=search) |
                Q(username__icontains=search)
            )
        
        # Apply role filter
        if role_filter:
            queryset = queryset.filter(role=role_filter)
        
        # Apply status filter
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        elif status_filter == 'verified':
            queryset = queryset.filter(is_verified=True)
        elif status_filter == 'unverified':
            queryset = queryset.filter(is_verified=False)
        
        # Apply sorting
        valid_sort_fields = ['email', 'full_name', 'role', 'date_joined', 'is_active']
        if sort_by.lstrip('-') in valid_sort_fields:
            queryset = queryset.order_by(sort_by)
        else:
            queryset = queryset.order_by('-date_joined')
        
        # Pagination
        paginator = Paginator(queryset, limit)
        page_obj = paginator.get_page(page)
        
        # Serialize users
        users_data = []
        for user in page_obj:
            # Get profile data
            profile_data = {}
            if hasattr(user, 'staffprofile'):
                profile = user.staffprofile
                profile_data = {
                    'department': profile.department,
                    'position': profile.position,
                    'join_date': profile.join_date.isoformat() if profile.join_date else None,
                    'salary': str(profile.salary) if profile.salary else None
                }
            elif hasattr(user, 'patientprofile'):
                profile = user.patientprofile
                profile_data = {
                    'date_of_birth': profile.date_of_birth.isoformat() if profile.date_of_birth else None,
                    'gender': profile.gender,
                    'emergency_contact': profile.emergency_contact,
                    'insurance_info': profile.insurance_info
                }
            
            users_data.append({
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'full_name': user.full_name,
                'role': user.role,
                'phone_number': user.phone_number,
                'license_number': user.license_number,
                'certification': user.certification,
                'specialization': user.specialization,
                'is_active': user.is_active,
                'is_verified': user.is_verified,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'date_joined': user.date_joined.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'profile': profile_data
            })
        
        # Get role statistics
        role_stats = User.objects.values('role').annotate(count=Count('id'))
        
        return JsonResponse({
            'success': True,
            'users': users_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'page_size': limit
            },
            'statistics': {
                'total_users': User.objects.count(),
                'active_users': User.objects.filter(is_active=True).count(),
                'verified_users': User.objects.filter(is_verified=True).count(),
                'role_distribution': list(role_stats)
            }
        })
        
    except Exception as e:
        logger.error(f"List users error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to fetch users'
        }, status=500)


@csrf_exempt
@require_super_admin
@require_http_methods(["POST"])
def create_admin_user(request):
    """Create a new admin user with secure password management (super admin only)"""
    try:
        data = json.loads(request.body)
        
        # Required fields for admin user
        required_fields = ['email', 'full_name']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'{field} is required'
                }, status=400)
        
        email = data.get('email')
        full_name = data.get('full_name')
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'error': 'User with this email already exists'
            }, status=400)
        
        # Handle password generation based on soft-coded policy
        password_mode = data.get('password_mode', 'auto')  # 'auto' or 'manual'
        
        if password_mode == 'auto' or not data.get('password'):
            # Auto-generate secure password using password manager
            password_result = AdminPasswordManager.create_admin_with_secure_password(
                user_data=data,
                user_type='admin'
            )
            password = password_result['generated_password']
            password_strength = password_result['password_strength']
            auto_generated = True
            
            logger.info(f"Auto-generated password for {email} - Strength: {password_strength['strength']} ({password_strength['score']}/100)")
        else:
            # Use provided password but validate it
            password = data.get('password')
            password_strength = PasswordManager.get_password_strength_score(password)
            auto_generated = False
            
            # Validate password meets policy requirements
            if not PasswordManager.validate_password_requirements(password):
                return JsonResponse({
                    'success': False,
                    'error': 'Password does not meet security requirements',
                    'password_feedback': password_strength['feedback']
                }, status=400)
            
            logger.info(f"Manual password provided for {email} - Strength: {password_strength['strength']} ({password_strength['score']}/100)")
        
        # Create admin user with the determined password
        admin_user = User.objects.create_user(
            email=email,
            password=password,  # This is now guaranteed to be the correct password
            full_name=full_name,
            role='admin',
            phone_number=data.get('phone_number', ''),
            license_number=data.get('license_number', ''),
            certification=data.get('certification', ''),
            specialization=data.get('specialization', ''),
            is_verified=True,
            is_staff=True,  # Admin users are staff
            is_active=True
        )
        
        # Apply password policy for first login (soft-coded)
        from .password_config import PASSWORD_POLICY
        admin_config = PASSWORD_POLICY.get('user_type_configs', {}).get('admin', {})
        
        if admin_config.get('force_change', True):
            admin_user.require_password_change(expires_in_hours=24)
            admin_user.save()
            logger.info(f"Password change required for new admin: {admin_user.email}")
        else:
            # Mark first login as completed if no change required
            admin_user.first_login_completed = True
            admin_user.save()
        
        # Create staff profile for admin
        StaffProfile.objects.create(
            user=admin_user,
            department=data.get('department', 'Administration'),
            position=data.get('position', 'Administrator'),
            join_date=timezone.now().date(),
            phone_number=admin_user.phone_number
        )
        
        # Create admin permissions - PURE SOFT CODING: Only enable what's explicitly requested
        permissions_data = data.get('permissions', {})
        AdminPermissions.objects.create(
            user=admin_user,
            can_manage_users=permissions_data.get('can_manage_users', False),
            can_view_reports=permissions_data.get('can_view_reports', False),
            can_manage_departments=permissions_data.get('can_manage_departments', False),
            can_access_billing=permissions_data.get('can_access_billing', False),
            can_manage_inventory=permissions_data.get('can_manage_inventory', False),
            can_access_emergency=permissions_data.get('can_access_emergency', False)
        )
        
        # Create dashboard features - PURE SOFT CODING: Only enable what's explicitly requested
        features_data = data.get('dashboard_features', {})
        AdminDashboardFeatures.objects.create(
            user=admin_user,
            # ALL features default to FALSE - only enable if explicitly requested
            user_management=features_data.get('user_management', False),
            patient_management=features_data.get('patient_management', False),
            doctor_management=features_data.get('doctor_management', False),
            nurse_management=features_data.get('nurse_management', False),
            pharmacist_management=features_data.get('pharmacist_management', False),
            # Healthcare Management Features
            hospital_management=features_data.get('hospital_management', False),
            clinic_management=features_data.get('clinic_management', False),
            all_doctors=features_data.get('all_doctors', False),
            add_doctors=features_data.get('add_doctors', False),
            doctor_profile=features_data.get('doctor_profile', False),
            # Medical Modules
            medicine_module=features_data.get('medicine_module', False),
            dentistry_module=features_data.get('dentistry_module', False),
            dermatology_module=features_data.get('dermatology_module', False),
            pathology_module=features_data.get('pathology_module', False),
            radiology_module=features_data.get('radiology_module', False),
            homeopathy_module=features_data.get('homeopathy_module', False),
            allopathy_module=features_data.get('allopathy_module', False),
            cosmetology_module=features_data.get('cosmetology_module', False),
            dna_sequencing_module=features_data.get('dna_sequencing_module', False),
            secureneat_module=features_data.get('secureneat_module', False),
            # Administrative Features
            subscription_management=features_data.get('subscription_management', False),
            billing_reports=features_data.get('billing_reports', False),
            financial_dashboard=features_data.get('financial_dashboard', False),
            system_settings=features_data.get('system_settings', False),
            audit_logs=features_data.get('audit_logs', False),
            # Analytics Features
            user_analytics=features_data.get('user_analytics', False),
            medical_reports=features_data.get('medical_reports', False),
            revenue_reports=features_data.get('revenue_reports', False),
            appointment_analytics=features_data.get('appointment_analytics', False),
            inventory_reports=features_data.get('inventory_reports', False),
            # Action Features
            create_user=features_data.get('create_user', False),
            schedule_appointment=features_data.get('schedule_appointment', False),
            generate_report=features_data.get('generate_report', False),
            backup_system=features_data.get('backup_system', False),
            send_notifications=features_data.get('send_notifications', False)
        )
        
        # Create user creation quota
        quota_data = data.get('user_creation_quota', {})
        if quota_data:
            current_usage = quota_data.get('current_usage', {})
            UserCreationQuota.objects.create(
                user=admin_user,
                enabled=quota_data.get('enabled', True),
                max_total_users=quota_data.get('max_total_users', 50),
                max_doctors=quota_data.get('max_doctors', 10),
                max_nurses=quota_data.get('max_nurses', 15),
                max_patients=quota_data.get('max_patients', 20),
                max_pharmacists=quota_data.get('max_pharmacists', 5),
                quota_reset_period=quota_data.get('quota_reset_period', 'monthly'),
                current_total_users=current_usage.get('total_users', 0),
                current_doctors=current_usage.get('doctors', 0),
                current_nurses=current_usage.get('nurses', 0),
                current_patients=current_usage.get('patients', 0),
                current_pharmacists=current_usage.get('pharmacists', 0)
            )
        
        # Add to Admin group with permissions
        admin_group, created = Group.objects.get_or_create(name='Administrators')
        
        # Grant admin permissions (exclude super admin permissions)
        admin_permissions = Permission.objects.filter(
            content_type__app_label__in=['hospital', 'dentistry', 'medicine', 'pathology']
        ).exclude(
            codename__in=['add_customuser', 'change_customuser', 'delete_customuser']  # No user management for admins
        )
        
        admin_group.permissions.set(admin_permissions)
        admin_user.groups.add(admin_group)
        
        logger.info(f"New admin user created by {request.user.email}: {admin_user.email}")
        
        # Send email notification with guaranteed correct password
        try:
            # Prepare email context with password information
            email_context = {
                'password': password,  # This is guaranteed to be the actual password
                'auto_generated': auto_generated,
                'password_strength': password_strength,
                'login_url': f"{request.build_absolute_uri('/')[:-1]}/login"
            }
            
            email_result = send_admin_account_email(
                admin_user=admin_user,
                temp_password=password,  # Guaranteed to match database
                created_by_user=request.user,
                extra_context=email_context
            )
            
            if email_result.get('success'):
                logger.info(f"Admin account creation email sent to {admin_user.email} - Auto-generated: {auto_generated}")
            else:
                logger.warning(f"Failed to send admin account email to {admin_user.email}: {email_result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error sending admin account creation email: {e}")
            # Don't fail the entire request if email fails
        
        return JsonResponse({
            'success': True,
            'message': 'Admin user created successfully',
            'user': {
                'id': admin_user.id,
                'email': admin_user.email,
                'full_name': admin_user.full_name,
                'role': admin_user.role,
                'is_active': admin_user.is_active,
                'is_verified': admin_user.is_verified,
                'date_joined': admin_user.date_joined.isoformat()
            },
            'password_info': {
                'auto_generated': auto_generated,
                'strength': password_strength['strength'],
                'score': password_strength['score'],
                'email_sent': email_result.get('success', False) if 'email_result' in locals() else False
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Create admin user error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to create admin user'
        }, status=500)


@csrf_exempt
@require_admin_or_super_admin_session  
@require_http_methods(["GET"])
def verify_user_exists(request, user_id):
    """Verify if a user exists in the database"""
    try:
        user_exists = User.objects.filter(id=user_id).exists()
        
        if user_exists:
            user = User.objects.get(id=user_id)
            return JsonResponse({
                'success': True,
                'exists': True,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role,
                    'is_active': user.is_active,
                    'is_verified': user.is_verified,
                    'date_joined': user.date_joined.isoformat()
                }
            })
        else:
            return JsonResponse({
                'success': True,
                'exists': False,
                'message': f'User with ID {user_id} not found'
            })
            
    except Exception as e:
        logger.error(f"User verification error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to verify user existence'
        }, status=500)


@csrf_exempt
@require_admin_or_super_admin_session
@require_http_methods(["POST"])
def create_user(request):
    """Create a new user with secure password management (admin and super admin)"""
    try:
        data = json.loads(request.body)
        
        # Required fields
        required_fields = ['email', 'full_name', 'role']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'{field} is required'
                }, status=400)
        
        email = data.get('email')
        full_name = data.get('full_name')
        role = data.get('role')
        
        # Validate role permissions
        if role in ['admin', 'super_admin'] and request.user.role != 'super_admin':
            return JsonResponse({
                'success': False,
                'error': 'Only super administrators can create admin users'
            }, status=403)
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'error': 'User with this email already exists'
            }, status=400)
        
        # Validate role
        valid_roles = [choice[0] for choice in User.ROLE_CHOICES]
        if role not in valid_roles:
            return JsonResponse({
                'success': False,
                'error': f'Invalid role. Must be one of: {", ".join(valid_roles)}'
            }, status=400)
        
        # Handle password generation based on soft-coded policy
        password_mode = data.get('password_mode', 'auto')  # 'auto' or 'manual'
        
        if password_mode == 'auto' or not data.get('password'):
            # Auto-generate secure password using password manager
            password = PasswordManager.generate_secure_password(role)
            password_strength = PasswordManager.get_password_strength_score(password)
            auto_generated = True
            
            logger.info(f"Auto-generated password for {email} ({role}) - Strength: {password_strength['strength']} ({password_strength['score']}/100)")
        else:
            # Use provided password but validate it
            password = data.get('password')
            password_strength = PasswordManager.get_password_strength_score(password)
            auto_generated = False
            
            # Validate password meets policy requirements
            if not PasswordManager.validate_password_requirements(password):
                return JsonResponse({
                    'success': False,
                    'error': 'Password does not meet security requirements',
                    'password_feedback': password_strength['feedback']
                }, status=400)
            
            logger.info(f"Manual password provided for {email} ({role}) - Strength: {password_strength['strength']} ({password_strength['score']}/100)")
        
        # Create user with the determined password
        new_user = User.objects.create_user(
            email=email,
            password=password,  # This is now guaranteed to be correct
            full_name=full_name,
            role=role,
            phone_number=data.get('phone_number', ''),
            license_number=data.get('license_number', ''),
            certification=data.get('certification', ''),
            specialization=data.get('specialization', ''),
            is_verified=data.get('is_verified', True),
            is_active=data.get('is_active', True)
        )
        
        # Apply password policy based on user role (soft-coded)
        from .password_config import PASSWORD_POLICY
        role_config = PASSWORD_POLICY.get('user_type_configs', {}).get(role, {})
        
        if role_config.get('force_change', False):
            new_user.require_password_change(expires_in_hours=24)
            new_user.save()
            logger.info(f"Password change required for new {role}: {new_user.email}")
        else:
            # Mark first login as completed if no change required
            new_user.first_login_completed = True
            new_user.save()
        
        # Handle feature selection
        selected_features = data.get('selected_features', [])
        if selected_features:
            # Create UserFeatureProfile
            from .models import UserFeatureProfile, FeatureAccess
            
            UserFeatureProfile.objects.create(
                user=new_user,
                selected_features=selected_features
            )
            
            # Create FeatureAccess entries for selected features
            for feature in selected_features:
                FeatureAccess.objects.create(
                    user=new_user,
                    feature=feature,
                    is_enabled=True
                )
        else:
            # If no features selected, create default feature access based on role
            from .models import FeatureAccess
            
            default_features = []
            if role in ['doctor', 'nurse']:
                default_features = ['medicine', 'patients', 'appointments']
            elif role == 'admin':
                default_features = ['hospital', 'patients', 'appointments', 'reports']
            elif role == 'super_admin':
                # Super admin gets access to all features
                default_features = [choice[0] for choice in FeatureAccess.FEATURE_CHOICES]
            elif role == 'patient':
                default_features = ['appointments', 'reports']
            elif role == 'pharmacist':
                default_features = ['pharmacy', 'patients']
            
            for feature in default_features:
                FeatureAccess.objects.create(
                    user=new_user,
                    feature=feature,
                    is_enabled=True
                )
        
        # Create appropriate profile
        if role in ['admin', 'doctor', 'nurse', 'pharmacist']:
            StaffProfile.objects.create(
                user=new_user,
                department=data.get('department', ''),
                position=data.get('position', role.title()),
                join_date=timezone.now().date(),
                phone_number=new_user.phone_number,
                salary=data.get('salary', None)
            )
        elif role == 'patient':
            PatientProfile.objects.create(
                user=new_user,
                date_of_birth=data.get('date_of_birth', None),
                gender=data.get('gender', ''),
                emergency_contact=data.get('emergency_contact', ''),
                insurance_info=data.get('insurance_info', '')
            )
        
        # Assign appropriate permissions
        if role == 'admin':
            new_user.is_staff = True
            new_user.save()
            
            admin_group, _ = Group.objects.get_or_create(name='Administrators')
            new_user.groups.add(admin_group)
        
        logger.info(f"New {role} user created by {request.user.email}: {new_user.email}")
        
        # Send email notification for admin account creation with enhanced context
        if role == 'admin':
            try:
                # Prepare email context with password information
                email_context = {
                    'password': password,  # Guaranteed to be the actual password
                    'auto_generated': auto_generated,
                    'password_strength': password_strength,
                    'login_url': f"{request.build_absolute_uri('/')[:-1]}/login"
                }
                
                email_result = send_admin_account_email(
                    admin_user=new_user,
                    temp_password=password,  # Guaranteed to match database
                    created_by_user=request.user,
                    extra_context=email_context
                )
                
                if email_result.get('success'):
                    logger.info(f"Admin account creation email sent to {new_user.email} - Auto-generated: {auto_generated}")
                else:
                    logger.warning(f"Failed to send admin account email to {new_user.email}: {email_result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Error sending admin account creation email: {e}")
                # Don't fail the entire request if email fails
        
        return JsonResponse({
            'success': True,
            'message': f'{role.title()} user created successfully',
            'user': {
                'id': new_user.id,
                'email': new_user.email,
                'full_name': new_user.full_name,
                'role': new_user.role,
                'is_active': new_user.is_active,
                'is_verified': new_user.is_verified,
                'date_joined': new_user.date_joined.isoformat()
            },
            'password_info': {
                'auto_generated': auto_generated,
                'strength': password_strength['strength'],
                'score': password_strength['score'],
                'email_sent': email_result.get('success', False) if 'email_result' in locals() else False
            } if role == 'admin' else None
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Create user error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to create user'
        }, status=500)


@csrf_exempt
@require_admin_or_super_admin_session
@require_http_methods(["PUT", "PATCH"])
def update_user(request, user_id):
    """Update an existing user"""
    print(f"🔍 UPDATE_USER DEBUG - Method: {request.method}, User: {request.user}, Authenticated: {request.user.is_authenticated}")
    try:
        data = json.loads(request.body)
        
        # Get user to update
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=404)
        
        # Permission check - only super admin can update admin/super admin users
        if user.role in ['admin', 'super_admin'] and request.user.role != 'super_admin':
            return JsonResponse({
                'success': False,
                'error': 'Only super administrators can update admin users'
            }, status=403)
        
        # Update user fields
        updatable_fields = ['full_name', 'phone_number', 'license_number', 
                           'certification', 'specialization', 'is_active', 'is_verified']
        
        for field in updatable_fields:
            if field in data:
                setattr(user, field, data[field])
        
        # Role change (super admin only)
        if 'role' in data and request.user.role == 'super_admin':
            new_role = data['role']
            valid_roles = [choice[0] for choice in User.ROLE_CHOICES]
            if new_role in valid_roles:
                user.role = new_role
                
                # Update staff status for admin roles
                if new_role == 'admin':
                    user.is_staff = True
                elif new_role not in ['admin', 'super_admin']:
                    user.is_staff = False
        
        # Update password if provided
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        user.save()
        
        # Update profile if needed
        profile_data = data.get('profile', {})
        if profile_data:
            if hasattr(user, 'staffprofile'):
                profile = user.staffprofile
                for field in ['department', 'position', 'salary']:
                    if field in profile_data:
                        setattr(profile, field, profile_data[field])
                profile.save()
            elif hasattr(user, 'patientprofile'):
                profile = user.patientprofile
                for field in ['date_of_birth', 'gender', 'emergency_contact', 'insurance_info']:
                    if field in profile_data:
                        setattr(profile, field, profile_data[field])
                profile.save()
        
        logger.info(f"User {user.email} updated by {request.user.email}")
        
        return JsonResponse({
            'success': True,
            'message': 'User updated successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'is_active': user.is_active,
                'is_verified': user.is_verified
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Update user error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to update user'
        }, status=500)


@require_super_admin
@csrf_exempt
@require_http_methods(["DELETE"])
def delete_user(request, user_id):
    """Delete a user (super admin only)"""
    try:
        # Get user to delete
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=404)
        
        # Prevent deleting the current super admin
        if user.id == request.user.id:
            return JsonResponse({
                'success': False,
                'error': 'Cannot delete your own account'
            }, status=400)
        
        # Prevent deleting the only super admin
        if user.role == 'super_admin':
            super_admin_count = User.objects.filter(role='super_admin').count()
            if super_admin_count <= 1:
                return JsonResponse({
                    'success': False,
                    'error': 'Cannot delete the only super administrator'
                }, status=400)
        
        user_email = user.email
        user.delete()
        
        logger.info(f"User {user_email} deleted by {request.user.email}")
        
        return JsonResponse({
            'success': True,
            'message': 'User deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Delete user error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to delete user'
        }, status=500)


@login_required
@require_admin_or_super_admin
@require_http_methods(["GET"])
def get_user_details(request, user_id):
    """Get detailed information about a specific user"""
    try:
        # Get user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=404)
        
        # Get profile data
        profile_data = {}
        if hasattr(user, 'staffprofile'):
            profile = user.staffprofile
            profile_data = {
                'type': 'staff',
                'department': profile.department,
                'position': profile.position,
                'phone_number': profile.phone_number,
                'address': profile.address,
                'join_date': profile.join_date.isoformat() if profile.join_date else None,
                'salary': str(profile.salary) if profile.salary else None,
                'created_at': profile.created_at.isoformat()
            }
        elif hasattr(user, 'patientprofile'):
            profile = user.patientprofile
            profile_data = {
                'type': 'patient',
                'date_of_birth': profile.date_of_birth.isoformat() if profile.date_of_birth else None,
                'gender': profile.gender,
                'blood_type': profile.blood_type,
                'emergency_contact': profile.emergency_contact,
                'address': profile.address,
                'insurance_info': profile.insurance_info,
                'medical_history': profile.medical_history,
                'created_at': profile.created_at.isoformat()
            }
        
        # Get groups and permissions
        groups = [group.name for group in user.groups.all()]
        permissions = [perm.codename for perm in user.user_permissions.all()]
        
        user_data = {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'full_name': user.full_name,
            'role': user.role,
            'phone_number': user.phone_number,
            'license_number': user.license_number,
            'certification': user.certification,
            'specialization': user.specialization,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'profile': profile_data,
            'groups': groups,
            'permissions': permissions
        }
        
        return JsonResponse({
            'success': True,
            'user': user_data
        })
        
    except Exception as e:
        logger.error(f"Get user details error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to fetch user details'
        }, status=500)


@csrf_exempt
@require_super_admin
@require_http_methods(["GET"])
def get_user_management_stats(request):
    """Get user management statistics"""
    try:
        # Basic statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        verified_users = User.objects.filter(is_verified=True).count()
        staff_users = User.objects.filter(is_staff=True).count()
        
        # Role distribution
        role_stats = {}
        for role_code, role_name in User.ROLE_CHOICES:
            count = User.objects.filter(role=role_code).count()
            role_stats[role_code] = {
                'name': role_name,
                'count': count
            }
        
        # Recent registrations (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_registrations = User.objects.filter(
            date_joined__gte=thirty_days_ago
        ).count()
        
        # Recent logins (last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_logins = User.objects.filter(
            last_login__gte=seven_days_ago
        ).count()
        
        return JsonResponse({
            'success': True,
            'statistics': {
                'total_users': total_users,
                'active_users': active_users,
                'verified_users': verified_users,
                'staff_users': staff_users,
                'inactive_users': total_users - active_users,
                'unverified_users': total_users - verified_users,
                'role_distribution': role_stats,
                'recent_registrations': recent_registrations,
                'recent_logins': recent_logins,
                'activity_rate': round((recent_logins / total_users * 100), 2) if total_users > 0 else 0
            }
        })
        
    except Exception as e:
        logger.error(f"Get user management stats error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to fetch statistics'
        }, status=500)


@csrf_exempt
@require_admin_or_super_admin
@require_http_methods(["GET"])
def get_available_features(request):
    """Get list of available features for selection"""
    try:
        from .models import FeatureAccess
        
        features = []
        for feature_code, feature_name in FeatureAccess.FEATURE_CHOICES:
            features.append({
                'code': feature_code,
                'name': feature_name,
                'description': get_feature_description(feature_code)
            })
        
        return JsonResponse({
            'success': True,
            'features': features
        })
        
    except Exception as e:
        logger.error(f"Get available features error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to fetch features'
        }, status=500)


@csrf_exempt
@require_admin_or_super_admin
@require_http_methods(["GET"])
def get_user_features(request, user_id):
    """Get features enabled for a specific user"""
    try:
        user = User.objects.get(id=user_id)
        from .models import FeatureAccess
        
        enabled_features = FeatureAccess.objects.filter(
            user=user, 
            is_enabled=True
        ).values_list('feature', flat=True)
        
        return JsonResponse({
            'success': True,
            'user_features': list(enabled_features)
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'User not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Get user features error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to fetch user features'
        }, status=500)


@csrf_exempt
@require_admin_or_super_admin
@require_http_methods(["POST"])
def update_user_features(request, user_id):
    """Update features enabled for a specific user"""
    try:
        data = json.loads(request.body)
        user = User.objects.get(id=user_id)
        selected_features = data.get('selected_features', [])
        
        from .models import FeatureAccess, UserFeatureProfile
        
        # Update or create UserFeatureProfile
        feature_profile, created = UserFeatureProfile.objects.get_or_create(
            user=user,
            defaults={'selected_features': selected_features}
        )
        if not created:
            feature_profile.selected_features = selected_features
            feature_profile.save()
        
        # Remove all existing feature access
        FeatureAccess.objects.filter(user=user).delete()
        
        # Create new feature access entries
        for feature in selected_features:
            FeatureAccess.objects.create(
                user=user,
                feature=feature,
                is_enabled=True
            )
        
        return JsonResponse({
            'success': True,
            'message': 'User features updated successfully'
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'User not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Update user features error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to update user features'
        }, status=500)


def get_feature_description(feature_code):
    """Get feature description for frontend display"""
    descriptions = {
        'medicine': 'General medicine, prescriptions, and patient care',
        'dentistry': 'Dental care, treatments, and oral health management',
        'dermatology': 'Skin conditions, treatments, and dermatological care',
        'pathology': 'Laboratory tests, diagnostics, and pathological analysis',
        'radiology': 'Medical imaging, X-rays, and radiological services',
        'patients': 'Patient registration, records, and management',
        'subscriptions': 'Subscription plans and billing management',
        'hospital': 'Hospital administration and management',
        'secureneat': 'Security and data protection features',
        'appointments': 'Appointment scheduling and management',
        'billing': 'Billing, payments, and financial management',
        'reports': 'Analytics, reports, and data insights',
        'emergency': 'Emergency services and critical care',
        'pharmacy': 'Pharmacy management and medication tracking',
        'lab_tests': 'Laboratory test orders and results',
        'imaging': 'Medical imaging and diagnostic tools',
        'telemedicine': 'Remote consultations and telehealth',
        'ai_diagnosis': 'AI-powered diagnosis and recommendations',
        'diabetes_management': 'Diabetes care and glucose monitoring',
        'cancer_detection': 'Cancer screening and detection tools',
    }
    return descriptions.get(feature_code, f'Access to {feature_code} features')


@csrf_exempt
@jwt_required
@require_http_methods(["GET"])
def get_current_user_permissions(request):
    """Get current user's permissions and dashboard features"""
    try:
        user = request.user
        
        # Build user permission data
        user_data = {
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role,
            'is_super_admin': user.role == 'super_admin',
            'permissions': {},
            'dashboard_features': {},
            'quota': None
        }
        
        # Super admin gets all permissions
        if user.role == 'super_admin':
            user_data['permissions'] = {
                'can_manage_users': True,
                'can_view_reports': True,
                'can_manage_departments': True,
                'can_access_billing': True,
                'can_manage_inventory': True,
                'can_access_emergency': True,
                'can_create_admins': True,
                'can_manage_system_settings': True,
                'can_access_all_features': True
            }
            user_data['dashboard_features'] = {
                'user_management': True,
                'patient_management': True,
                'doctor_management': True,
                'nurse_management': True,
                'pharmacist_management': True,
                'hospital_management': True,
                'clinic_management': True,
                'medicine_module': True,
                'dentistry_module': True,
                'dermatology_module': True,
                'pathology_module': True,
                'radiology_module': True,
                'subscription_management': True,
                'billing_reports': True,
                'financial_dashboard': True,
                'system_settings': True,
                'audit_logs': True,
                'user_analytics': True,
                'medical_reports': True,
                'revenue_reports': True,
                'appointment_analytics': True,
                'inventory_reports': True,
                'create_user': True,
                'schedule_appointment': True,
                'generate_report': True,
                'backup_system': True,
                'send_notifications': True
            }
        else:
            # Get admin permissions if they exist
            try:
                admin_permissions = AdminPermissions.objects.get(user=user)
                user_data['permissions'] = {
                    'can_manage_users': admin_permissions.can_manage_users,
                    'can_view_reports': admin_permissions.can_view_reports,
                    'can_manage_departments': admin_permissions.can_manage_departments,
                    'can_access_billing': admin_permissions.can_access_billing,
                    'can_manage_inventory': admin_permissions.can_manage_inventory,
                    'can_access_emergency': admin_permissions.can_access_emergency,
                    'can_create_admins': False,  # Only super admin can create admins
                    'can_manage_system_settings': False,  # Only super admin
                    'can_access_all_features': False  # Only super admin
                }
            except AdminPermissions.DoesNotExist:
                logger.warning(f"AdminPermissions not found for user {user.id}")
                # Default minimal permissions for admin without specific permissions
                user_data['permissions'] = {
                    'can_manage_users': False,
                    'can_view_reports': False,
                    'can_manage_departments': False,
                    'can_access_billing': False,
                    'can_manage_inventory': False,
                    'can_access_emergency': False,
                    'can_create_admins': False,
                    'can_manage_system_settings': False,
                    'can_access_all_features': False
                }
            except Exception as e:
                logger.error(f"Error fetching AdminPermissions for user {user.id}: {str(e)}")
                user_data['permissions'] = {
                    'can_manage_users': False,
                    'can_view_reports': False,
                    'can_manage_departments': False,
                    'can_access_billing': False,
                    'can_manage_inventory': False,
                    'can_access_emergency': False,
                    'can_create_admins': False,
                    'can_manage_system_settings': False,
                    'can_access_all_features': False
                }
            
            # Get dashboard features if they exist
            try:
                dashboard_features = AdminDashboardFeatures.objects.get(user=user)
                user_data['dashboard_features'] = {
                    'user_management': dashboard_features.user_management,
                    'patient_management': dashboard_features.patient_management,
                    'doctor_management': dashboard_features.doctor_management,
                    'nurse_management': dashboard_features.nurse_management,
                    'pharmacist_management': dashboard_features.pharmacist_management,
                    'hospital_management': dashboard_features.hospital_management,
                    'clinic_management': dashboard_features.clinic_management,
                    'medicine_module': dashboard_features.medicine_module,
                    'dentistry_module': dashboard_features.dentistry_module,
                    'dermatology_module': dashboard_features.dermatology_module,
                    'pathology_module': dashboard_features.pathology_module,
                    'radiology_module': dashboard_features.radiology_module,
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
                    'send_notifications': dashboard_features.send_notifications
                }
            except AdminDashboardFeatures.DoesNotExist:
                logger.warning(f"AdminDashboardFeatures not found for user {user.id}")
                # Default minimal dashboard features
                user_data['dashboard_features'] = {
                    'user_management': False,
                    'patient_management': False,
                    'doctor_management': False,
                    'nurse_management': False,
                    'pharmacist_management': False,
                    'hospital_management': False,
                    'clinic_management': False,
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
                    'user_analytics': False,
                    'medical_reports': False,
                    'revenue_reports': False,
                    'appointment_analytics': False,
                    'inventory_reports': False,
                    'create_user': False,
                    'schedule_appointment': False,
                    'generate_report': False,
                    'backup_system': False,
                    'send_notifications': False
                }
            except Exception as e:
                logger.error(f"Error fetching AdminDashboardFeatures for user {user.id}: {str(e)}")
                user_data['dashboard_features'] = {}
            
            # Get user creation quota if it exists
            try:
                quota = UserCreationQuota.objects.get(user=user)
                user_data['quota'] = {
                    'enabled': quota.enabled,
                    'max_total_users': quota.max_total_users,
                    'max_doctors': quota.max_doctors,
                    'max_nurses': quota.max_nurses,
                    'max_patients': quota.max_patients,
                    'max_pharmacists': quota.max_pharmacists,
                    'quota_reset_period': quota.quota_reset_period,
                    'current_usage': quota.current_usage
                }
            except UserCreationQuota.DoesNotExist:
                logger.warning(f"UserCreationQuota not found for user {user.id}")
                user_data['quota'] = None
            except Exception as e:
                logger.error(f"Error fetching UserCreationQuota for user {user.id}: {str(e)}")
                user_data['quota'] = None
        
        return JsonResponse({
            'success': True,
            'user': user_data
        })
        
    except Exception as e:
        logger.error(f"Get current user permissions error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'error': f'Failed to fetch user permissions: {str(e)}'
        }, status=500)
