#!/bin/sh
set -e

# Ensure the data directory exists for SQLite persistence
mkdir -p /app/data

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || true

# Start supervisor to manage both processes
echo "Starting services with supervisor..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
