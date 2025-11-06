#!/bin/bash

echo "Waiting for dependencies..."
sleep 2

echo "Running migrations..."
python manage.py migrate

echo "Starting Django development server..."
python manage.py runserver 0.0.0.0:8000

