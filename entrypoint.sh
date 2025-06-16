#!/bin/bash

# Exit on any error
set -e

echo "Starting Django application..."

# Wait a bit for any database to be ready (not needed for SQLite but good practice)
sleep 2

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist (optional)
echo "Checking for superuser..."
python manage.py shell -c "
from core.models import User
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123', role='superuser')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Starting server..."
exec "$@"