from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder
from django.middleware.csrf import get_token
import json
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def login_api(request):
    """
    API endpoint for user authentication
    """
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        print(f"🔐 Login attempt - Email: {email}")
        
        if not email or not password:
            print("❌ Missing email or password")
            return JsonResponse({
                'success': False,
                'error': 'Email and password are required'
            }, status=400)
        
        # Authenticate user by email (not username)
        try:
            print(f"🔍 Looking up user with email: {email}")
            user = User.objects.get(email=email)
            print(f"✅ User found: {user.email} (ID: {user.id})")
            
            if user.check_password(password):
                print(f"✅ Password check passed for: {user.email}")
                if not user.is_active:
                    return JsonResponse({
                        'success': False,
                        'error': 'Account is deactivated'
                    }, status=401)
                
                # Log the user in - specify backend for multiple auth backends
                django_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
                # Get user's enabled features
                from .models import FeatureAccess
                enabled_features = FeatureAccess.objects.filter(
                    user=user, is_enabled=True
                ).values_list('feature', flat=True)
                
                # Return user data
                user_data = {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'full_name': user.full_name,
                    'role': user.role,
                    'is_superuser': user.is_superuser,
                    'is_staff': user.is_staff,
                    'is_active': user.is_active,
                    'is_verified': user.is_verified,
                    'phone_number': user.phone_number,
                    'specialization': user.specialization,
                    'license_number': user.license_number,
                    'certification': user.certification,
                    'subscription_bypass': user.is_superuser,  # Super users bypass subscription
                    'enabled_features': list(enabled_features),  # Include user's features
                }
                
                logger.info(f"User {user.email} logged in successfully with role {user.role}")
                
                return JsonResponse({
                    'success': True,
                    'message': 'Login successful',
                    'user': user_data,
                    'token': 'session-based-auth'  # We're using session-based auth for now
                }, status=200)
                
            else:
                print(f"❌ Password check failed for: {user.email}")
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid email or password'
                }, status=401)
                
        except User.DoesNotExist:
            print(f"❌ User not found with email: {email}")
            return JsonResponse({
                'success': False,
                'error': 'Invalid email or password'
            }, status=401)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def logout_api(request):
    """
    API endpoint for user logout
    """
    try:
        user_email = request.user.email
        django_logout(request)
        
        logger.info(f"User {user_email} logged out successfully")
        
        return JsonResponse({
            'success': True,
            'message': 'Logout successful'
        }, status=200)
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def user_profile_api(request):
    """
    API endpoint to get current user profile
    """
    try:
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required'
            }, status=401)
            
        user = request.user
        
        # Get user's enabled features
        from .models import FeatureAccess
        enabled_features = FeatureAccess.objects.filter(
            user=user, is_enabled=True
        ).values_list('feature', flat=True)
        
        user_data = {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'full_name': user.full_name,
            'role': user.role,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'phone_number': user.phone_number,
            'specialization': user.specialization,
            'license_number': user.license_number,
            'certification': user.certification,
            'subscription_bypass': user.is_superuser,
            'enabled_features': list(enabled_features),
        }
        
        return JsonResponse({
            'success': True,
            'user': user_data
        }, status=200)
        
    except Exception as e:
        logger.error(f"User profile error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def register_api(request):
    """
    API endpoint for user registration
    """
    try:
        data = json.loads(request.body)
        
        required_fields = ['email', 'password', 'full_name', 'role']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'{field} is required'
                }, status=400)
        
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        role = data.get('role')
        
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
        
        # Only super admin can create admin users
        if role in ['admin', 'super_admin'] and not (
            request.user.is_authenticated and request.user.role == 'super_admin'
        ):
            return JsonResponse({
                'success': False,
                'error': 'Only super administrators can create admin users'
            }, status=403)
        
        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
            full_name=full_name,
            role=role,
            phone_number=data.get('phone_number', ''),
            license_number=data.get('license_number', ''),
            certification=data.get('certification', ''),
            specialization=data.get('specialization', ''),
            is_verified=True  # Auto-verify for demo
        )
        
        logger.info(f"New user registered: {user.email} with role {user.role}")
        
        return JsonResponse({
            'success': True,
            'message': 'Registration successful',
            'user_id': user.id
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@ensure_csrf_cookie
@require_http_methods(["GET"])
def csrf_token_api(request):
    """
    API endpoint to get CSRF token for frontend
    """
    try:
        csrf_token = get_token(request)
        return JsonResponse({
            'success': True,
            'csrf_token': csrf_token
        }, status=200)
    except Exception as e:
        logger.error(f"CSRF token error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get CSRF token'
        }, status=500)
