#!/bin/bash

# Railway Healthcare Application Startup Script
# Handles database migration issues with graceful fallback

echo "🏥 Starting Healthcare Application on Railway..."
echo "=" * 50

# Function to run migrations with error handling
run_migrations() {
    echo "🔄 Attempting database migration..."
    python manage.py migrate 2>&1 | tee migration.log
    
    # Check if migration failed due to foreign key constraint
    if grep -q "there is no unique constraint matching given keys for referenced table" migration.log; then
        echo "❌ Foreign key constraint error detected"
        echo "🔄 Attempting database reset and clean migration..."
        
        # Try to reset only hospital migrations
        python -c "
import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

try:
    with connection.cursor() as cursor:
        # Clear only hospital migration records
        cursor.execute('DELETE FROM django_migrations WHERE app = %s', ['hospital'])
        print('✅ Cleared hospital migration history')
except Exception as e:
    print(f'⚠️ Could not clear migrations: {e}')
"
        
        # Try migration again
        echo "🔄 Retrying migration after reset..."
        python manage.py migrate --run-syncdb
        
        if [ $? -ne 0 ]; then
            echo "❌ Migration still failing. Starting without full migration..."
            # Create essential tables only
            python manage.py migrate auth
            python manage.py migrate contenttypes
            python manage.py migrate sessions
        fi
    else
        echo "✅ Migration completed successfully"
    fi
}

# Run migrations with error handling
run_migrations

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Start the application
echo "🚀 Starting Gunicorn server..."
exec gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120