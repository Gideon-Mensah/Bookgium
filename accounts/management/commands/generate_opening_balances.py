from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, date

from accounts.models import Account, JournalEntry, JournalEntryLine


class Command(BaseCommand):
    help = 'Generate opening balances for accounts based on various methods'

    def add_arguments(self, parser):
        parser.add_argument(
            '--method',
            type=str,
            choices=['calculate', 'import', 'zero'],
            default='calculate',
            help='Method to generate opening balances: '
                 'calculate (from existing transactions), '
                 'import (from CSV file), '
                 'zero (set all to zero)'
        )
        
        parser.add_argument(
            '--cutoff-date',
            type=str,
            help='Cut-off date for calculating opening balances (YYYY-MM-DD). '
                 'Balances will be calculated up to this date.'
        )
        
        parser.add_argument(
            '--opening-date',
            type=str,
            help='Date to set as opening balance date (YYYY-MM-DD). '
                 'If not provided, uses cutoff date.'
        )
        
        parser.add_argument(
            '--csv-file',
            type=str,
            help='Path to CSV file for importing opening balances. '
                 'Format: account_code,opening_balance'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually updating accounts'
        )
        
        parser.add_argument(
            '--accounts',
            type=str,
            nargs='*',
            help='Specific account codes to process. If not provided, processes all accounts.'
        )
        
        parser.add_argument(
            '--create-journal-entry',
            action='store_true',
            help='Create a journal entry for the opening balances (for calculate method only)'
        )

    def handle(self, *args, **options):
        method = options['method']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        try:
            if method == 'calculate':
                self.calculate_opening_balances(options)
            elif method == 'import':
                self.import_opening_balances(options)
            elif method == 'zero':
                self.zero_opening_balances(options)
        except Exception as e:
            raise CommandError(f'Error generating opening balances: {str(e)}')

    def calculate_opening_balances(self, options):
        """Calculate opening balances from existing journal entries"""
        cutoff_date_str = options.get('cutoff_date')
        if not cutoff_date_str:
            raise CommandError('--cutoff-date is required for calculate method')
        
        try:
            cutoff_date = datetime.strptime(cutoff_date_str, '%Y-%m-%d').date()
        except ValueError:
            raise CommandError('Invalid cutoff date format. Use YYYY-MM-DD')
        
        opening_date = cutoff_date
        if options.get('opening_date'):
            try:
                opening_date = datetime.strptime(options['opening_date'], '%Y-%m-%d').date()
            except ValueError:
                raise CommandError('Invalid opening date format. Use YYYY-MM-DD')
        
        # Get accounts to process
        if options.get('accounts'):
            accounts = Account.objects.filter(
                code__in=options['accounts'], 
                is_active=True
            )
            if not accounts.exists():
                raise CommandError('No accounts found with the specified codes')
        else:
            accounts = Account.objects.filter(is_active=True)
        
        self.stdout.write(
            f'Calculating opening balances up to {cutoff_date} '
            f'for {accounts.count()} accounts...'
        )
        
        updated_accounts = []
        journal_entries = []  # For creating opening balance journal entry
        
        with transaction.atomic():
            for account in accounts:
                # Calculate balance up to cutoff date
                journal_lines = JournalEntryLine.objects.filter(
                    account=account,
                    journal_entry__date__lte=cutoff_date,
                    journal_entry__is_posted=True
                )
                
                credits = journal_lines.filter(entry_type='credit').aggregate(
                    total=Sum('amount')
                )['total'] or Decimal('0')
                
                debits = journal_lines.filter(entry_type='debit').aggregate(
                    total=Sum('amount')
                )['total'] or Decimal('0')
                
                # Calculate balance based on account type
                if account.account_type in ['asset', 'expense']:
                    calculated_balance = debits - credits
                else:
                    calculated_balance = credits - debits
                
                if calculated_balance != account.opening_balance or not account.opening_balance_date:
                    if not options['dry_run']:
                        account.opening_balance = calculated_balance
                        account.opening_balance_date = opening_date
                        account.save()
                    
                    updated_accounts.append({
                        'account': account,
                        'old_balance': account.opening_balance,
                        'new_balance': calculated_balance,
                    })
                    
                    # Prepare for journal entry creation
                    if options.get('create_journal_entry') and calculated_balance != 0:
                        journal_entries.append({
                            'account': account,
                            'balance': calculated_balance
                        })
        
        # Create opening balance journal entry if requested
        if options.get('create_journal_entry') and journal_entries and not options['dry_run']:
            self.create_opening_balance_journal_entry(journal_entries, opening_date)
        
        # Report results
        self.stdout.write(
            self.style.SUCCESS(
                f'{"Would update" if options["dry_run"] else "Updated"} '
                f'{len(updated_accounts)} accounts:'
            )
        )
        
        for item in updated_accounts:
            account = item['account']
            self.stdout.write(
                f'  {account.code} - {account.name}: '
                f'{item["old_balance"]} → {item["new_balance"]}'
            )

    def import_opening_balances(self, options):
        """Import opening balances from CSV file"""
        csv_file = options.get('csv_file')
        if not csv_file:
            raise CommandError('--csv-file is required for import method')
        
        opening_date = date.today()
        if options.get('opening_date'):
            try:
                opening_date = datetime.strptime(options['opening_date'], '%Y-%m-%d').date()
            except ValueError:
                raise CommandError('Invalid opening date format. Use YYYY-MM-DD')
        
        import csv
        import os
        
        if not os.path.exists(csv_file):
            raise CommandError(f'CSV file not found: {csv_file}')
        
        updated_accounts = []
        
        try:
            with open(csv_file, 'r') as file:
                reader = csv.DictReader(file)
                expected_columns = ['account_code', 'opening_balance']
                
                if not all(col in reader.fieldnames for col in expected_columns):
                    raise CommandError(
                        f'CSV file must contain columns: {", ".join(expected_columns)}'
                    )
                
                with transaction.atomic():
                    for row in reader:
                        account_code = row['account_code'].strip()
                        try:
                            opening_balance = Decimal(row['opening_balance'].strip() or '0')
                        except (ValueError, TypeError):
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Invalid balance for account {account_code}: '
                                    f'{row["opening_balance"]}. Skipping.'
                                )
                            )
                            continue
                        
                        try:
                            account = Account.objects.get(code=account_code, is_active=True)
                            
                            if not options['dry_run']:
                                account.opening_balance = opening_balance
                                account.opening_balance_date = opening_date
                                account.save()
                            
                            updated_accounts.append({
                                'account': account,
                                'old_balance': account.opening_balance,
                                'new_balance': opening_balance,
                            })
                            
                        except Account.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Account with code {account_code} not found. Skipping.'
                                )
                            )
                            continue
        
        except Exception as e:
            raise CommandError(f'Error reading CSV file: {str(e)}')
        
        # Report results
        self.stdout.write(
            self.style.SUCCESS(
                f'{"Would update" if options["dry_run"] else "Updated"} '
                f'{len(updated_accounts)} accounts from CSV:'
            )
        )
        
        for item in updated_accounts:
            account = item['account']
            self.stdout.write(
                f'  {account.code} - {account.name}: '
                f'{item["old_balance"]} → {item["new_balance"]}'
            )

    def zero_opening_balances(self, options):
        """Set all opening balances to zero"""
        opening_date = date.today()
        if options.get('opening_date'):
            try:
                opening_date = datetime.strptime(options['opening_date'], '%Y-%m-%d').date()
            except ValueError:
                raise CommandError('Invalid opening date format. Use YYYY-MM-DD')
        
        # Get accounts to process
        if options.get('accounts'):
            accounts = Account.objects.filter(
                code__in=options['accounts'], 
                is_active=True
            )
            if not accounts.exists():
                raise CommandError('No accounts found with the specified codes')
        else:
            accounts = Account.objects.filter(is_active=True)
        
        updated_count = 0
        
        with transaction.atomic():
            for account in accounts:
                if account.opening_balance != 0:
                    if not options['dry_run']:
                        account.opening_balance = Decimal('0.00')
                        account.opening_balance_date = opening_date
                        account.save()
                    
                    updated_count += 1
                    self.stdout.write(
                        f'  {account.code} - {account.name}: '
                        f'{account.opening_balance} → 0.00'
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'{"Would update" if options["dry_run"] else "Updated"} '
                f'{updated_count} accounts to zero balance.'
            )
        )

    def create_opening_balance_journal_entry(self, journal_entries, opening_date):
        """Create a journal entry for opening balances"""
        
        # Create the journal entry
        journal_entry = JournalEntry.objects.create(
            date=opening_date,
            description='Opening Balances',
            reference='OB-' + opening_date.strftime('%Y%m%d'),
            notes='Automatically generated opening balance entries',
            is_posted=False  # Don't post automatically
        )
        
        # Create journal entry lines
        for item in journal_entries:
            account = item['account']
            balance = item['balance']
            
            if balance > 0:
                # Positive balance
                if account.account_type in ['asset', 'expense']:
                    # Asset/Expense: Positive balance = Debit
                    entry_type = 'debit'
                else:
                    # Liability/Equity/Income: Positive balance = Credit
                    entry_type = 'credit'
            else:
                # Negative balance
                if account.account_type in ['asset', 'expense']:
                    # Asset/Expense: Negative balance = Credit
                    entry_type = 'credit'
                else:
                    # Liability/Equity/Income: Negative balance = Debit
                    entry_type = 'debit'
            
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                account=account,
                entry_type=entry_type,
                amount=abs(balance),
                description=f'Opening balance for {account.name}'
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Created opening balance journal entry: {journal_entry.reference}'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                'Journal entry created but not posted. Review and post manually.'
            )
        )
