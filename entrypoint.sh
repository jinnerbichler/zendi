#!/bin/bash

# Apply database migrations
echo "Apply database migrations"
python manage.py migrate

# Start server
echo "Starting Django"
python manage.py runserver 0.0.0.0:8000 --noreload --insecure