from django.core.management.base import BaseCommand
from help_chat.models import KnowledgeBase, FAQ

class Command(BaseCommand):
    help = 'Populate the knowledge base with initial content'

    def handle(self, *args, **options):
        # Clear existing data
        KnowledgeBase.objects.all().delete()
        FAQ.objects.all().delete()
        
        # Knowledge Base entries
        knowledge_entries = [
            {
                'title': 'Getting Started with Bookgium',
                'category': 'getting_started',
                'content': '''Welcome to Bookgium! This guide will help you get started with our comprehensive accounting application.

**First Steps:**
1. **Set up Chart of Accounts**: Start by creating your account structure. Go to "Chart of Accounts" and add your business accounts (Assets, Liabilities, Equity, Revenue, and Expenses).

2. **Add Clients**: If you work with customers, set up your client list in the "Clients" section. This will be useful for invoicing and tracking customer transactions.

3. **Configure Settings**: Visit the Settings page to configure your default currency, company information, and other preferences.

**Key Features:**
- **Chart of Accounts**: Organize your financial structure
- **Transactions**: Record individual financial transactions
- **Journal Entries**: Create complex multi-account entries
- **Reports**: Generate financial statements and analysis
- **Invoicing**: Create and manage customer invoices
- **Audit Trail**: Track all changes and activities

**Tips for Success:**
- Always ensure your debits equal credits in journal entries
- Upload source documents (receipts, invoices) to support your entries
- Review your trial balance regularly to ensure accuracy
- Use meaningful descriptions for all transactions

Need help with any specific feature? Feel free to ask our AI assistant!''',
                'keywords': 'getting started, setup, first time, new user, basics, overview'
            },
            {
                'title': 'Creating and Managing Chart of Accounts',
                'category': 'accounts',
                'content': '''The Chart of Accounts is the foundation of your accounting system. It organizes all your financial accounts into categories.

**Account Types:**
- **Assets**: What you own (Cash, Accounts Receivable, Equipment, etc.)
- **Liabilities**: What you owe (Accounts Payable, Loans, etc.)
- **Equity**: Owner's investment and retained earnings
- **Revenue**: Income from sales and services
- **Expenses**: Costs of doing business

**Creating New Accounts:**
1. Navigate to "Chart of Accounts" in the main menu
2. Click "Add New Account"
3. Enter account code (e.g., 1000 for Cash)
4. Choose account type from dropdown
5. Enter account name and description
6. Select parent account if creating sub-accounts
7. Click "Save"

**Best Practices:**
- Use a consistent numbering system (1000s for Assets, 2000s for Liabilities, etc.)
- Create meaningful account names
- Group similar accounts under parent accounts
- Keep active accounts separate from inactive ones

**Account Codes Convention:**
- 1000-1999: Assets
- 2000-2999: Liabilities  
- 3000-3999: Equity
- 4000-4999: Revenue
- 5000-9999: Expenses''',
                'keywords': 'chart of accounts, accounts, assets, liabilities, equity, revenue, expenses, account types'
            },
            {
                'title': 'Recording Transactions',
                'category': 'transactions',
                'content': '''Transactions are individual financial events that affect your business accounts. Each transaction must balance (debits = credits).

**Recording a Transaction:**
1. Go to "Transactions" > "New Transaction"
2. Select the transaction date
3. Choose the account to be affected
4. Select transaction type (Debit or Credit)
5. Enter the amount
6. Add a clear description
7. Upload supporting documents if available
8. Click "Save"

**Transaction Types:**
- **Debit**: Increases Assets and Expenses, Decreases Liabilities, Equity, and Revenue
- **Credit**: Increases Liabilities, Equity, and Revenue, Decreases Assets and Expenses

**Common Transaction Examples:**
- **Cash Sale**: Debit Cash, Credit Sales Revenue
- **Purchase Supplies**: Debit Office Supplies, Credit Cash or Accounts Payable
- **Pay Rent**: Debit Rent Expense, Credit Cash
- **Receive Payment**: Debit Cash, Credit Accounts Receivable

**Tips:**
- Always include clear, descriptive text
- Upload receipts or invoices as evidence
- Double-check amounts before saving
- Review transaction reports regularly

**Supporting Documents:**
You can upload up to 5 documents per transaction:
- Receipts
- Invoices  
- Bank statements
- Contracts
- Other supporting evidence''',
                'keywords': 'transactions, recording, debit, credit, balance, financial events'
            },
            {
                'title': 'Creating Journal Entries',
                'category': 'journal_entries',
                'content': '''Journal entries allow you to record complex transactions involving multiple accounts in a single entry.

**Creating a Journal Entry:**
1. Navigate to "Journal Entries" > "New Entry"
2. Enter the date for the entry
3. Add a reference number (optional but recommended)
4. Enter a description of the transaction
5. Add line items for each account affected:
   - Select account
   - Choose Debit or Credit
   - Enter amount
   - Add line description
6. Ensure total debits equal total credits
7. Upload supporting documents
8. Save the entry

**Journal Entry Rules:**
- Total debits must equal total credits
- Minimum of 2 accounts involved
- Maximum of 20 line items per entry
- All amounts must be positive numbers

**Common Journal Entry Examples:**

**Equipment Purchase with Loan:**
- Debit: Equipment $10,000
- Credit: Bank Loan $10,000

**Adjusting Entry for Depreciation:**
- Debit: Depreciation Expense $500
- Credit: Accumulated Depreciation $500

**Record Sales with Tax:**
- Debit: Accounts Receivable $1,080
- Credit: Sales Revenue $1,000
- Credit: Sales Tax Payable $80

**Tips for Success:**
- Use clear, descriptive references
- Add detailed descriptions for each line
- Upload all relevant documentation
- Review the entry before saving
- Check that debits equal credits''',
                'keywords': 'journal entries, multiple accounts, debits, credits, balance, complex transactions'
            },
            {
                'title': 'Managing Clients and Customers',
                'category': 'clients',
                'content': '''The client management system helps you track customer information for invoicing and relationship management.

**Adding New Clients:**
1. Go to "Clients" in the main menu
2. Click "Add New Client"
3. Enter client information:
   - Company/Individual name
   - Contact person
   - Email address
   - Phone number
   - Billing address
   - Shipping address (if different)
4. Add any additional notes
5. Save the client record

**Client Information Includes:**
- Basic contact details
- Billing and shipping addresses
- Payment terms and preferences
- Transaction history
- Outstanding balances
- Communication log

**Using Client Data:**
- Generate invoices automatically
- Track customer payments
- Analyze customer profitability
- Maintain communication history
- Monitor credit limits

**Best Practices:**
- Keep contact information current
- Set up payment terms clearly
- Track communication with notes
- Regular review of customer accounts
- Monitor overdue accounts

**Integration with Other Features:**
- Invoicing system uses client data
- Transaction reports can filter by client
- Aging reports track overdue amounts
- Customer statements generation''',
                'keywords': 'clients, customers, contact management, invoicing, customer data'
            },
            {
                'title': 'Financial Reports and Analysis',
                'category': 'reports',
                'content': '''Bookgium provides comprehensive financial reporting to help you understand your business performance.

**Available Reports:**

**Balance Sheet:**
- Shows financial position at a specific date
- Lists Assets, Liabilities, and Equity
- Must balance (Assets = Liabilities + Equity)

**Income Statement (P&L):**
- Shows Revenue and Expenses over a period
- Calculates Net Income (Revenue - Expenses)
- Available for any date range

**Trial Balance:**
- Lists all accounts with their balances
- Shows debits and credits for verification
- Helps identify data entry errors

**General Ledger:**
- Detailed transaction history by account
- Shows all debits and credits
- Useful for account analysis

**Generating Reports:**
1. Navigate to "Reports" menu
2. Select desired report type
3. Choose date range or specific date
4. Apply any filters (account, client, etc.)
5. Click "Generate Report"
6. Export to PDF or Excel if needed

**Report Features:**
- Date range filtering
- Account filtering
- Client-specific reports
- Export capabilities
- Print-friendly formats

**Using Reports for Analysis:**
- Monitor profitability trends
- Track cash flow patterns
- Analyze expense categories
- Review customer performance
- Prepare for tax filing''',
                'keywords': 'reports, financial statements, balance sheet, income statement, trial balance, analysis'
            },
            {
                'title': 'System Settings and Configuration',
                'category': 'settings',
                'content': '''Customize Bookgium to match your business needs through the Settings page.

**Currency Settings:**
- Choose your default currency from 15+ options
- Supported currencies include USD, EUR, GBP, CAD, AUD, JPY, and more
- Currency symbol appears throughout the application
- Change anytime in Settings > General

**Company Information:**
- Update company name and details
- Set default addresses
- Configure tax settings
- Add logo for reports and invoices

**User Preferences:**
- Date format preferences
- Report defaults
- Dashboard customization
- Notification settings

**Account Settings:**
- Default account types
- Chart of accounts structure
- Transaction categories
- Approval workflows

**System Configuration:**
- Backup settings
- Data export options
- Security preferences
- Audit trail settings

**Accessing Settings:**
1. Click "Settings" in the main navigation
2. Choose the category to modify
3. Make your changes
4. Click "Save" to apply

**Important Notes:**
- Currency changes affect new transactions only
- Some settings require admin privileges
- Changes are logged in audit trail
- Backup before major configuration changes''',
                'keywords': 'settings, configuration, currency, company info, preferences, customization'
            }
        ]

        # Create knowledge base entries
        for entry_data in knowledge_entries:
            KnowledgeBase.objects.create(**entry_data)
            self.stdout.write(f"Created KB entry: {entry_data['title']}")

        # FAQ entries
        faq_entries = [
            {
                'question': 'How do I change my default currency?',
                'answer': 'Go to Settings > General and select your preferred currency from the dropdown menu. The change will apply to new transactions and displays throughout the application.',
                'category': 'settings'
            },
            {
                'question': 'Why do my debits and credits need to balance?',
                'answer': 'This is a fundamental principle of double-entry bookkeeping. Every transaction affects at least two accounts, and the total debits must equal total credits to maintain the accounting equation (Assets = Liabilities + Equity).',
                'category': 'journal_entries'
            },
            {
                'question': 'Can I upload documents with my transactions?',
                'answer': 'Yes! You can upload up to 5 supporting documents per transaction or journal entry. Supported formats include PDF, images (JPG, PNG, GIF), and Office documents. Maximum file size is 10MB per document.',
                'category': 'transactions'
            },
            {
                'question': 'How do I create a new account?',
                'answer': 'Navigate to Chart of Accounts, click "Add New Account", enter the account code and name, select the account type (Asset, Liability, Equity, Revenue, or Expense), and save. Use a consistent numbering system for organization.',
                'category': 'accounts'
            },
            {
                'question': 'What reports are available?',
                'answer': 'Bookgium provides Balance Sheet, Income Statement, Trial Balance, and General Ledger reports. All reports can be filtered by date range and exported to PDF or Excel formats.',
                'category': 'reports'
            },
            {
                'question': 'How do I add a new client?',
                'answer': 'Go to the Clients section, click "Add New Client", fill in the contact information including name, email, phone, and addresses. Client data is used for invoicing and customer tracking.',
                'category': 'clients'
            },
            {
                'question': 'Can I edit transactions after saving?',
                'answer': 'Yes, you can edit transactions after saving them. However, all changes are tracked in the audit log for security and compliance purposes. Be careful when editing historical transactions.',
                'category': 'transactions'
            },
            {
                'question': 'What file types can I upload as source documents?',
                'answer': 'You can upload PDF files, images (JPG, JPEG, PNG, GIF), and Microsoft Office documents (Word, Excel). Each file must be under 10MB in size.',
                'category': 'general'
            },
            {
                'question': 'How do I create a journal entry with multiple accounts?',
                'answer': 'Go to Journal Entries > New Entry, add a description, then add line items for each account. Select the account, choose debit or credit, enter the amount. Ensure total debits equal total credits before saving.',
                'category': 'journal_entries'
            },
            {
                'question': 'Is there an audit trail for my data?',
                'answer': 'Yes, Bookgium maintains a complete audit trail that tracks all user actions, changes, and system events. You can view audit logs to see who made changes and when.',
                'category': 'general'
            }
        ]

        # Create FAQ entries
        for faq_data in faq_entries:
            FAQ.objects.create(**faq_data)
            self.stdout.write(f"Created FAQ: {faq_data['question']}")

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(knowledge_entries)} knowledge base entries and {len(faq_entries)} FAQs'
            )
        )
