#!/bin/bash

# Exit on any error
set -e

echo "========================================="
echo "Starting Django DMP Application"
echo "========================================="

# Function to wait for database (if using PostgreSQL in future)
wait_for_db() {
    echo "Waiting for database to be ready..."
    python << END
import sys
import time
import os

# For SQLite, just check if we can import Django
try:
    import django
    django.setup()
    from django.db import connections
    from django.db.utils import OperationalError

    max_retries = 30
    retry_count = 0

    while retry_count < max_retries:
        try:
            db_conn = connections['default']
            db_conn.cursor()
            print("Database is ready!")
            sys.exit(0)
        except OperationalError as e:
            retry_count += 1
            print(f"Database unavailable, waiting... (attempt {retry_count}/{max_retries})")
            time.sleep(1)

    print("Could not connect to database!")
    sys.exit(1)

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
END
}

# Wait for database
wait_for_db

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Create default groups and permissions
echo "Setting up groups and permissions..."
python manage.py setup_groups || echo "Groups already set up"

# Create superuser if it doesn't exist (only in development or if AUTO_CREATE_SUPERUSER=true)
if [ "$AUTO_CREATE_SUPERUSER" = "true" ]; then
    echo "Checking for superuser..."
    python manage.py shell -c "
from core.models import User
import os

if not User.objects.filter(is_superuser=True).exists():
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

    User.objects.create_superuser(username, email, password)
    print(f'Superuser created: {username}/{password}')
    print('⚠️  IMPORTANT: Change the password immediately!')
else:
    print('Superuser already exists')
" 2>/dev/null || echo "Note: Superuser creation skipped or failed"
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Optional: Run system checks
echo "Running Django system checks..."
python manage.py check --deploy || echo "Warning: Some deployment checks failed"

echo "========================================="
echo "Django DMP is ready!"
echo "Starting Gunicorn server..."
echo "========================================="

# Execute the main command (Gunicorn)
exec "$@"