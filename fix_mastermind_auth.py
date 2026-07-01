#!/usr/bin/env python
import os
import sys
import django

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from hospital.models import CustomUser

def fix_mastermind_auth():
    """Fix mastermind user authentication"""
    try:
        # Get or create mastermind user
        mastermind_user, created = CustomUser.objects.get_or_create(
            username='mastermind',
            defaults={
                'email': 'mastermind@xerxez.com',
                'full_name': 'Super Administrator',
                'role': 'super_admin',
                'is_superuser': True,
                'is_staff': True,
                'is_active': True,
                'is_verified': True,
            }
        )
        
        if created:
            print("✅ Created new mastermind user")
        else:
            print("✅ Found existing mastermind user")
            
        # Set the password
        mastermind_user.set_password('Tanzilla@tanzeem786')
        mastermind_user.save()
        
        print(f"✅ Password set for user: {mastermind_user.username}")
        print(f"📧 Email: {mastermind_user.email}")
        print(f"🔑 Role: {mastermind_user.role}")
        print(f"🛡️ Is superuser: {mastermind_user.is_superuser}")
        print(f"📋 Is staff: {mastermind_user.is_staff}")
        print(f"✔️ Is active: {mastermind_user.is_active}")
        
        # Test login
        if mastermind_user.check_password('Tanzilla@tanzeem786'):
            print("✅ Password verification successful!")
        else:
            print("❌ Password verification failed!")
            
        return True
        
    except Exception as e:
        print(f"❌ Error fixing mastermind auth: {e}")
        return False

if __name__ == '__main__':
    print("🔧 Fixing mastermind user authentication...")
    success = fix_mastermind_auth()
    if success:
        print("🎉 Mastermind auth fixed successfully!")
    else:
        print("💥 Failed to fix mastermind auth!")
