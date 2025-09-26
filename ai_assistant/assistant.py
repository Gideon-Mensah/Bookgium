try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from django.conf import settings
from django.core.cache import cache
import json
from typing import List, Dict
import os

class BookgiumAIAssistant:
    """AI Assistant for Bookgium accounting application"""
    
    def __init__(self):
        self.openai_available = OPENAI_AVAILABLE
        self.api_key = getattr(settings, 'OPENAI_API_KEY', '') or os.getenv('OPENAI_API_KEY', '')
        
        if self.openai_available and self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            self.client = None
            
        self.knowledge_base = self._load_knowledge_base()
    
    def _load_knowledge_base(self) -> str:
        """Load Bookgium-specific knowledge base"""
        return """
        Bookgium is a comprehensive accounting application with the following features:
        
        1. ACCOUNTS MANAGEMENT:
        - Chart of Accounts with hierarchical structure
        - Account types: Assets, Liabilities, Equity, Income, Expenses
        - Opening balance management
        - Account statements and reports
        
        2. JOURNAL ENTRIES:
        - Double-entry bookkeeping
        - Quick journal entries for simple transactions
        - Complex journal entries with multiple lines
        - Transaction history and audit trails
        
        3. INVOICING:
        - Customer management
        - Invoice creation and management
        - Payment tracking
        - Invoice templates
        
        4. REPORTING:
        - Trial Balance
        - Balance Sheet
        - Income Statement (P&L)
        - Cash Flow reports
        - Aged receivables
        - Custom report templates
        
        5. MULTI-CURRENCY SUPPORT:
        - 15+ supported currencies
        - User-specific currency preferences
        - Currency conversion
        
        6. USER MANAGEMENT:
        - Role-based access (Admin, Accountant, Viewer)
        - Multi-tenant support
        - User preferences and settings
        
        Common accounting principles:
        - Assets = Liabilities + Equity
        - Debits must equal Credits
        - Revenue increases equity
        - Expenses decrease equity
        """
    
    def get_help_response(self, user_question: str, user_context: Dict = None) -> str:
        """Get AI response for user questions about Bookgium"""
        
        # Check if OpenAI is available and configured
        if not self.openai_available:
            return self._get_fallback_response(user_question)
        
        if not self.api_key:
            return "AI Assistant is not configured. Please set your OpenAI API key in the environment variables."
        
        # Build context from user's current state
        context_info = ""
        if user_context:
            context_info = f"""
            User Context:
            - Current page: {user_context.get('current_page', 'Unknown')}
            - User role: {user_context.get('user_role', 'Unknown')}
            - Recent actions: {user_context.get('recent_actions', [])}
            """
        
        system_prompt = f"""
        You are a helpful AI assistant for Bookgium, an accounting application.
        
        {self.knowledge_base}
        
        {context_info}
        
        Guidelines:
        1. Provide clear, step-by-step instructions
        2. Use accounting terminology appropriately
        3. Reference specific Bookgium features
        4. If you're unsure, ask for clarification
        5. Always consider double-entry bookkeeping principles
        6. Be helpful but concise
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Using gpt-3.5-turbo for cost efficiency
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_question}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return self._get_fallback_response(user_question)
    
    def _get_fallback_response(self, user_question: str) -> str:
        """Fallback response when OpenAI is not available"""
        
        # Simple keyword-based responses
        question_lower = user_question.lower()
        
        if any(word in question_lower for word in ['journal', 'entry', 'debit', 'credit']):
            return """
            To create a journal entry in Bookgium:
            1. Go to Accounts > Journal Entries
            2. Click 'New Journal Entry'  
            3. Enter the date and description
            4. Add debit and credit lines (must balance)
            5. Save the entry
            
            Remember: Total debits must equal total credits!
            """
        
        elif any(word in question_lower for word in ['account', 'create', 'new']):
            return """
            To create a new account:
            1. Go to Accounts > Chart of Accounts
            2. Click 'New Account'
            3. Enter account code and name
            4. Select the account type (Asset, Liability, Equity, Income, Expense)
            5. Set opening balance if needed
            6. Save the account
            """
        
        elif any(word in question_lower for word in ['invoice', 'customer']):
            return """
            To create an invoice:
            1. Go to Invoices > Create Invoice
            2. Select or create a customer
            3. Add invoice items with descriptions and amounts
            4. Review totals and tax calculations
            5. Save and send the invoice
            """
        
        elif any(word in question_lower for word in ['report', 'balance', 'sheet']):
            return """
            To generate reports:
            1. Go to Reports section
            2. Choose report type:
               - Trial Balance: Shows all account balances
               - Balance Sheet: Assets = Liabilities + Equity
               - Income Statement: Revenue - Expenses = Net Income
            3. Select date range
            4. Generate and export as needed
            """
        
        else:
            return """
            I'm currently operating in basic mode. Here are some common help topics:
            
            📊 **Accounts**: Create accounts, set opening balances, view statements
            📝 **Journal Entries**: Record transactions, ensure debits = credits  
            💰 **Invoicing**: Create invoices, track payments, manage customers
            📈 **Reports**: Generate trial balance, balance sheet, income statement
            
            For detailed help, please refer to the Bookgium documentation or contact support.
            """
    
    def get_contextual_help(self, page_name: str, user_role: str) -> List[str]:
        """Get contextual help suggestions based on current page"""
        
        help_suggestions = {
            'accounts': [
                "How do I create a new account?",
                "What's the difference between assets and liabilities?",
                "How do I set opening balances?",
                "How do I generate an account statement?"
            ],
            'journal_entries': [
                "How do I create a journal entry?",
                "What if my debits don't equal credits?",
                "How do I edit a journal entry?",
                "What's a quick journal entry?"
            ],
            'invoices': [
                "How do I create an invoice?",
                "How do I track payments?",
                "How do I set up customers?",
                "How do I customize invoice templates?"
            ],
            'reports': [
                "How do I generate a trial balance?",
                "What's the difference between Balance Sheet and P&L?",
                "How do I create custom reports?",
                "How do I export reports to Excel?"
            ]
        }
        
        return help_suggestions.get(page_name, [
            "How do I navigate Bookgium?",
            "What accounting features are available?",
            "How do I get started with bookkeeping?"
        ])

# Usage example
def get_ai_response(question: str, user=None, current_page=None):
    """Utility function to get AI response"""
    assistant = BookgiumAIAssistant()
    
    context = {}
    if user:
        context['user_role'] = getattr(user, 'role', 'viewer')
        context['current_page'] = current_page
    
    return assistant.get_help_response(question, context)
