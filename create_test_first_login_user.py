#!/usr/bin/env python
"""
Script to create a test admin user for first login testing
"""
import os
import sys
import django

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from hospital.models import CustomUser
from hospital.password_manager import AdminPasswordManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def create_test_admin():
    email = 'testfirstlogin@example.com'
    password_manager = AdminPasswordManager()
    temp_password = password_manager.generate_temporary_password()
    
    try:
        # Delete existing user if exists
        try:
            existing_user = CustomUser.objects.get(email=email)
            existing_user.delete()
            print(f'🗑️ Deleted existing user: {email}')
        except CustomUser.DoesNotExist:
            pass
        
        # Create new user
        user = CustomUser.objects.create_user(
            email=email,
            password=temp_password,
            full_name='Test First Login Admin',
            role='admin'
        )
        
        # Apply password policy requirements manually
        user.require_password_change()
        user.save()
        
        print(f'✅ Created test admin user: {email}')
        print(f'📧 Temporary password: {temp_password}')
        print(f'🔒 Password change required: {user.password_change_required}')
        print(f'🆕 First login setup needed: {user.needs_first_login_setup()}')
        print(f'👤 User role: {user.role}')
        print(f'📅 First login completed: {user.first_login_completed}')
        
        return True
        
    except Exception as e:
        print(f'❌ Error creating user: {e}')
        return False

if __name__ == '__main__':
    create_test_admin()
