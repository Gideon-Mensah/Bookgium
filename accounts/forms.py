from django import forms
from django.forms import inlineformset_factory
from .models import Account, Transaction, JournalEntry, JournalEntryLine, SourceDocument
from decimal import Decimal

class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['code', 'name', 'account_type', 'description', 'opening_balance', 'opening_balance_date', 'parent', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 1000'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Account name'}),
            'account_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional description'}),
            'opening_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'opening_balance_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'parent': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter parent accounts to only show accounts of compatible types
        self.fields['parent'].queryset = Account.objects.filter(is_active=True)
        self.fields['parent'].empty_label = "None (Top Level Account)"

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['account', 'date', 'description', 'transaction_type', 'amount', 'notes']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Transaction description'}),
            'transaction_type': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional notes'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active accounts
        active_accounts = Account.objects.filter(is_active=True).order_by('code')
        self.fields['account'].queryset = active_accounts

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')

        if amount and amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")

        return cleaned_data

class AccountFilterForm(forms.Form):
    ACCOUNT_TYPE_CHOICES = [('', 'All Types')] + Account.ACCOUNT_TYPES
    
    account_type = forms.ChoiceField(
        choices=ACCOUNT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    is_active = forms.ChoiceField(
        choices=[('', 'All'), ('true', 'Active'), ('false', 'Inactive')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search accounts...'})
    )

class TransactionFilterForm(forms.Form):
    TRANSACTION_TYPE_CHOICES = [('', 'All Types')] + Transaction.TRANSACTION_TYPES
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    account = forms.ModelChoiceField(
        queryset=Account.objects.filter(is_active=True).order_by('code'),
        required=False,
        empty_label="All Accounts",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    transaction_type = forms.ChoiceField(
        choices=TRANSACTION_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    amount_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Min amount'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search transactions...'})
    )

class JournalEntryForm(forms.ModelForm):
    """Form for creating journal entries"""
    class Meta:
        model = JournalEntry
        fields = ['reference', 'date', 'description', 'notes']
        widgets = {
            'reference': forms.TextInput(attrs={'placeholder': 'Reference number (optional)'}),
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.TextInput(attrs={'placeholder': 'Describe the transaction'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Any notes…'}),
        }

class JournalEntryLineForm(forms.ModelForm):
    """Form for individual journal entry lines"""
    class Meta:
        model = JournalEntryLine
        fields = ['account', 'entry_type', 'amount', 'description']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'description': forms.TextInput(attrs={
                'placeholder': 'Line description',
                'class': 'form-control'
            }),
        }
        

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active accounts
        self.fields['account'].queryset = Account.objects.filter(is_active=True).order_by('code')

# Create formset for journal entry lines
JournalEntryLineFormSet = inlineformset_factory(
    JournalEntry,
    JournalEntryLine,
    fields=('account', 'entry_type', 'amount', 'description'),
    extra=1,
    min_num=1,
    max_num=20,
    can_delete=True,
    validate_min=True
)

class QuickJournalEntryForm(forms.Form):
    """Simplified form for common two-account transactions"""
    date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    description = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))
    reference = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    debit_account = forms.ModelChoiceField(
        queryset=Account.objects.filter(is_active=True).order_by('code'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    credit_account = forms.ModelChoiceField(
        queryset=Account.objects.filter(is_active=True).order_by('code'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    amount = forms.DecimalField(
        max_digits=15, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )

    def clean(self):
        cleaned_data = super().clean()
        debit_account = cleaned_data.get('debit_account')
        credit_account = cleaned_data.get('credit_account')
        
        if debit_account and credit_account and debit_account == credit_account:
            raise forms.ValidationError("Debit and credit accounts must be different.")
        
        return cleaned_data


class SourceDocumentForm(forms.ModelForm):
    """Form for uploading source documents"""
    class Meta:
        model = SourceDocument
        fields = ['title', 'document_type', 'file', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Document title (e.g., Receipt #123)'
            }),
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.gif,.doc,.docx,.xls,.xlsx'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description or notes about this document'
            })
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (limit to 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("File size cannot exceed 10MB.")
            
            # Check file type
            allowed_types = [
                'application/pdf',
                'image/jpeg', 'image/jpg', 'image/png', 'image/gif',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ]
            
            if hasattr(file, 'content_type') and file.content_type not in allowed_types:
                raise forms.ValidationError(
                    "Unsupported file type. Please upload PDF, images, or Office documents."
                )
        
        return file


# Create formset for source documents
SourceDocumentFormSet = inlineformset_factory(
    Transaction,
    SourceDocument,
    form=SourceDocumentForm,
    fields=('title', 'document_type', 'file', 'description'),
    extra=1,
    max_num=5,
    can_delete=True
)

# Formset for journal entry source documents
JournalEntrySourceDocumentFormSet = inlineformset_factory(
    JournalEntry,
    SourceDocument,
    form=SourceDocumentForm,
    fields=('title', 'document_type', 'file', 'description'),
    extra=1,
    max_num=5,
    can_delete=True
)