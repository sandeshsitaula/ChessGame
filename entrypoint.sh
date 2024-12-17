#!/bin/bash

echo "Starting Django server..."
python manage.py makemigrations
python manage.py migrate

# Start server with debug output
exec python manage.py runserver 0.0.0.0:80 2>&1

# The exec is important - it replaces the shell process with Django
# 2>&1 redirects stderr to stdout

