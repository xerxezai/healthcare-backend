"""
First Login and Password Change Management Views
Handles mandatory password changes and first login setup
"""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import CustomUser as User
from .password_manager import PasswordManager

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def check_first_login_status(request):
    """Check if user needs first login setup after authentication"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return JsonResponse({
                'success': False,
                'error': 'Email is required'
            }, status=400)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=404)
        
        # Check if account is locked
        if user.is_account_locked():
            return JsonResponse({
                'success': False,
                'error': 'Account is temporarily locked due to failed login attempts',
                'locked_until': user.account_locked_until.isoformat() if user.account_locked_until else None
            }, status=423)
        
        # Check if password has expired
        if user.is_password_expired():
            return JsonResponse({
                'success': False,
                'error': 'Temporary password has expired. Please contact administrator.',
                'expired': True
            }, status=401)
        
        # Check first login status
        needs_setup = user.needs_first_login_setup()
        
        return JsonResponse({
            'success': True,
            'needs_first_login_setup': needs_setup,
            'password_change_required': user.password_change_required,
            'first_login_completed': user.first_login_completed,
            'temp_password_expires': user.temp_password_expires.isoformat() if user.temp_password_expires else None,
            'user_info': {
                'full_name': user.full_name,
                'role': user.role,
                'email': user.email
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Check first login status error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to check first login status'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def complete_first_login_setup(request):
    """Complete first login setup with password change"""
    try:
        data = json.loads(request.body)
        
        # Required fields
        required_fields = ['email', 'current_password', 'new_password', 'confirm_password']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'{field} is required'
                }, status=400)
        
        email = data.get('email')
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        # Validate password confirmation
        if new_password != confirm_password:
            return JsonResponse({
                'success': False,
                'error': 'New passwords do not match'
            }, status=400)
        
        # Get user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=404)
        
        # Check if account is locked
        if user.is_account_locked():
            return JsonResponse({
                'success': False,
                'error': 'Account is temporarily locked'
            }, status=423)
        
        # Authenticate with current password
        if not user.check_password(current_password):
            user.increment_failed_login()
            return JsonResponse({
                'success': False,
                'error': 'Current password is incorrect'
            }, status=401)
        
        # Validate new password against policy
        password_strength = PasswordManager.get_password_strength_score(new_password)
        if not PasswordManager.validate_password_requirements(new_password):
            return JsonResponse({
                'success': False,
                'error': 'New password does not meet security requirements',
                'password_feedback': password_strength['feedback']
            }, status=400)
        
        # Check if new password is different from current
        if user.check_password(new_password):
            return JsonResponse({
                'success': False,
                'error': 'New password must be different from current password'
            }, status=400)
        
        # Update password and complete first login setup
        user.set_password(new_password)  # This method handles all the flags
        user.reset_failed_logins()
        user.save()
        
        logger.info(f"First login setup completed for user: {user.email}")
        
        return JsonResponse({
            'success': True,
            'message': 'Password changed successfully. First login setup complete.',
            'password_strength': {
                'score': password_strength['score'],
                'level': password_strength['strength']
            },
            'user_info': {
                'full_name': user.full_name,
                'role': user.role,
                'email': user.email,
                'first_login_completed': True
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Complete first login setup error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to complete first login setup'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def change_password(request):
    """Change password for authenticated users"""
    try:
        data = json.loads(request.body)
        
        # Required fields
        required_fields = ['email', 'current_password', 'new_password', 'confirm_password']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'{field} is required'
                }, status=400)
        
        email = data.get('email')
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        # Validate password confirmation
        if new_password != confirm_password:
            return JsonResponse({
                'success': False,
                'error': 'New passwords do not match'
            }, status=400)
        
        # Get user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=404)
        
        # Authenticate with current password
        if not user.check_password(current_password):
            return JsonResponse({
                'success': False,
                'error': 'Current password is incorrect'
            }, status=401)
        
        # Validate new password against policy
        password_strength = PasswordManager.get_password_strength_score(new_password)
        if not PasswordManager.validate_password_requirements(new_password):
            return JsonResponse({
                'success': False,
                'error': 'New password does not meet security requirements',
                'password_feedback': password_strength['feedback']
            }, status=400)
        
        # Check if new password is different from current
        if user.check_password(new_password):
            return JsonResponse({
                'success': False,
                'error': 'New password must be different from current password'
            }, status=400)
        
        # Update password
        user.set_password(new_password)
        user.save()
        
        logger.info(f"Password changed for user: {user.email}")
        
        return JsonResponse({
            'success': True,
            'message': 'Password changed successfully',
            'password_strength': {
                'score': password_strength['score'],
                'level': password_strength['strength']
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to change password'
        }, status=500)


@csrf_exempt  
@require_http_methods(["POST"])
def validate_password_strength(request):
    """Validate password strength in real-time"""
    try:
        data = json.loads(request.body)
        password = data.get('password', '')
        
        if not password:
            return JsonResponse({
                'success': False,
                'error': 'Password is required'
            }, status=400)
        
        # Get password strength and validation
        strength = PasswordManager.get_password_strength_score(password)
        is_valid = PasswordManager.validate_password_requirements(password)
        
        return JsonResponse({
            'success': True,
            'strength': strength,
            'is_valid': is_valid,
            'meets_requirements': is_valid
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Validate password strength error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to validate password'
        }, status=500)
