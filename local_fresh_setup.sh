#!/bin/bash
# Local development script to test fresh database setup

echo "=== LOCAL FRESH SETUP TEST ==="

# Configure Python environment
export DATABASE_URL="postgres://postgres:password@localhost:5432/bookgium_db"

echo "1. Installing dependencies..."
pip install -r requirements.txt

echo "2. Setting up fresh database..."
./manage.py fresh_setup --confirm-reset

echo "3. Collecting static files..."
./manage.py collectstatic --noinput

echo "=== LOCAL SETUP COMPLETED ==="
echo "Test the application locally:"
echo "1. Run: ./manage.py runserver"
echo "2. Visit: http://127.0.0.1:8000/admin/login/"
echo "3. Login: geolumia67 / Metrotv111l2@"
