"""
Custom authentication backend that works with our database structure.
This bypasses Django's default authentication system.
"""
import hashlib
import psycopg2
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from django.conf import settings
from hospital.models import CustomUser


class SimpleAuthBackend(BaseBackend):
    """
    Simple authentication backend that directly works with the database.
    """
    
    def authenticate(self, request, username=None, password=None, email=None, **kwargs):
        # Support both username and email parameters
        email_to_use = email or username
        if email_to_use is None or password is None:
            return None
        
        print(f"🔐 Authenticating user: {email_to_use}")
        
        try:
            # Try to get user from hospital_customuser table
            user = CustomUser.objects.using('default').get(email=email_to_use)
            
            # Check password using Django's built-in hasher
            print(f"🔐 Checking password for user: {user.email}")
            if check_password(password, user.password):
                print(f"✅ Authentication successful for: {user.email}")
                return user
            else:
                print(f"❌ Password check failed for: {user.email}")
                return None
                
        except CustomUser.DoesNotExist:
            print(f"❌ User not found: {email_to_use}")
            return None
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return None
    
    def get_user(self, user_id):
        try:
            return CustomUser.objects.using('default').get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None


class DirectDatabaseAuthBackend(BaseBackend):
    """
    Fallback authentication that queries the database directly.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        
        try:
            # Get database configuration
            db_config = settings.DATABASES['default']
            
            # Connect directly to PostgreSQL
            conn = psycopg2.connect(
                host=db_config['HOST'],
                port=db_config['PORT'],
                user=db_config['USER'],
                password=db_config['PASSWORD'],
                database=db_config['NAME']
            )
            cursor = conn.cursor()
            
            # Query users table directly (new comprehensive schema)
            cursor.execute(
                "SELECT id, password_hash, email, full_name, role, is_active FROM users WHERE email = %s OR username = %s",
                (username, username)
            )
            user_data = cursor.fetchone()
            
            if user_data:
                user_id, hashed_password, email, full_name, role, is_active = user_data
                
                # Check password
                if check_password(password, hashed_password) and is_active:
                    # Create a mock user object
                    user = type('User', (), {
                        'id': user_id,
                        'email': email,
                        'username': email,
                        'full_name': full_name,
                        'role': role,
                        'is_active': is_active,
                        'is_authenticated': True,
                        'is_anonymous': False,
                    })()
                    
                    cursor.close()
                    conn.close()
                    return user
            
            cursor.close()
            conn.close()
            return None
            
        except Exception as e:
            print(f"Direct database authentication error: {e}")
            return None
    
    def get_user(self, user_id):
        try:
            # Get database configuration
            db_config = settings.DATABASES['default']
            
            # Connect directly to PostgreSQL
            conn = psycopg2.connect(
                host=db_config['HOST'],
                port=db_config['PORT'],
                user=db_config['USER'],
                password=db_config['PASSWORD'],
                database=db_config['NAME']
            )
            cursor = conn.cursor()
            
            # Query hospital_customuser table directly
            cursor.execute(
                "SELECT id, email, first_name, last_name, is_active FROM hospital_customuser WHERE id = %s",
                (user_id,)
            )
            user_data = cursor.fetchone()
            
            if user_data:
                user_id, email, first_name, last_name, is_active = user_data
                
                # Create a mock user object
                user = type('User', (), {
                    'id': user_id,
                    'email': email,
                    'username': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_active': is_active,
                    'is_authenticated': True,
                    'is_anonymous': False,
                })()
                
                cursor.close()
                conn.close()
                return user
            
            cursor.close()
            conn.close()
            return None
            
        except Exception as e:
            print(f"Direct database get_user error: {e}")
            return None
