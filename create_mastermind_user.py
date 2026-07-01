#!/usr/bin/env python
"""
Create mastermind@xerxez.com super admin user in production database
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

def create_mastermind_user():
    """Create or update the mastermind super admin user"""
    
    email = 'mastermind@xerxez.com'
    password = 'Tanzilla@tanzeem786'
    
    try:
        with transaction.atomic():
            # Check if user exists
            user, created = User.objects.update_or_create(
                email=email,
                defaults={
                    'username': 'mastermind',
                    'full_name': 'Mastermind Super Admin',
                    'role': 'super_admin',
                    'is_active': True,
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            
            # Set the password
            user.set_password(password)
            user.save()
            
            if created:
                print(f"✅ Created new super admin user: {email}")
            else:
                print(f"✅ Updated existing super admin user: {email}")
                
            print(f"📧 Email: {email}")
            print(f"🔑 Password: {password}")
            print(f"👤 Username: {user.username}")
            print(f"🛡️ Role: {user.role}")
            print(f"✓ Is Active: {user.is_active}")
            print(f"✓ Is Staff: {user.is_staff}")
            print(f"✓ Is Superuser: {user.is_superuser}")
            
            # Verify password works
            from django.contrib.auth import authenticate
            test_user = authenticate(username=email, password=password)
            if test_user:
                print("\n✅ Password authentication verified successfully!")
            else:
                print("\n⚠️ Warning: Password authentication failed - checking...")
                # Try setting password again
                user.set_password(password)
                user.save()
                test_user = authenticate(username=email, password=password)
                if test_user:
                    print("✅ Password re-set and verified successfully!")
                else:
                    print("❌ Password authentication still failing")
                    
            return user
            
    except Exception as e:
        print(f"❌ Error creating user: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    print("=" * 60)
    print("CREATING MASTERMIND SUPER ADMIN USER")
    print("=" * 60)
    
    user = create_mastermind_user()
    
    if user:
        print("\n" + "=" * 60)
        print("✅ MASTERMIND USER READY FOR PRODUCTION!")
        print("=" * 60)
    else:
        print("\n❌ Failed to create mastermind user")
        sys.exit(1)