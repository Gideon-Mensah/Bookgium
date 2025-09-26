#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/gideonowusu/Desktop/Learn Django/Bookgium')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')
django.setup()

from help_chat.models import KnowledgeBase, FAQ

print("Creating knowledge base entries...")

# Create some basic knowledge base entries
knowledge_entries = [
    {
        'title': 'Getting Started with Bookgium',
        'category': 'getting_started',
        'content': '''Welcome to Bookgium! This guide will help you get started with your accounting application.

**First Steps:**
1. Set up your company information in Settings
2. Configure your default currency
3. Create your Chart of Accounts
4. Add your first clients
5. Start recording transactions

**Navigation:**
- Use the sidebar menu to access different modules
- Dashboard provides an overview of your financial data
- Reports section contains all your financial statements''',
        'keywords': 'getting started, setup, navigation, first time, tutorial'
    },
    {
        'title': 'Understanding Chart of Accounts',
        'category': 'accounts',
        'content': '''The Chart of Accounts is the foundation of your accounting system.

**Account Types:**
- Assets: Things your business owns
- Liabilities: Things your business owes
- Equity: Owner's investment
- Revenue: Income from sales
- Expenses: Costs of running business

**Creating Accounts:**
1. Go to 'Chart of Accounts'
2. Click 'Add New Account'
3. Select account type
4. Enter account name
5. Save the account''',
        'keywords': 'chart of accounts, accounts, assets, liabilities'
    },
    {
        'title': 'Recording Transactions',
        'category': 'transactions',
        'content': '''Learn how to record transactions in Bookgium.

**Steps:**
1. Navigate to 'Transactions' > 'New Transaction'
2. Select the transaction date
3. Choose accounts to debit and credit
4. Enter amounts (must balance)
5. Add description
6. Upload source documents
7. Save transaction

**Important:** Debits must equal credits!''',
        'keywords': 'transactions, recording, debit, credit, balance'
    }
]

for entry_data in knowledge_entries:
    kb, created = KnowledgeBase.objects.get_or_create(
        title=entry_data['title'],
        defaults=entry_data
    )
    if created:
        print(f"Created: {entry_data['title']}")
    else:
        print(f"Already exists: {entry_data['title']}")

# Create some FAQs
faq_entries = [
    {
        'question': 'How do I create my first account?',
        'category': 'accounts',
        'answer': '''To create your first account:
1. Go to "Chart of Accounts" in the main menu
2. Click "Add New Account"
3. Choose an account type
4. Enter account name
5. Click "Save"'''
    },
    {
        'question': 'What is the difference between a transaction and journal entry?',
        'category': 'transactions',
        'answer': '''Transactions are simple two-account entries.
Journal entries can involve multiple accounts and are used for complex entries.
Both must follow the rule: debits must equal credits.'''
    }
]

for faq_data in faq_entries:
    faq, created = FAQ.objects.get_or_create(
        question=faq_data['question'],
        defaults=faq_data
    )
    if created:
        print(f"Created FAQ: {faq_data['question']}")
    else:
        print(f"FAQ already exists: {faq_data['question']}")

print("\nKnowledge base entries:")
for entry in KnowledgeBase.objects.all():
    print(f"ID: {entry.id}, Title: {entry.title}")

print("Done!")
