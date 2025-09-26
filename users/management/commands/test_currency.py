from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.utils import get_currency_symbol, get_user_currency

User = get_user_model()

class Command(BaseCommand):
    help = 'Test currency system to verify it works correctly'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Currency System Test ==='))
        
        users = User.objects.all()
        
        for user in users:
            self.stdout.write(f'\nUser: {user.username}')
            self.stdout.write(f'  Database preferred_currency: {user.preferred_currency}')
            self.stdout.write(f'  get_user_currency(): {get_user_currency(user)}')
            self.stdout.write(f'  get_currency_symbol(): {get_currency_symbol(user=user)}')
            
        self.stdout.write(self.style.SUCCESS('\n=== Currency System Test Complete ==='))
        self.stdout.write('If all users show their correct preferred currency and symbol, the system is working correctly.')
        self.stdout.write('If users are seeing the wrong currency, it may be a browser cache issue.')
        self.stdout.write('Ask users to:')
        self.stdout.write('1. Clear their browser cache')
        self.stdout.write('2. Log out and log back in')
        self.stdout.write('3. Try an incognito/private browser window')
