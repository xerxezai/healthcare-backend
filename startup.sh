#!/bin/sh
# EMERGENCY Railway deployment script - bypasses CustomUser issues

export DJANGO_SETTINGS_MODULE="backend.settings_emergency"
export PORT="${PORT:-8080}"

echo "🚨 EMERGENCY DEPLOYMENT: Starting with emergency settings"
echo "📋 Bypassing CustomUser model to avoid auth_group constraint errors"
echo "🚀 Starting Django on port $PORT"
echo "DATABASE_URL: ${DATABASE_URL:-'NOT SET'}"

# Start with emergency settings that bypass hospital app
python manage_emergency.py runserver 0.0.0.0:$PORT
import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.db import connection
try:
    connection.ensure_connection()
    print('Database connection successful')
    sys.exit(0)
except Exception as e:
    print(f'Database connection failed: {e}')
    sys.exit(1)
" 2>/dev/null; do
    timeout=$((timeout - 1))
    if [ $timeout -le 0 ]; then
        echo "Database connection timeout. Continuing anyway..."
        break
    fi
    echo "Waiting for database... ($timeout seconds remaining)"
    sleep 1
done

# Run migrations with better error handling
echo "Running migrations..."
python manage.py migrate --noinput || {
    echo "Migration failed, but continuing..."
}

# Load initial data if it exists
if [ -f "load/subscription_plans.json" ]; then
    echo "Loading subscription plans..."
    python manage.py loaddata load/subscription_plans.json || echo "Loaddata failed, continuing..."
fi

# Create superuser if it doesn't exist
echo "Creating superuser if needed..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
try:
    User = get_user_model()
    if not User.objects.filter(email='admin@healthcare.com').exists():
        User.objects.create_superuser(
            email='admin@healthcare.com',
            password='admin123',
            full_name='Administrator',
            role='admin'
        )
        print('Admin superuser created')
    else:
        print('Admin superuser already exists')
except Exception as e:
    print(f'User creation error: {e}')
" || echo "User creation failed, continuing..."

# Start Django server with better error handling
echo "Starting Django server on 0.0.0.0:${PORT}..."
exec python manage.py runserver "0.0.0.0:${PORT}" --noreload