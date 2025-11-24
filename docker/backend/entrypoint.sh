#!/bin/bash

echo "Waiting for PostgreSQL..."

# Ждем, пока PostgreSQL станет доступен
if [ "$DB_ENGINE" = "postgresql" ]; then
    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 1
    done
    echo "PostgreSQL is up!"
fi

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || true

echo "Creating superuser if not exists..."
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model;
User = get_user_model();
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@victorinka.com')
nickname = os.environ.get('DJANGO_SUPERUSER_NICKNAME', 'admin')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(
        email=email,
        nickname=nickname,
        password=password
    );
    print(f'Superuser created: {email}')
else:
    print('Superuser already exists')
" || true

echo "Starting Django development server..."
python manage.py runserver 0.0.0.0:8000

