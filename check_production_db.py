#!/usr/bin/env python
"""Check production database migration status"""
import os
import sys
import django

# Set the production database URL
os.environ['DATABASE_URL'] = 'postgresql://postgres:HogFaJuzRvZXMXIfRTmSInWAxIenfYCG@ballast.proxy.rlwy.net:35095/railway'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

django.setup()

from django.core.management import call_command
from django.db import connection

print("Connecting to production database...")
print(f"Database: {connection.settings_dict['NAME']}")
print(f"Host: {connection.settings_dict['HOST']}")

# Check current migration status
print("\n=== Migration Status ===")
call_command('showmigrations', '--list')

# Check if there are pending migrations
print("\n=== Checking for pending migrations ===")
try:
    call_command('migrate', '--check')
    print("All migrations are applied!")
except SystemExit:
    print("There are unapplied migrations!")

# List tables in database
print("\n=== Database Tables ===")
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()
    for table in tables:
        print(f"  - {table[0]}")

# Check django_migrations table
print("\n=== Applied Migrations in Database ===")
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT app, name, applied 
        FROM django_migrations 
        WHERE app = 'hospital'
        ORDER BY id DESC
        LIMIT 20;
    """)
    migrations = cursor.fetchall()
    for mig in migrations:
        print(f"  {mig[0]}.{mig[1]} - Applied: {mig[2]}")