from django.core.management.base import BaseCommand
from help_chat.models import KnowledgeBase, FAQ

class Command(BaseCommand):
    help = 'Populate the knowledge base and FAQ with initial data'

    def handle(self, *args, **options):
        self.stdout.write('Populating knowledge base and FAQ...')
        
        # Create Knowledge Base entries
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
- Reports section contains all your financial statements

**Getting Help:**
- Use the AI chat assistant for instant help
- Browse the Knowledge Base for detailed guides
- Check the FAQ for quick answers to common questions''',
                'keywords': 'getting started, setup, navigation, first time, tutorial, guide'
            },
            {
                'title': 'Understanding Chart of Accounts',
                'category': 'accounts',
                'content': '''The Chart of Accounts is the foundation of your accounting system. It's a list of all accounts used to categorize your business transactions.

**Account Types:**
- **Assets**: Things your business owns (Cash, Accounts Receivable, Equipment)
- **Liabilities**: Things your business owes (Accounts Payable, Loans)
- **Equity**: Owner's investment and retained earnings
- **Revenue**: Income from sales and services
- **Expenses**: Costs of running your business

**Creating Accounts:**
1. Go to 'Chart of Accounts' in the main menu
2. Click 'Add New Account'
3. Select the account type
4. Enter the account name and description
5. Set the account code (optional)
6. Save the account

**Best Practices:**
- Use clear, descriptive account names
- Follow standard accounting conventions
- Group similar accounts together
- Review and clean up unused accounts regularly''',
                'keywords': 'chart of accounts, accounts, assets, liabilities, equity, revenue, expenses, account types'
            },
            {
                'title': 'Recording Transactions',
                'category': 'transactions',
                'content': '''Transactions are the building blocks of your accounting records. Every financial event in your business should be recorded as a transaction.

**Creating a Transaction:**
1. Navigate to 'Transactions' > 'New Transaction'
2. Select the transaction date
3. Choose the accounts to debit and credit
4. Enter the amounts (debits must equal credits)
5. Add a description explaining the transaction
6. Upload source documents if available
7. Save the transaction

**Important Rules:**
- Every transaction must balance (total debits = total credits)
- Use clear, descriptive descriptions
- Include reference numbers when available
- Attach supporting documents for audit trail

**Common Transaction Types:**
- Sales: Debit Cash/Accounts Receivable, Credit Revenue
- Purchases: Debit Expense/Asset, Credit Cash/Accounts Payable
- Payments: Debit Accounts Payable, Credit Cash
- Receipts: Debit Cash, Credit Accounts Receivable

**Source Documents:**
You can upload supporting documents like receipts, invoices, and bank statements to provide evidence for your transactions.''',
                'keywords': 'transactions, recording, debit, credit, balance, source documents, receipts, invoices'
            },
            {
                'title': 'Working with Journal Entries',
                'category': 'journal_entries',
                'content': '''Journal entries allow you to record complex transactions that involve multiple accounts or adjusting entries.

**Creating Journal Entries:**
1. Go to 'Journal Entries' > 'New Entry'
2. Select the entry date
3. Add multiple line items with accounts, debits, and credits
4. Ensure total debits equal total credits
5. Add a reference number and description
6. Upload supporting documents if needed
7. Save the entry

**When to Use Journal Entries:**
- Adjusting entries at month/year end
- Corrections to previously recorded transactions
- Complex transactions involving multiple accounts
- Depreciation entries
- Accrual entries

**Components of a Journal Entry:**
- **Date**: When the transaction occurred
- **Reference**: Internal reference number
- **Description**: Explanation of the entry
- **Line Items**: Individual debit and credit lines
- **Accounts**: Which accounts are affected
- **Amounts**: Debit and credit amounts

**Best Practices:**
- Use clear reference numbers
- Provide detailed descriptions
- Review entries before saving
- Keep supporting documentation
- Use consistent formatting''',
                'keywords': 'journal entries, adjusting entries, corrections, multiple accounts, reference, line items'
            },
            {
                'title': 'Managing Clients',
                'category': 'clients',
                'content': '''Client management helps you keep track of your customers and their contact information for invoicing and relationship management.

