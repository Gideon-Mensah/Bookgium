from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from audit.models import AuditLog, AuditSettings


class Command(BaseCommand):
    help = 'Clean up old audit logs based on retention settings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            help='Number of days to keep (overrides settings)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        settings = AuditSettings.get_settings()
        days = options.get('days') or settings.retention_days
        
        if days == 0:
            self.stdout.write(
                self.style.WARNING('Retention is set to 0 (keep forever). No logs will be deleted.')
            )
            return
        
        cutoff_date = timezone.now() - timedelta(days=days)
        old_logs = AuditLog.objects.filter(timestamp__lt=cutoff_date)
        count = old_logs.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(f'No audit logs older than {days} days found.')
            )
            return
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would delete {count} audit logs older than {days} days.')
            )
        else:
            old_logs.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {count} audit logs older than {days} days.')
            )
