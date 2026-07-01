# Password Policy Configuration for Healthcare Platform
# This file contains soft-coded password policies that can be easily adjusted

"""
Soft-Coded Password Policy Configuration
Allows easy customization for different customer deployments
"""
import os
from django.conf import settings

# Environment-based configuration override
def get_env_bool(key, default=False):
    """Get boolean environment variable"""
    return os.getenv(key, str(default)).lower() in ('true', '1', 'yes', 'on')

def get_env_int(key, default=0):
    """Get integer environment variable"""
    try:
        return int(os.getenv(key, default))
    except (ValueError, TypeError):
        return default

# Base password policy configuration
BASE_PASSWORD_POLICY = {
    'min_length': get_env_int('PASSWORD_MIN_LENGTH', 8),
    'require_uppercase': get_env_bool('PASSWORD_REQUIRE_UPPERCASE', True),
    'require_lowercase': get_env_bool('PASSWORD_REQUIRE_LOWERCASE', True),
    'require_numbers': get_env_bool('PASSWORD_REQUIRE_NUMBERS', True),
    'require_special_chars': get_env_bool('PASSWORD_REQUIRE_SPECIAL', True),
    'max_age_days': get_env_int('PASSWORD_MAX_AGE_DAYS', 90),
    'temp_password_expiry_hours': get_env_int('TEMP_PASSWORD_EXPIRY_HOURS', 24),
    'max_failed_attempts': get_env_int('MAX_FAILED_LOGIN_ATTEMPTS', 5),
    'lockout_duration_minutes': get_env_int('LOCKOUT_DURATION_MINUTES', 30),
}

