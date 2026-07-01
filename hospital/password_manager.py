"""
Secure Password Management Utilities
Provides consistent password generation, validation, and handling
"""
import secrets
import string
import re
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class PasswordManager:
    """Centralized password management with soft-coded policies"""
    
    # Soft-coded password policy configuration
    DEFAULT_PASSWORD_CONFIG = {
        'min_length': 12,
        'max_length': 32,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_digits': True,
        'require_special_chars': True,
        'special_chars': '!@#$%^&*()_+-=[]{}|;:,.<>?',
        'exclude_ambiguous': True,  # Exclude 0, O, l, I, etc.
        'auto_generate_for_admin': True,
        'force_password_change': True,  # Force change on first login
        'password_expiry_days': 90
    }
    
    # Ambiguous characters to exclude for better user experience
    AMBIGUOUS_CHARS = '0O1lI'
    
    @classmethod
    def get_password_config(cls):
        """Get password configuration from settings or use defaults"""
        return getattr(settings, 'PASSWORD_POLICY', cls.DEFAULT_PASSWORD_CONFIG)
    
    @classmethod
    def generate_secure_password(cls, user_type='admin', custom_length=None):
        """
        Generate a cryptographically secure password based on user type
        
        Args:
            user_type (str): Type of user (admin, doctor, nurse, patient, etc.)
            custom_length (int): Override default length
            
        Returns:
            str: Generated secure password
        """
        config = cls.get_password_config()
        
        # User-type specific configurations
        type_configs = {
            'admin': {'length': 16, 'complexity': 'high'},
            'super_admin': {'length': 20, 'complexity': 'maximum'},
            'doctor': {'length': 14, 'complexity': 'high'},
            'nurse': {'length': 12, 'complexity': 'medium'},
            'patient': {'length': 10, 'complexity': 'medium'},
            'pharmacist': {'length': 12, 'complexity': 'medium'}
        }
        
        user_config = type_configs.get(user_type, type_configs['admin'])
        length = custom_length or user_config['length']
        
        # Build character pool based on requirements
        chars = []
        
        if config.get('require_lowercase', True):
            lowercase = string.ascii_lowercase
            if config.get('exclude_ambiguous', True):
                lowercase = ''.join(c for c in lowercase if c not in cls.AMBIGUOUS_CHARS)
            chars.extend(lowercase)
        
        if config.get('require_uppercase', True):
            uppercase = string.ascii_uppercase
            if config.get('exclude_ambiguous', True):
                uppercase = ''.join(c for c in uppercase if c not in cls.AMBIGUOUS_CHARS)
            chars.extend(uppercase)
        
        if config.get('require_digits', True):
            digits = string.digits
            if config.get('exclude_ambiguous', True):
                digits = ''.join(c for c in digits if c not in cls.AMBIGUOUS_CHARS)
            chars.extend(digits)
        
        if config.get('require_special_chars', True):
            special = config.get('special_chars', '!@#$%^&*')
            chars.extend(special)
        
        if not chars:
            raise ValueError("Password policy too restrictive - no valid characters available")
        
        # Generate password ensuring all required character types
        while True:
            password = ''.join(secrets.choice(chars) for _ in range(length))
            
            if cls.validate_password_requirements(password, config):
                return password
    
    @classmethod
    def validate_password_requirements(cls, password, config=None):
        """
        Validate password against soft-coded requirements
        
        Args:
            password (str): Password to validate
            config (dict): Password policy configuration
            
        Returns:
            bool: True if password meets all requirements
        """
        if config is None:
            config = cls.get_password_config()
        
        # Length check
        if len(password) < config.get('min_length', 8):
            return False
        if len(password) > config.get('max_length', 128):
            return False
        
        # Character type requirements
        if config.get('require_uppercase', False) and not re.search(r'[A-Z]', password):
            return False
        
        if config.get('require_lowercase', False) and not re.search(r'[a-z]', password):
            return False
        
        if config.get('require_digits', False) and not re.search(r'[0-9]', password):
            return False
        
        if config.get('require_special_chars', False):
            special_chars = config.get('special_chars', '!@#$%^&*')
            if not any(char in password for char in special_chars):
                return False
        
        return True
    
    @classmethod
    def get_password_strength_score(cls, password):
        """
        Calculate password strength score (0-100)
        
        Args:
            password (str): Password to evaluate
            
        Returns:
            dict: Score and feedback
        """
        score = 0
        feedback = []
        
        # Length scoring
        if len(password) >= 12:
            score += 25
        elif len(password) >= 8:
            score += 15
            feedback.append("Consider using a longer password")
        else:
            feedback.append("Password is too short")
        
        # Character variety
        if re.search(r'[a-z]', password):
            score += 15
        else:
            feedback.append("Add lowercase letters")
        
        if re.search(r'[A-Z]', password):
            score += 15
        else:
            feedback.append("Add uppercase letters")
        
        if re.search(r'[0-9]', password):
            score += 15
        else:
            feedback.append("Add numbers")
        
        if re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
            score += 20
        else:
            feedback.append("Add special characters")
        
        # Complexity bonus
        unique_chars = len(set(password))
        if unique_chars >= len(password) * 0.8:
            score += 10
        
        return {
            'score': min(score, 100),
            'strength': cls._get_strength_level(score),
            'feedback': feedback
        }
    
    @classmethod
    def _get_strength_level(cls, score):
        """Convert numeric score to strength level"""
        if score >= 90:
            return 'Excellent'
        elif score >= 70:
            return 'Strong'
        elif score >= 50:
            return 'Moderate'
        elif score >= 30:
            return 'Weak'
        else:
            return 'Very Weak'


class AdminPasswordManager:
    """Specialized password management for admin users"""
    
    @staticmethod
    def create_admin_with_secure_password(user_data, user_type='admin'):
        """
        Create admin user with auto-generated secure password
        
        Args:
            user_data (dict): User creation data
            user_type (str): Type of admin user
            
        Returns:
            dict: User object and generated password
        """
        # Generate secure password
        secure_password = PasswordManager.generate_secure_password(user_type)
        
        # Store original password for email
        original_password = secure_password
        
        # Add password to user data
        user_data['password'] = secure_password
        user_data['force_password_change'] = True
        
        return {
            'user_data': user_data,
            'generated_password': original_password,
            'password_strength': PasswordManager.get_password_strength_score(secure_password)
        }
    
    @staticmethod
    def generate_temporary_password(length=12):
        """Generate temporary password for immediate use"""
        return PasswordManager.generate_secure_password('admin', length)


# Utility functions for backward compatibility
def generate_admin_password():
    """Generate a secure password for admin users"""
    return PasswordManager.generate_secure_password('admin')

def validate_user_password(password, user_type='admin'):
    """Validate password against policy"""
    return PasswordManager.validate_password_requirements(password)
