from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from clients.models import Client

class Command(BaseCommand):
    help = 'Create sample clients with different currencies for testing'

    def handle(self, *args, **options):
        # Sample clients with different currencies
        sample_clients = [
            {
                'name': 'TechCorp USA',
                'slug': 'techcorp-usa',
                'email': 'contact@techcorp.com',
                'currency': 'USD',
                'monthly_fee': 99.00,
                'country': 'United States',
                'city': 'New York'
            },
            {
                'name': 'Digital Solutions EU',
                'slug': 'digital-solutions-eu',
                'email': 'info@digitalsolutions.eu',
                'currency': 'EUR',
                'monthly_fee': 89.00,
                'country': 'Germany',
                'city': 'Berlin'
            },
            {
                'name': 'Innovation Labs UK',
                'slug': 'innovation-labs-uk',
                'email': 'hello@innovationlabs.co.uk',
                'currency': 'GBP',
                'monthly_fee': 79.00,
                'country': 'United Kingdom',
                'city': 'London'
            },
            {
                'name': 'StartupHub Japan',
                'slug': 'startuphub-japan',
                'email': 'contact@startuphub.jp',
                'currency': 'JPY',
                'monthly_fee': 9800.00,
                'country': 'Japan',
                'city': 'Tokyo'
            },
            {
                'name': 'Digital Agency Australia',
                'slug': 'digital-agency-au',
                'email': 'hello@digitalagency.com.au',
                'currency': 'AUD',
                'monthly_fee': 129.00,
                'country': 'Australia',
                'city': 'Sydney'
            }
        ]

        created_count = 0
        for client_data in sample_clients:
            client, created = Client.objects.get_or_create(
                slug=client_data['slug'],
                defaults={
                    'name': client_data['name'],
                    'email': client_data['email'],
                    'currency': client_data['currency'],
                    'monthly_fee': client_data['monthly_fee'],
                    'country': client_data['country'],
                    'city': client_data['city'],
                    'paid_until': timezone.now().date() + timedelta(days=30),
                    'trial_ends': timezone.now().date() + timedelta(days=30),
                    'subscription_status': 'active',
                    'plan_type': 'professional',
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created client: {client.name} ({client.currency})')
                )
            else:
                # Update currency if client exists
                client.currency = client_data['currency']
                client.monthly_fee = client_data['monthly_fee']
                client.save()
                self.stdout.write(
                    self.style.WARNING(f'Updated client: {client.name} ({client.currency})')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\nSample clients setup complete! Created {created_count} new clients.')
        )