**Adding New Clients:**
1. Navigate to 'Clients' in the main menu
2. Click 'Add New Client'
3. Fill in the client's information:
   - Company/Individual name
   - Contact person details
   - Address information
   - Email and phone
   - Tax information if applicable
4. Save the client record

**Client Information:**
- **Basic Details**: Name, contact person, address
- **Contact Info**: Email, phone, website
- **Billing Address**: May differ from main address
- **Tax Details**: Tax ID, tax exemption status
- **Notes**: Additional information about the client

**Using Client Records:**
- Select clients when creating invoices
- Track outstanding receivables by client
- Generate client-specific reports
- Maintain communication history

**Best Practices:**
- Keep client information up to date
- Use consistent naming conventions
- Include all relevant contact details
- Add notes for special requirements
- Regular cleanup of inactive clients''',
                'keywords': 'clients, customers, contact information, invoicing, management, addresses, billing'
            },
            {
                'title': 'Understanding Reports',
                'category': 'reports',
                'content': '''Bookgium provides several key financial reports to help you understand your business performance and financial position.

**Available Reports:**

**Balance Sheet:**
- Shows your financial position at a specific date
- Lists assets, liabilities, and equity
- Must balance (Assets = Liabilities + Equity)
- Use for understanding financial health

**Income Statement (P&L):**
- Shows revenue and expenses over a period
- Calculates net income/loss
- Use for performance analysis
- Compare periods to track trends

**Trial Balance:**
- Lists all accounts with their balances
- Ensures debits equal credits
- Use for account verification
- Helpful for preparing other reports

**General Ledger:**
- Detailed transaction history by account
- Shows all debits and credits
- Use for detailed analysis
- Essential for auditing

**Generating Reports:**
1. Go to 'Reports' in the main menu
2. Select the report type
3. Choose date ranges
4. Apply any filters needed
5. View or export the report

**Report Options:**
- PDF export for sharing
- Excel export for analysis
- Date range filtering
- Account filtering
- Comparative periods''',
                'keywords': 'reports, balance sheet, income statement, trial balance, general ledger, financial statements, PDF, Excel'
            },
            {
                'title': 'Configuring Settings',
                'category': 'settings',
                'content': '''Settings allow you to customize Bookgium to match your business needs and preferences.

**Company Settings:**
- Company name and address
- Tax registration numbers
- Logo and branding
- Contact information

**Currency Settings:**
- Default currency for your business
- Currency symbols and formatting
- Multi-currency support (if enabled)
- Exchange rate handling

**Account Preferences:**
- Default accounts for common transactions
- Account numbering system
- Account grouping preferences
- Chart of accounts structure

**User Preferences:**
- Date and time formats
- Number formatting
- Report defaults
- Dashboard customization

**System Settings:**
- Backup and security settings
- User access controls
- Audit trail configuration
- Data retention policies

**Accessing Settings:**
1. Click on 'Settings' in the main menu
2. Select the category you want to modify
3. Make your changes
4. Save the settings

**Important Notes:**
- Some settings affect all users
- Currency changes may affect existing data
- Backup your data before major changes
- Test settings in a safe environment first''',
                'keywords': 'settings, configuration, company, currency, preferences, system, backup, security'
            }
        ]
        
        for entry_data in knowledge_entries:
            knowledge_base, created = KnowledgeBase.objects.get_or_create(
                title=entry_data['title'],
                defaults=entry_data
            )
            if created:
                self.stdout.write(f'Created knowledge base entry: {entry_data["title"]}')
            else:
                self.stdout.write(f'Knowledge base entry already exists: {entry_data["title"]}')
        
        # Create FAQ entries
        faq_entries = [
            {
                'question': 'How do I create my first account?',
                'category': 'accounts',
                'answer': '''To create your first account:
1. Go to "Chart of Accounts" in the main menu
2. Click "Add New Account"
3. Choose an account type (Asset, Liability, Equity, Revenue, or Expense)
4. Enter a clear account name (e.g., "Cash", "Sales Revenue", "Office Supplies")
5. Add a description if needed
6. Click "Save"

