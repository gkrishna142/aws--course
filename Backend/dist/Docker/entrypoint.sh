#!/usr/bin/env bash
set -e

# Wait for DB to be ready
echo "Waiting for PostgreSQL..."
until nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  sleep 2
done

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput || true

echo "Starting Gunicorn..."
exec gunicorn edustream.wsgi:application --bind 0.0.0.0:8000 --workers 3
