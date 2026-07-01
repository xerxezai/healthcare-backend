#!/usr/bin/env python
"""Fix duplicate 0013 migrations in production database"""
import os
import sys
import django

# Set the production database URL
os.environ['DATABASE_URL'] = 'postgresql://postgres:HogFaJuzRvZXMXIfRTmSInWAxIenfYCG@ballast.proxy.rlwy.net:35095/railway'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

django.setup()

from django.db import connection

print("Connecting to production database...")

# Remove duplicate 0013 migrations except the latest one
with connection.cursor() as cursor:
    print("\n=== Removing duplicate 0013 migrations ===")
    
    # Delete the old conflicting 0013 migrations
    cursor.execute("""
        DELETE FROM django_migrations 
        WHERE app = 'hospital' 
        AND name IN (
            '0013_add_features_merged',
            '0013_add_healthcare_management_features_simple',
            '0013_rename_notification_logs_type_idx_notificatio_notific_0cc56e_idx_and_more'
        );
    """)
    
    deleted_count = cursor.rowcount
    print(f"Deleted {deleted_count} duplicate migrations")
    
    # Verify current state
    cursor.execute("""
        SELECT name, applied 
        FROM django_migrations 
        WHERE app = 'hospital' AND name LIKE '0013%'
        ORDER BY applied DESC;
    """)
    
    remaining = cursor.fetchall()
    print("\n=== Remaining 0013 migrations ===")
    for mig in remaining:
        print(f"  {mig[0]} - Applied: {mig[1]}")

print("\nMigration cleanup complete!")