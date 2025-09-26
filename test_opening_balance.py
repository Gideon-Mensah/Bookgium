#!/usr/bin/env python
"""
Quick test script to verify opening balance calculation for revenue accounts
"""
import os
import sys
import django
from datetime import datetime, date

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')
django.setup()

from accounts.models import Account, JournalEntry, JournalEntryLine
from accounts.views import calculate_period_opening_balance
from decimal import Decimal

def test_revenue_opening_balance():
    """Test opening balance calculation for revenue accounts"""
    print("Testing revenue account opening balance calculation...")
    
    # Find a revenue account
    try:
        revenue_account = Account.objects.filter(account_type='income').first()
        if not revenue_account:
            print("No revenue/income accounts found in database")
            return
            
        print(f"Testing account: {revenue_account.code} - {revenue_account.name}")
        print(f"Account type: {revenue_account.account_type}")
        print(f"Current opening balance: {revenue_account.opening_balance or 0}")
        
        # Test opening balance calculation for current year
        current_year = date.today().year
        from_date = date(current_year, 1, 1)
        
        calculated_balance = calculate_period_opening_balance(revenue_account, from_date)
        print(f"Calculated opening balance for {from_date}: {calculated_balance}")
        
        # Check recent journal entries for this account
        recent_entries = JournalEntryLine.objects.filter(
            account=revenue_account,
            journal_entry__is_posted=True
        ).order_by('-journal_entry__date')[:5]
        
        print("\nRecent journal entries:")
        for entry in recent_entries:
            print(f"  {entry.journal_entry.date}: {entry.entry_type} ${entry.amount} - {entry.description or entry.journal_entry.description}")
            
        print(f"\nRevenue accounts should have:")
        print("- Credit balances (positive amounts shown in credit column)")
        print("- Opening balances calculated as: opening_balance + (credits - debits)")
        
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == '__main__':
    test_revenue_opening_balance()
