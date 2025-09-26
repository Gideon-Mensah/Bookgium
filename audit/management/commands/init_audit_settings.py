from django.core.management.base import BaseCommand
from audit.models import AuditSettings


class Command(BaseCommand):
    help = 'Initialize audit settings with default values'

    def handle(self, *args, **options):
        settings, created = AuditSettings.objects.get_or_create(pk=1)
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Successfully created default audit settings.')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Audit settings already exist.')
            )
        
        # Display current settings
        self.stdout.write('\nCurrent Audit Settings:')
        self.stdout.write(f'  Audit Accounts: {settings.audit_accounts}')
        self.stdout.write(f'  Audit Journal Entries: {settings.audit_journal_entries}')
        self.stdout.write(f'  Audit Transactions: {settings.audit_transactions}')
        self.stdout.write(f'  Audit Users: {settings.audit_users}')
        self.stdout.write(f'  Audit Clients: {settings.audit_clients}')
        self.stdout.write(f'  Audit Invoices: {settings.audit_invoices}')
        self.stdout.write(f'  Retention Days: {settings.retention_days}')
        self.stdout.write(f'  Audit Create: {settings.audit_create}')
        self.stdout.write(f'  Audit Update: {settings.audit_update}')
        self.stdout.write(f'  Audit Delete: {settings.audit_delete}')
        self.stdout.write(f'  Audit Login: {settings.audit_login}')
