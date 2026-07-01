#!/usr/bin/env python
"""
Emergency Railway Startup Script
This script uses alternative settings to bypass CustomUser migration issues
"""
import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line

def main():
    """Run administrative tasks with emergency settings."""
    # Use emergency settings that bypass CustomUser model
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings_emergency')
    
    print("🚨 EMERGENCY STARTUP: Using alternative settings without CustomUser model")
    print("📋 This bypasses migration issues to get the app running")
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Skip migrations for runserver command (they cause issues)
    if len(sys.argv) > 1 and 'runserver' in sys.argv:
        print("🚀 Starting emergency server without migrations...")
        print("📋 Emergency mode: Hospital features disabled, other modules available")
        print("🔗 Admin panel available at /admin/ (may need manual DB setup)")
    else:
        # Only run migrations for other commands
        print("🔄 Running migrations with emergency settings...")
        try:
            execute_from_command_line(['manage.py', 'migrate', '--verbosity=0'])
            print("✅ Emergency migrations completed successfully")
        except Exception as e:
            print(f"⚠️ Migration warning: {e}")
            print("🔧 Continuing anyway - some features may be limited")
    
        # Create superuser if needed (using default User model) - only if not runserver
        print("👤 Checking for admin users...")
        try:
            django.setup()
            from django.contrib.auth.models import User
            if not User.objects.filter(is_superuser=True).exists():
                print("🔐 Creating emergency admin user...")
                User.objects.create_superuser(
                    username='admin',
                    email='admin@healthcare.com',
                    password='admin123'
                )
                print("✅ Emergency admin created: admin/admin123")
            else:
                print("✅ Admin users already exist")
        except Exception as e:
            print(f"⚠️ Admin setup warning: {e}")
            print("🔧 Run 'python manage_emergency.py migrate' manually if needed")
    
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()