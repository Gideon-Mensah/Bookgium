from django.core.management.base import BaseCommand
from django.conf import settings
import os
import re

class Command(BaseCommand):
    help = 'Change the default reporting currency'

    def add_arguments(self, parser):
        parser.add_argument('currency', type=str, help='Currency code (e.g., USD, EUR, GBP)')

    def handle(self, *args, **options):
        currency = options['currency'].upper()
        
        # Check if currency is supported
        supported_currencies = getattr(settings, 'CURRENCY_SYMBOLS', {})
        if currency not in supported_currencies:
            self.stdout.write(
                self.style.ERROR(f'Currency {currency} is not supported.')
            )
            self.stdout.write('Supported currencies:')
            for code, symbol in supported_currencies.items():
                self.stdout.write(f'  {code}: {symbol}')
            return

        # Update settings.py
        settings_path = os.path.join(settings.BASE_DIR, 'bookgium', 'settings.py')
        
        try:
            with open(settings_path, 'r') as file:
                content = file.read()
            
            # Replace the DEFAULT_CURRENCY value
            pattern = r"DEFAULT_CURRENCY\s*=\s*['\"][^'\"]*['\"]"
            replacement = f"DEFAULT_CURRENCY = '{currency}'"
            new_content = re.sub(pattern, replacement, content)
            
            with open(settings_path, 'w') as file:
                file.write(new_content)
            
            symbol = supported_currencies[currency]
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully changed reporting currency to {currency} ({symbol})'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    'Please restart your Django server for changes to take effect.'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error updating settings: {str(e)}')
            )
