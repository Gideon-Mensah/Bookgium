#!/usr/bin/env python
"""
Render deployment build script for Bookgium Django multi-tenant application.
This script is automatically executed by Render during deployment.
"""
import os
import subprocess
import sys

def run_command(command):
    """Execute a command and handle errors."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {command}")
        print(f"Error output: {result.stderr}")
        sys.exit(1)
    return result.stdout

def main():
    """Main build process for Render deployment."""
    print("=== Starting Render build process for Multi-Tenant Bookgium ===")
    
    # Install Python dependencies
    print("\n1. Installing Python dependencies...")
    run_command("pip install -r requirements.txt")
    
    # Collect static files
    print("\n2. Collecting static files...")
    run_command("python manage.py collectstatic --noinput")
    
    # Run database migrations for shared apps (creates public schema)
    print("\n3. Running shared schema migrations...")
    run_command("python manage.py migrate_schemas --shared")
    
    # Run database migrations for all schemas
    print("\n4. Running tenant schema migrations...")
    run_command("python manage.py migrate_schemas")
    
    # Initialize audit settings (if needed)
    print("\n5. Initializing audit settings...")
    try:
        run_command("python manage.py init_audit_settings")
    except:
        print("Audit settings initialization skipped (may already exist)")
    
    print("\n6. Multi-tenant build process completed successfully!")
    print("=== Render build process finished ===")
    print("\nNext steps:")
    print("1. Create your first tenant: python manage.py create_tenant 'Client Name' domain.com")
    print("2. Create admin user: python manage.py create_tenant_superuser schema_name")

if __name__ == "__main__":
    main()
