from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Set preferred currency for a specific user or all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username to update currency for (if not provided, will list all users)'
        )
        parser.add_argument(
            '--currency',
            type=str,
            choices=['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY', 'CHF', 'CNY', 'INR', 'BRL', 'ZAR', 'MXN', 'SGD', 'HKD', 'NZD'],
            help='Currency code to set'
        )
        parser.add_argument(
            '--all-users',
            action='store_true',
            help='Set currency for all users (requires --currency)'
        )

    def handle(self, *args, **options):
        if options['all_users'] and options['currency']:
            # Set currency for all users
            users = User.objects.all()
            for user in users:
                old_currency = user.preferred_currency
                user.preferred_currency = options['currency']
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated {user.username}: {old_currency} → {options["currency"]}')
                )
            self.stdout.write(self.style.SUCCESS(f'All users updated to {options["currency"]}'))
            
        elif options['user'] and options['currency']:
            # Set currency for specific user
            try:
                user = User.objects.get(username=options['user'])
                old_currency = user.preferred_currency
                user.preferred_currency = options['currency']
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated {user.username}: {old_currency} → {options["currency"]}')
                )
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User "{options["user"]}" not found'))
                
        else:
            # List all users and their currencies
            self.stdout.write('Current user currencies:')
            self.stdout.write('-' * 40)
            users = User.objects.all()
            for user in users:
                self.stdout.write(f'{user.username:20} → {user.preferred_currency}')
            
            self.stdout.write('\nUsage examples:')
            self.stdout.write('  python manage.py update_user_currency --user john --currency EUR')
            self.stdout.write('  python manage.py update_user_currency --all-users --currency USD')
