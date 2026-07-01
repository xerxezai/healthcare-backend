#!/usr/bin/env python3
"""
Emergency Railway Database Reset Script
This script bypasses the auth_group constraint issue by using Django's default User model temporarily
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def setup_django():
    """Initialize Django settings"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    django.setup()

def reset_database_completely():
    """
    Complete database reset for Railway PostgreSQL
    """
    print("🚨 EMERGENCY DATABASE RESET FOR RAILWAY")
    print("=" * 50)
    
    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            print("🔄 Dropping ALL tables...")
            
            # Get all table names
            cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            
            # Drop all tables including django_migrations
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                print(f"  ✅ Dropped: {table}")
            
            print("✅ All tables dropped successfully!")
            
    except Exception as e:
        print(f"❌ Database reset failed: {str(e)}")
        return False
    
    return True

def run_fresh_setup():
    """
    Run fresh Django setup
    """
    print("🚀 Running fresh Django setup...")
    
    try:
        # Run migrations for core Django apps first
        print("📋 Creating Django core tables...")
        execute_from_command_line(['manage.py', 'migrate', 'contenttypes'])
        execute_from_command_line(['manage.py', 'migrate', 'auth'])
        execute_from_command_line(['manage.py', 'migrate', 'sessions'])
        execute_from_command_line(['manage.py', 'migrate', 'admin'])
        
        # Now migrate all other apps
        print("📋 Migrating application tables...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        print("✅ Fresh setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Fresh setup failed: {str(e)}")
        return False

def main():
    """
    Main execution
    """
    print("🏥 Railway Emergency Database Reset")
    print("This will completely reset the database and bypass migration issues")
    print()
    
    # Setup Django
    setup_django()
    
    # Step 1: Complete database reset
    if not reset_database_completely():
        print("❌ Database reset failed. Exiting.")
        sys.exit(1)
    
    # Step 2: Fresh setup
    if not run_fresh_setup():
        print("❌ Fresh setup failed. Exiting.")
        sys.exit(1)
    
    print("\n🎉 Emergency database reset completed successfully!")
    print("Railway should now start without foreign key constraint errors.")

if __name__ == "__main__":
    main()