# Customer-specific deployment settings
DEPLOYMENT_CONFIG = {
    'customer_name': os.getenv('CUSTOMER_NAME', 'Healthcare Platform'),
    'support_email': os.getenv('SUPPORT_EMAIL', 'support@xerxez.in'),
    'platform_name': os.getenv('PLATFORM_NAME', 'Xerxez Healthcare'),
    'frontend_url': os.getenv('FRONTEND_URL', 'http://localhost:5173'),
    'backend_url': os.getenv('BACKEND_URL', 'http://localhost:8000'),
    'login_url': os.getenv('LOGIN_URL', f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/auth/login"),
    'dashboard_url': os.getenv('DASHBOARD_URL', f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/dashboard"),
    'mandatory_password_change': get_env_bool('MANDATORY_PASSWORD_CHANGE', True),
    'password_strength_enforcement': os.getenv('PASSWORD_STRENGTH_ENFORCEMENT', 'strict'),  # strict, moderate, lenient
    'send_password_emails': get_env_bool('SEND_PASSWORD_EMAILS', True),
    'enable_first_login_setup': get_env_bool('ENABLE_FIRST_LOGIN_SETUP', True),
    'enable_password_reset_menu': get_env_bool('ENABLE_PASSWORD_RESET_MENU', True),
}

# Password Generation Policies
PASSWORD_POLICY = {
    # Base requirements (maintained for backward compatibility)
    'min_length': 12,
    'max_length': 32,
    'require_uppercase': True,
    'require_lowercase': True,
    'require_digits': True,
    'require_special_chars': True,
    'special_chars': '!@#$%^&*()_+-=[]{}|;:,.<>?',
    'exclude_ambiguous': True,  # Exclude 0, O, l, I, etc.
    
    # User type specific policies (enhanced with environment variables)
    'user_type_configs': {
        'super_admin': {
            'force_change_on_creation': get_env_bool('SUPER_ADMIN_FORCE_CHANGE', True),
            'min_length': get_env_int('SUPER_ADMIN_MIN_LENGTH', 16),
            'complexity_level': os.getenv('SUPER_ADMIN_COMPLEXITY', 'maximum'),
            'expiry_days': get_env_int('SUPER_ADMIN_EXPIRY_DAYS', 30),
            'auto_generate': get_env_bool('SUPER_ADMIN_AUTO_GENERATE', True),
            'require_special_chars': get_env_int('SUPER_ADMIN_SPECIAL_CHARS', 3),
            'require_numbers': get_env_int('SUPER_ADMIN_NUMBERS', 2),
            # Legacy fields for backward compatibility
            'length': 20,
            'complexity': 'maximum',
            'force_change': True
        },
        'admin': {
            'force_change_on_creation': get_env_bool('ADMIN_FORCE_CHANGE', True),
            'min_length': get_env_int('ADMIN_MIN_LENGTH', 14),
            'complexity_level': os.getenv('ADMIN_COMPLEXITY', 'high'),
            'expiry_days': get_env_int('ADMIN_EXPIRY_DAYS', 60),
            'auto_generate': get_env_bool('ADMIN_AUTO_GENERATE', True),
            'require_special_chars': get_env_int('ADMIN_SPECIAL_CHARS', 2),
            'require_numbers': get_env_int('ADMIN_NUMBERS', 2),
            # Legacy fields for backward compatibility
            'length': 16,
            'complexity': 'high',
            'force_change': True
        },
        'doctor': {
            'force_change_on_creation': get_env_bool('DOCTOR_FORCE_CHANGE', True),
            'min_length': get_env_int('DOCTOR_MIN_LENGTH', 12),
            'complexity_level': os.getenv('DOCTOR_COMPLEXITY', 'high'),
            'expiry_days': get_env_int('DOCTOR_EXPIRY_DAYS', 90),
            'auto_generate': get_env_bool('DOCTOR_AUTO_GENERATE', True),
            'require_special_chars': get_env_int('DOCTOR_SPECIAL_CHARS', 2),
            'require_numbers': get_env_int('DOCTOR_NUMBERS', 1),
            # Legacy fields for backward compatibility
            'length': 14,
            'complexity': 'high',
            'force_change': True
        },
        'nurse': {
            'force_change_on_creation': get_env_bool('NURSE_FORCE_CHANGE', False),
            'min_length': get_env_int('NURSE_MIN_LENGTH', 10),
            'complexity_level': os.getenv('NURSE_COMPLEXITY', 'medium'),
            'expiry_days': get_env_int('NURSE_EXPIRY_DAYS', 90),
            'auto_generate': get_env_bool('NURSE_AUTO_GENERATE', True),
            'require_special_chars': get_env_int('NURSE_SPECIAL_CHARS', 1),
            'require_numbers': get_env_int('NURSE_NUMBERS', 1),
            # Legacy fields for backward compatibility
            'length': 12,
            'complexity': 'medium',
            'force_change': False
        },
        'patient': {
            'force_change_on_creation': get_env_bool('PATIENT_FORCE_CHANGE', False),
            'min_length': get_env_int('PATIENT_MIN_LENGTH', 8),
            'complexity_level': os.getenv('PATIENT_COMPLEXITY', 'medium'),
            'expiry_days': get_env_int('PATIENT_EXPIRY_DAYS', 180),
            'auto_generate': get_env_bool('PATIENT_AUTO_GENERATE', False),
            'require_special_chars': get_env_int('PATIENT_SPECIAL_CHARS', 1),
            'require_numbers': get_env_int('PATIENT_NUMBERS', 1),
            # Legacy fields for backward compatibility
            'length': 10,
            'complexity': 'medium',
            'force_change': False
        },
        'pharmacist': {
            'force_change_on_creation': get_env_bool('PHARMACIST_FORCE_CHANGE', False),
            'min_length': get_env_int('PHARMACIST_MIN_LENGTH', 10),
            'complexity_level': os.getenv('PHARMACIST_COMPLEXITY', 'medium'),
            'expiry_days': get_env_int('PHARMACIST_EXPIRY_DAYS', 90),
            'auto_generate': get_env_bool('PHARMACIST_AUTO_GENERATE', True),
            'require_special_chars': get_env_int('PHARMACIST_SPECIAL_CHARS', 1),
            'require_numbers': get_env_int('PHARMACIST_NUMBERS', 1),
            # Legacy fields for backward compatibility
            'length': 12,
            'complexity': 'medium',
            'force_change': False
        },
        'default': {
            'force_change_on_creation': get_env_bool('DEFAULT_FORCE_CHANGE', False),
            'min_length': get_env_int('DEFAULT_MIN_LENGTH', 8),
            'complexity_level': os.getenv('DEFAULT_COMPLEXITY', 'medium'),
            'expiry_days': get_env_int('DEFAULT_EXPIRY_DAYS', 90),
            'auto_generate': get_env_bool('DEFAULT_AUTO_GENERATE', False),
            'require_special_chars': get_env_int('DEFAULT_SPECIAL_CHARS', 1),
            'require_numbers': get_env_int('DEFAULT_NUMBERS', 1),
            # Legacy fields for backward compatibility
            'length': 8,
            'complexity': 'medium',
            'force_change': False
        }
    },
    
    # Email notification settings (enhanced with deployment config)
    'email_notifications': {
        'send_for_roles': ['admin', 'super_admin', 'doctor'],
        'include_strength_info': True,
        'include_security_tips': True,
        'template_path': 'notifications/email/admin_account_created.html',
        'enabled': DEPLOYMENT_CONFIG['send_password_emails']
    },
    
    # Security settings (enhanced with environment variables)
    'security': {
        'hash_algorithm': 'pbkdf2_sha256',
        'require_unique_password': True,  # Password must be different from previous passwords
        'password_history_count': get_env_int('PASSWORD_HISTORY_COUNT', 5),      # Remember last 5 passwords
        'lockout_after_attempts': BASE_PASSWORD_POLICY['max_failed_attempts'],      # Lock account after failed attempts
        'lockout_duration_minutes': BASE_PASSWORD_POLICY['lockout_duration_minutes']    # Lock duration in minutes
    }
}

# Customer deployment configuration examples
CUSTOMER_DEPLOYMENT_EXAMPLES = {
    'healthcare_enterprise': {
        'description': 'High-security healthcare enterprise',
        'env_vars': {
            'MANDATORY_PASSWORD_CHANGE': 'true',
            'PASSWORD_STRENGTH_ENFORCEMENT': 'strict',
            'ADMIN_FORCE_CHANGE': 'true',
            'ADMIN_MIN_LENGTH': '16',
            'TEMP_PASSWORD_EXPIRY_HOURS': '12',
        }
    },
    'clinic_standard': {
        'description': 'Standard clinic deployment',
        'env_vars': {
            'MANDATORY_PASSWORD_CHANGE': 'true', 
            'PASSWORD_STRENGTH_ENFORCEMENT': 'moderate',
            'ADMIN_FORCE_CHANGE': 'true',
            'ADMIN_MIN_LENGTH': '12',
            'TEMP_PASSWORD_EXPIRY_HOURS': '24',
        }
    },
    'small_practice': {
        'description': 'Small practice with relaxed security',
        'env_vars': {
            'MANDATORY_PASSWORD_CHANGE': 'false',
            'PASSWORD_STRENGTH_ENFORCEMENT': 'lenient',
            'ADMIN_FORCE_CHANGE': 'false',
            'ADMIN_MIN_LENGTH': '8',
            'TEMP_PASSWORD_EXPIRY_HOURS': '48',
        }
    }
}

def get_policy_for_user_type(user_type):
    """Get password policy for specific user type"""
    return PASSWORD_POLICY['user_type_configs'].get(user_type, PASSWORD_POLICY['user_type_configs']['default'])

def should_force_password_change(user_type):
    """Check if password change should be forced for user type"""
    if not DEPLOYMENT_CONFIG['enable_first_login_setup']:
        return False
    
    policy = get_policy_for_user_type(user_type)
    return policy.get('force_change_on_creation', False)

def get_password_requirements_text(user_type='default'):
    """Get human-readable password requirements for user type"""
    policy = get_policy_for_user_type(user_type)
    base_policy = BASE_PASSWORD_POLICY
    
    requirements = []
    requirements.append(f"At least {policy['min_length']} characters long")
    
    if base_policy['require_uppercase']:
        requirements.append("Contains uppercase letters")
    if base_policy['require_lowercase']:
        requirements.append("Contains lowercase letters")
    if base_policy['require_numbers']:
        requirements.append(f"Contains at least {policy['require_numbers']} number(s)")
    if base_policy['require_special_chars']:
        requirements.append(f"Contains at least {policy['require_special_chars']} special character(s)")
    
    return requirements

def get_deployment_info():
    """Get current deployment configuration info"""
    return {
        'customer_name': DEPLOYMENT_CONFIG['customer_name'],
        'platform_name': DEPLOYMENT_CONFIG['platform_name'],
        'support_email': DEPLOYMENT_CONFIG['support_email'],
        'mandatory_password_change': DEPLOYMENT_CONFIG['mandatory_password_change'],
        'password_strength_enforcement': DEPLOYMENT_CONFIG['password_strength_enforcement'],
        'first_login_setup_enabled': DEPLOYMENT_CONFIG['enable_first_login_setup'],
    }

# Email template customization
EMAIL_TEMPLATES = {
    'admin_created': {
        'subject': '🎉 Admin Account Created - Welcome to {platform_name}',
        'template': 'notifications/email/admin_account_created.html',
        'include_password_strength': True,
        'include_security_tips': True
    },
    'password_reset': {
        'subject': '🔒 Password Reset Request - {platform_name}',
        'template': 'notifications/email/password_reset.html'
    }
}

# Logging configuration for password operations
PASSWORD_LOGGING = {
    'log_creation': True,
    'log_changes': True,
    'log_failed_attempts': True,
    'log_strength_scores': True,
    'audit_retention_days': 365
}

# Frontend integration settings
FRONTEND_CONFIG = {
    'show_password_strength': True,
    'allow_manual_passwords': {
        'super_admin': False,  # Super admins must use auto-generated
        'admin': True,         # Admins can choose
        'doctor': True,
        'nurse': True,
        'patient': True,
        'pharmacist': True
    },
    'password_visibility_toggle': True,
    'strength_meter_enabled': True
}
