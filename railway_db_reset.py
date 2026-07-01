#!/usr/bin/env python3
"""
Railway Database Reset Script for Healthcare Application
This script handles the database migration reset for Railway deployment
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.db import connection
from django.conf import settings

def reset_railway_database():
    """
    Reset Railway PostgreSQL database for clean migration
    """
    print("🔄 Starting Railway Database Reset...")
    
    # Set up Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    django.setup()
    
    try:
        # Drop all tables except django_migrations
        with connection.cursor() as cursor:
            print("📋 Dropping existing tables...")
            
            # Get all table names except system tables
            cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename != 'django_migrations'
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            
            # Drop tables with CASCADE to handle foreign keys
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                print(f"  ✅ Dropped table: {table}")
            
            # Clear migration history for hospital app only
            cursor.execute("""
                DELETE FROM django_migrations 
                WHERE app = 'hospital'
            """)
            print("  ✅ Cleared hospital migration history")
            
        print("✅ Database reset completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database reset failed: {str(e)}")
        return False

def run_fresh_migrations():
    """
    Run migrations after database reset
    """
    print("🚀 Running fresh migrations...")
    
    try:
        # Run migrations
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Migrations completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

def main():
    """
    Main execution function
    """
    print("🏥 Healthcare Railway Database Reset Tool")
    print("=" * 50)
    
    # Check if this is Railway environment
    if not os.environ.get('RAILWAY_ENVIRONMENT'):
        print("⚠️  Warning: Not in Railway environment")
        print("   This script is designed for Railway PostgreSQL")
        
        response = input("   Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("❌ Aborted by user")
            sys.exit(1)
    
    # Step 1: Reset database
    if not reset_railway_database():
        print("❌ Database reset failed. Aborting.")
        sys.exit(1)
    
    # Step 2: Run fresh migrations  
    if not run_fresh_migrations():
        print("❌ Migrations failed. Check logs.")
        sys.exit(1)
    
    print("\n🎉 Railway database reset and migration completed successfully!")
    print("🔗 Your Healthcare application should now start without foreign key errors")

if __name__ == "__main__":
    main()