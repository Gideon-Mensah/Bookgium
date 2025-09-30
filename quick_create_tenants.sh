#!/bin/bash
# Quick tenant creation script matching the shell commands you provided

echo "=== Creating Tenants via Django Shell ==="

python manage.py shell -c "
from clients.models import Client, Domain

print('Creating tenants...')

# The public schema is usually created by migrations automatically
# But let's ensure our tenant exists

# Create the bookgium tenant schema  
try:
    tenant, created = Client.objects.get_or_create(
        schema_name='bookgium',
        defaults={
            'name': 'Bookgium',
            'email': 'admin@bookgium.com',
            'paid_until': '2025-12-31'
        }
    )
    print(f'Tenant: {\"Created\" if created else \"Already exists\"} - {tenant.name} (schema: {tenant.schema_name})')
except Exception as e:
    print(f'Error creating tenant: {e}')

# Create domain mapping
try:
    domain, created = Domain.objects.get_or_create(
        domain='bookgium.onrender.com',
        defaults={
            'tenant': tenant,
            'is_primary': True
        }
    )
    print(f'Domain: {\"Created\" if created else \"Already exists\"} - {domain.domain} -> {domain.tenant.schema_name}')
except Exception as e:
    print(f'Error creating domain: {e}')

# Verify setup
print('')
print('Current setup:')
for t in Client.objects.all():
    domains = [d.domain for d in Domain.objects.filter(tenant=t)]
    print(f'  Tenant: {t.schema_name} ({t.name}) - Domains: {domains}')
"

echo "=== Tenant creation complete ==="
