#!/usr/bin/env python3
"""
SIMPLE FIX: Just create the users table - no complex migration logic
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django_tenants.utils import schema_context
from django.contrib.auth import get_user_model
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Simple fix to create users table'

    def handle(self, *args, **options):
        try:
            # Just migrate users in the tenant - simple and direct
            self.stdout.write("Creating users tables in bookgium tenant...")
            call_command('migrate_schemas', '--tenant', '--schema=bookgium', 'users')
            
            # Create superuser
            with schema_context('bookgium'):
                User = get_user_model()
                user, created = User.objects.get_or_create(
                    username='geolumia67',
                    defaults={
                        'email': 'admin@bookgium.com',
                        'is_staff': True,
                        'is_superuser': True,
                    }
                )
                user.set_password('Metrotv111l2@')
                user.save()
                
                self.stdout.write(f"✓ User ready: geolumia67")
                
        except Exception as e:
            self.stdout.write(f"Error: {e}")
            # Try alternative approach
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO bookgium;")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users_customuser (
                        id SERIAL PRIMARY KEY,
                        password VARCHAR(128) NOT NULL,
                        last_login TIMESTAMP WITH TIME ZONE,
                        is_superuser BOOLEAN NOT NULL,
                        username VARCHAR(150) UNIQUE NOT NULL,
                        first_name VARCHAR(150) NOT NULL,
                        last_name VARCHAR(150) NOT NULL,
                        email VARCHAR(254) NOT NULL,
                        is_staff BOOLEAN NOT NULL,
                        is_active BOOLEAN NOT NULL,
                        date_joined TIMESTAMP WITH TIME ZONE NOT NULL,
                        role VARCHAR(50) NOT NULL,
                        preferred_currency VARCHAR(3) NOT NULL
                    );
                """)
                self.stdout.write("✓ Created users table manually")
