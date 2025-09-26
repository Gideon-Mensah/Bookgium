"""
Knowledge Base integration for Bookgium AI Assistant

This creates a searchable knowledge base from your documentation.
"""

from django.db import models
import json
from typing import List, Dict

class KnowledgeBaseEntry(models.Model):
    """Store knowledge base entries for AI assistant"""
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=100)  # 'accounts', 'invoices', 'reports', etc.
    tags = models.CharField(max_length=500, blank=True)  # comma-separated
    priority = models.IntegerField(default=1)  # Higher priority = more relevant
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', '-updated_at']
    
    def __str__(self):
        return self.title

class AITrainingSession(models.Model):
    """Track AI training sessions and improvements"""
    
    user_question = models.TextField()
    ai_response = models.TextField()
    user_feedback = models.CharField(max_length=20, choices=[
        ('helpful', 'Helpful'),
        ('not_helpful', 'Not Helpful'),
        ('partially_helpful', 'Partially Helpful')
    ])
    improvement_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Training session {self.id} - {self.user_feedback}"

# Knowledge base management functions
def populate_knowledge_base():
    """Populate initial knowledge base entries"""
    
    entries = [
        {
            'title': 'Creating Journal Entries',
            'content': '''
            To create a journal entry in Bookgium:
            1. Navigate to Accounts > Journal Entries
            2. Click "New Journal Entry" button
            3. Fill in the entry date and description
            4. Add journal entry lines with accounts, debit/credit amounts
            5. Ensure total debits equal total credits
            6. Save the entry
            
            For simple two-account transactions, use the "Quick Journal Entry" option.
            ''',
            'category': 'accounts',
            'tags': 'journal entry, bookkeeping, debits, credits',
            'priority': 5
        },
        {
            'title': 'Understanding Account Types',
            'content': '''
            Bookgium uses five main account types:
            
            1. ASSETS: Resources owned by the business
               - Normal balance: Debit
               - Examples: Cash, Accounts Receivable, Inventory
            
            2. LIABILITIES: Debts owed by the business
               - Normal balance: Credit
               - Examples: Accounts Payable, Loans, Accrued Expenses
            
            3. EQUITY: Owner's stake in the business
               - Normal balance: Credit
               - Examples: Capital, Retained Earnings
            
            4. INCOME/REVENUE: Money earned from business operations
               - Normal balance: Credit
               - Examples: Sales Revenue, Service Income
            
            5. EXPENSES: Costs incurred in business operations
               - Normal balance: Debit
               - Examples: Rent, Utilities, Salaries
            ''',
            'category': 'accounts',
            'tags': 'account types, assets, liabilities, equity, income, expenses',
            'priority': 5
        },
        # Add more entries...
    ]
    
    for entry_data in entries:
        KnowledgeBaseEntry.objects.get_or_create(
            title=entry_data['title'],
            defaults=entry_data
        )
