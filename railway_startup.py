#!/usr/bin/env python3
"""
Railway Startup Script for Healthcare Application
Handles database migration with error recovery
"""

import os
import sys
import subprocess
import django
from django.core.management import execute_from_command_line

def setup_django():
    """Initialize Django settings"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    django.setup()

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ {description} error: {str(e)}")
        return False

def clear_hospital_migrations():
    """Clear only hospital app migrations from database"""
    print("🔄 Clearing hospital migration history...")
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM django_migrations WHERE app = 'hospital'")
            print("✅ Hospital migration history cleared")
        return True
    except Exception as e:
        print(f"⚠️ Could not clear migrations: {e}")
        return False

def main():
    """Main startup sequence"""
    print("🏥 Healthcare Application Startup")
    print("=" * 40)
    
    # Setup Django
    setup_django()
    
    # Try normal migration first
    print("🔄 Attempting database migration...")
    migrate_cmd = f"{sys.executable} manage.py migrate"
    result = subprocess.run(migrate_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        if "there is no unique constraint matching given keys" in result.stderr:
            print("❌ Foreign key constraint error detected")
            print("🔄 Applying database fix...")
            
            # Clear hospital migrations and retry
            clear_hospital_migrations()
            
            # Run syncdb for problem apps
            print("🔄 Running syncdb for core apps...")
            run_command(f"{sys.executable} manage.py migrate auth", "Auth migration")
            run_command(f"{sys.executable} manage.py migrate contenttypes", "ContentTypes migration")
            run_command(f"{sys.executable} manage.py migrate sessions", "Sessions migration")
            
            # Try hospital migration again
            print("🔄 Retrying hospital migration...")
            result = subprocess.run(f"{sys.executable} manage.py migrate hospital", shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                print("⚠️ Hospital migration still failing, continuing with other apps...")
                run_command(f"{sys.executable} manage.py migrate --run-syncdb", "Syncdb fallback")
        else:
            print("❌ Migration failed with other error:")
            print(result.stderr)
    else:
        print("✅ Migration completed successfully")
    
    # Collect static files
    run_command(f"{sys.executable} manage.py collectstatic --noinput", "Static files collection")
    
    # Start the server
    port = os.environ.get('PORT', '8000')
    print(f"🚀 Starting server on port {port}...")
    
    gunicorn_cmd = f"gunicorn backend.wsgi:application --bind 0.0.0.0:{port} --workers 2 --timeout 120"
    os.execvp("gunicorn", gunicorn_cmd.split())

if __name__ == "__main__":
    main()