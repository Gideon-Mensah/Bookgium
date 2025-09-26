from django.db import models
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
import os
import uuid

class Account(models.Model):
    ACCOUNT_TYPES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    
    code = models.CharField(max_length=20, unique=True, help_text="Account code (e.g., 1000, 2000)")
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='asset')
    description = models.TextField(blank=True, null=True)
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), 
                                        help_text="Opening balance for this account")
    opening_balance_date = models.DateField(null=True, blank=True, 
                                          help_text="Date of the opening balance")
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_absolute_url(self):
        return reverse('accounts:account_detail', kwargs={'pk': self.pk})

    @property
    def balance(self):
        """Calculate account balance including opening balance and journal entry lines"""
        from django.db.models import Sum, Q
        
        # Get sum of credits and debits from posted journal entries only
        credits = self.journal_lines.filter(
            journal_entry__is_posted=True,
            entry_type='credit'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        debits = self.journal_lines.filter(
            journal_entry__is_posted=True,
            entry_type='debit'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Calculate journal entry balance
        if self.account_type in ['asset', 'expense']:
            journal_balance = debits - credits
        else:
            journal_balance = credits - debits
        
        # Add opening balance
        return self.opening_balance + journal_balance
    
    @property
    def journal_balance(self):
        """Calculate only the balance from journal entries (excluding opening balance)"""
        from django.db.models import Sum, Q
        
        # Get sum of credits and debits from posted journal entries only
        credits = self.journal_lines.filter(
            journal_entry__is_posted=True,
            entry_type='credit'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        debits = self.journal_lines.filter(
            journal_entry__is_posted=True,
            entry_type='debit'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # For asset and expense accounts, balance = debits - credits
        if self.account_type in ['asset', 'expense']:
            return debits - credits
        # For liability, equity, and income accounts, balance = credits - debits
        else:
            return credits - debits

    @property 
    def balance_with_unposted(self):
        """Calculate account balance including unposted journal entries"""
        from django.db.models import Sum, Q
        
        # Get sum of credits and debits from all journal entries
        credits = self.journal_lines.filter(entry_type='credit').aggregate(
            total=Sum('amount'))['total'] or Decimal('0')
        debits = self.journal_lines.filter(entry_type='debit').aggregate(
            total=Sum('amount'))['total'] or Decimal('0')
        
        # Calculate journal entry balance
        if self.account_type in ['asset', 'expense']:
            journal_balance = debits - credits
        else:
            journal_balance = credits - debits
        
        # Add opening balance
        return self.opening_balance + journal_balance

class JournalEntry(models.Model):
    """
    Represents a complete double-entry journal entry.
    Each journal entry must have balanced debits and credits.
    """
    date = models.DateField(default=timezone.now)
    description = models.TextField(help_text="Description of the transaction")
    reference = models.CharField(max_length=50, blank=True, null=True, help_text="Reference number or code")
    notes = models.TextField(blank=True, null=True, help_text="Optional additional notes")
    is_posted = models.BooleanField(default=False, help_text="Whether this entry has been posted to the ledger")
    created_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Journal Entry'
        verbose_name_plural = 'Journal Entries'

    def __str__(self):
        return f"JE-{self.id}: {self.description[:50]} ({self.date})"

    def get_absolute_url(self):
        return reverse('accounts:journal_entry_detail', kwargs={'pk': self.pk})

    @property
    def total_debits(self):
        """Calculate total debit amount for this journal entry"""
        return self.lines.filter(entry_type='debit').aggregate(
            total=models.Sum('amount'))['total'] or Decimal('0')

    @property
    def total_credits(self):
        """Calculate total credit amount for this journal entry"""
        return self.lines.filter(entry_type='credit').aggregate(
            total=models.Sum('amount'))['total'] or Decimal('0')

    @property
    def is_balanced(self):
        """Check if debits equal credits"""
        return self.total_debits == self.total_credits

    def clean(self):
        from django.core.exceptions import ValidationError
        # Only validate balance if the entry has lines
        if hasattr(self, '_state') and self._state.adding:
            return  # Skip validation during creation
        
        if not self.is_balanced:
            raise ValidationError(
                f"Journal entry is not balanced. Debits: {self.total_debits}, Credits: {self.total_credits}"
            )

    def post(self):
        """Post this journal entry to the ledger"""
        if not self.is_balanced:
            raise ValueError("Cannot post unbalanced journal entry")
        
        self.is_posted = True
        self.save()

class JournalEntryLine(models.Model):
    """
    Individual debit or credit line within a journal entry.
    Multiple lines make up a complete double-entry transaction.
    """
    ENTRY_TYPES = [
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    ]
    
    journal_entry = models.ForeignKey(JournalEntry, related_name='lines', on_delete=models.CASCADE)
    account = models.ForeignKey(Account, related_name='journal_lines', on_delete=models.CASCADE)
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True, null=True, help_text="Line-specific description")

    class Meta:
        ordering = ['entry_type', 'account__code']  # Debits first, then credits

    def __str__(self):
        return f"{self.account.code} - {self.entry_type.title()}: {self.amount}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.amount and self.amount <= 0:
            raise ValidationError("Amount must be greater than zero.")

# Keep the old Transaction model for backward compatibility, but deprecate it
class Transaction(models.Model):
    """
    DEPRECATED: Use JournalEntry and JournalEntryLine instead.
    This model is kept for backward compatibility only.
    """
    TRANSACTION_TYPES = [
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    ]
    
    account = models.ForeignKey(Account, related_name='transactions', on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    description = models.TextField()
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    notes = models.TextField(blank=True, null=True, help_text="Optional additional notes")
    created_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.account.name} - {self.description[:50]}"

    def get_absolute_url(self):
        return reverse('accounts:transaction_detail', kwargs={'pk': self.pk})

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.amount and self.amount <= 0:
            raise ValidationError("Amount must be greater than zero.")


def source_document_upload_path(instance, filename):
    """Generate upload path for source documents"""
    # Get file extension
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4().hex}.{ext}" if ext else str(uuid.uuid4().hex)
    
    # Organize by year/month for better file management
    if hasattr(instance, 'transaction') and instance.transaction:
        date_folder = instance.transaction.date.strftime('%Y/%m')
        return f'source_documents/transactions/{date_folder}/{unique_filename}'
    elif hasattr(instance, 'journal_entry') and instance.journal_entry:
        date_folder = instance.journal_entry.date.strftime('%Y/%m')
        return f'source_documents/journal_entries/{date_folder}/{unique_filename}'
    else:
        return f'source_documents/misc/{unique_filename}'


class SourceDocument(models.Model):
    """Model for storing source documents attached to transactions or journal entries"""
    
    DOCUMENT_TYPES = [
        ('receipt', 'Receipt'),
        ('invoice', 'Invoice'),
        ('bank_statement', 'Bank Statement'),
        ('contract', 'Contract'),
        ('check', 'Check'),
        ('voucher', 'Voucher'),
        ('other', 'Other'),
    ]
    
    # Relations - can be attached to either a transaction or journal entry
    transaction = models.ForeignKey(
        Transaction, 
        related_name='source_documents', 
        on_delete=models.CASCADE,
        null=True, 
        blank=True,
        help_text="Legacy transaction this document is attached to"
    )
    journal_entry = models.ForeignKey(
        JournalEntry,
        related_name='source_documents',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Journal entry this document is attached to"
    )
    
    # Document details
    title = models.CharField(
        max_length=200, 
        help_text="Descriptive title for the document"
    )
    document_type = models.CharField(
        max_length=20, 
        choices=DOCUMENT_TYPES, 
        default='other',
        help_text="Type of source document"
    )
    file = models.FileField(
        upload_to=source_document_upload_path,
        help_text="Upload the source document file"
    )
    description = models.TextField(
        blank=True, 
        null=True,
        help_text="Optional description or notes about the document"
    )
    
    # File metadata
    file_size = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="File size in bytes"
    )
    content_type = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="MIME type of the file"
    )
    
    # Audit fields
    uploaded_by = models.ForeignKey(
        'users.CustomUser', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    uploaded_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Source Document'
        verbose_name_plural = 'Source Documents'
    
    def __str__(self):
        parent = self.transaction or self.journal_entry
        parent_type = "Transaction" if self.transaction else "Journal Entry"
        return f"{self.title} ({parent_type}: {parent})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Ensure document is attached to either transaction or journal entry, but not both
        if self.transaction and self.journal_entry:
            raise ValidationError("Document cannot be attached to both transaction and journal entry.")
        
        if not self.transaction and not self.journal_entry:
            raise ValidationError("Document must be attached to either a transaction or journal entry.")
    
    def save(self, *args, **kwargs):
        # Set file metadata if file is present
        if self.file:
            self.file_size = self.file.size
            self.content_type = getattr(self.file.file, 'content_type', '')
        
        super().save(*args, **kwargs)
    
    @property
    def filename(self):
        """Get the original filename"""
        if self.file:
            return os.path.basename(self.file.name)
        return None
    
    @property
    def file_extension(self):
        """Get file extension"""
        if self.file:
            return os.path.splitext(self.file.name)[1].lower()
        return None
    
    @property
    def file_size_formatted(self):
        """Get human-readable file size"""
        if not self.file_size:
            return "Unknown"
        
        size = float(self.file_size)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    @property
    def is_image(self):
        """Check if the file is an image"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        return self.file_extension in image_extensions
    
    @property
    def is_pdf(self):
        """Check if the file is a PDF"""
        return self.file_extension == '.pdf'
