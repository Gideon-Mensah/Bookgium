from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Account, JournalEntry, JournalEntryLine
from audit.models import AuditLog
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Demonstrate the audit logging system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Audit Logging System Demo ===\n'))
        
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='demo_user',
            defaults={
                'email': 'demo@example.com',
                'first_name': 'Demo',
                'last_name': 'User',
                'role': 'admin'
            }
        )
        
        if created:
            user.set_password('demo123')
            user.save()
            self.stdout.write('Created demo user: demo_user (password: demo123)')
        
        # Show initial audit log count
        initial_count = AuditLog.objects.count()
        self.stdout.write(f'Initial audit log count: {initial_count}')
        
        # Create a test account (this should be audited)
        self.stdout.write('\n1. Creating a new account...')
        account = Account.objects.create(
            code='1001',
            name='Demo Cash Account',
            account_type='asset',
            description='Demo account for audit testing',
            created_by=user
        )
        self.stdout.write(f'Created account: {account}')
        
        # Update the account (this should be audited)
        self.stdout.write('\n2. Updating the account...')
        account.description = 'Updated description for audit demo'
        account.save()
        self.stdout.write('Updated account description')
        
        # Create a journal entry (this should be audited)
        self.stdout.write('\n3. Creating a journal entry...')
        journal_entry = JournalEntry.objects.create(
            date='2025-09-22',
            description='Demo journal entry for audit testing',
            reference='DEMO-001',
            created_by=user
        )
        self.stdout.write(f'Created journal entry: {journal_entry}')
        
        # Show final audit log count
        final_count = AuditLog.objects.count()
        self.stdout.write(f'\nFinal audit log count: {final_count}')
        self.stdout.write(f'New audit logs created: {final_count - initial_count}')
        
        # Show recent audit logs
        self.stdout.write('\n=== Recent Audit Logs ===')
        recent_logs = AuditLog.objects.order_by('-timestamp')[:5]
        
        for log in recent_logs:
            self.stdout.write(f'• {log.timestamp.strftime("%Y-%m-%d %H:%M:%S")} - '
                            f'{log.user.username if log.user else "System"} - '
                            f'{log.get_action_display()} - {log.object_repr}')
            if log.changes:
                for field, change in log.changes.items():
                    if isinstance(change, dict) and 'old' in change and 'new' in change:
                        self.stdout.write(f'    {field}: "{change["old"]}" → "{change["new"]}"')
        
        self.stdout.write(self.style.SUCCESS('\n=== Demo Complete ==='))
        self.stdout.write('You can now:')
        self.stdout.write('1. Visit http://127.0.0.1:8001/audit/ to view the audit dashboard')
        self.stdout.write('2. Login with demo_user / demo123')
        self.stdout.write('3. Explore the audit logs and user sessions')