Start with basic accounts like Cash, Sales Revenue, and common expense accounts.'''
            },
            {
                'question': 'What is the difference between a transaction and a journal entry?',
                'category': 'transactions',
                'answer': '''Transactions and journal entries serve different purposes:

**Transactions:**
- Simple, two-account entries (one debit, one credit)
- Good for routine business activities
- Examples: sales, purchases, payments

**Journal Entries:**
- Can involve multiple accounts
- Used for complex entries or adjustments
- Examples: depreciation, corrections, period-end adjustments

Both must follow the fundamental rule: debits must equal credits.'''
            },
            {
                'question': 'How do I balance my books?',
                'category': 'general',
                'answer': '''To ensure your books are balanced:

1. **Check the Trial Balance report** - total debits should equal total credits
2. **Review individual transactions** - each must have equal debits and credits
3. **Verify account balances** - ensure they make sense for the account type
4. **Look for data entry errors** - check for transposed numbers or wrong accounts
5. **Use the Balance Sheet** - Assets should equal Liabilities plus Equity

If books don't balance, use the General Ledger report to find discrepancies.'''
            },
            {
                'question': 'Can I upload documents with my transactions?',
                'category': 'transactions',
                'answer': '''Yes! You can upload source documents with both transactions and journal entries:

1. When creating or editing a transaction/journal entry
2. Look for the "Source Documents" section
3. Click "Choose File" to select documents
4. You can upload multiple files (receipts, invoices, bank statements)
5. Supported formats include PDF, images (JPG, PNG), and common document types

This creates a complete audit trail and helps with record-keeping and compliance.'''
            },
            {
                'question': 'How do I change the currency?',
                'category': 'settings',
                'answer': '''To change your default currency:

1. Go to "Settings" in the main menu
2. Look for "Currency Settings" or similar section
3. Select your preferred currency from the dropdown
4. Save the changes

**Note:** Changing currency affects how amounts are displayed throughout the application. Existing transaction amounts are not converted - only the display symbol changes.

Supported currencies include USD, EUR, GBP, CAD, AUD, JPY, and many others.'''
            },
            {
                'question': 'What reports should I run regularly?',
                'category': 'reports',
                'answer': '''Essential reports to run regularly:

**Monthly:**
- Income Statement (P&L) - shows profitability
- Balance Sheet - shows financial position
- Trial Balance - ensures books are balanced

**Weekly:**
- Accounts Receivable aging
- Cash flow summary

**Daily:**
- Transaction summaries
- Account balances

**Year-end:**
- Complete financial statements
- General Ledger for all accounts
- Tax preparation reports

Run reports consistently to track trends and identify issues early.'''
            },
            {
                'question': 'How do I add a new client?',
                'category': 'clients',
                'answer': '''To add a new client:

1. Navigate to "Clients" in the main menu
2. Click "Add New Client" button
3. Fill in the required information:
   - Client/Company name
   - Contact person (if applicable)
   - Email and phone number
   - Business address
   - Billing address (if different)
4. Add any additional notes
5. Click "Save"

Complete client records help with invoicing, communication, and relationship management.'''
            },
            {
                'question': 'What should I do if I made an error in a transaction?',
                'category': 'troubleshooting',
                'answer': '''If you made an error in a transaction:

**For Recent Transactions:**
1. Go to the transaction list
2. Find the incorrect transaction
3. Click "Edit" 
4. Make the necessary corrections
5. Save the changes

**For Posted/Finalized Transactions:**
1. Create a correcting journal entry
2. Reverse the incorrect amounts
3. Enter the correct amounts
4. Add a clear description explaining the correction

**Best Practice:** Always document corrections with clear descriptions and keep supporting documentation.'''
            }
        ]
        
        for faq_data in faq_entries:
            faq, created = FAQ.objects.get_or_create(
                question=faq_data['question'],
                defaults=faq_data
            )
            if created:
                self.stdout.write(f'Created FAQ: {faq_data["question"]}')
            else:
                self.stdout.write(f'FAQ already exists: {faq_data["question"]}')
        
        self.stdout.write(self.style.SUCCESS('Successfully populated knowledge base and FAQ!'))
