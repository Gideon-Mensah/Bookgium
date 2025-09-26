from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from .models import Account


class OpeningBalanceForm(forms.Form):
    """Form for setting up opening balances for multiple accounts"""
    
    opening_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        initial=date.today,
        help_text="Date to use as the opening balance date for all accounts"
    )
    
    method = forms.ChoiceField(
        choices=[
            ('manual', 'Manual Entry'),
            ('calculate', 'Calculate from Existing Transactions'),
            ('import', 'Import from CSV'),
            ('zero', 'Set All to Zero'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='manual',
        help_text="Method to use for setting opening balances"
    )
    
    cutoff_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        help_text="For 'calculate' method: calculate balances up to this date"
    )
    
    csv_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        }),
        help_text="For 'import' method: CSV file with account_code,opening_balance columns"
    )
    
    create_journal_entry = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Create a journal entry for the opening balances"
    )

    def clean(self):
        cleaned_data = super().clean()
        method = cleaned_data.get('method')
        
        if method == 'calculate' and not cleaned_data.get('cutoff_date'):
            raise ValidationError({
                'cutoff_date': 'Cutoff date is required for calculate method'
            })
        
        if method == 'import' and not cleaned_data.get('csv_file'):
            raise ValidationError({
                'csv_file': 'CSV file is required for import method'
            })
        
        return cleaned_data


class BulkOpeningBalanceForm(forms.Form):
    """Form for bulk editing opening balances with individual account entries"""
    
    opening_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        initial=date.today,
        help_text="Date to use as the opening balance date"
    )
    
    def __init__(self, *args, **kwargs):
        accounts = kwargs.pop('accounts', Account.objects.filter(is_active=True))
        super().__init__(*args, **kwargs)
        
        # Add a field for each account
        for account in accounts:
            field_name = f'balance_{account.pk}'
            self.fields[field_name] = forms.DecimalField(
                required=False,
                decimal_places=2,
                max_digits=15,
                initial=account.opening_balance or Decimal('0.00'),
                widget=forms.NumberInput(attrs={
                    'class': 'form-control',
                    'step': '0.01',
                    'placeholder': '0.00'
                }),
                label=f'{account.code} - {account.name}'
            )
            
            # Store account info for processing
            self.fields[field_name].account = account
    
    def get_account_fields(self):
        """Get fields that represent account balances"""
        return [(name, field) for name, field in self.fields.items() 
                if name.startswith('balance_') and hasattr(field, 'account')]


class CSVOpeningBalanceUploadForm(forms.Form):
    """Simple form for CSV upload"""
    
    csv_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        }),
        help_text="CSV file with columns: account_code, opening_balance"
    )
    
    opening_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        initial=date.today,
        help_text="Date to use as the opening balance date"
    )
    
    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        
        # Validate file extension
        if not csv_file.name.endswith('.csv'):
            raise ValidationError('File must be a CSV file')
        
        # Validate file size (5MB limit)
        if csv_file.size > 5 * 1024 * 1024:
            raise ValidationError('File size must be less than 5MB')
        
        return csv_file


class SingleAccountOpeningBalanceForm(forms.ModelForm):
    """Form for editing opening balance of a single account"""
    
    class Meta:
        model = Account
        fields = ['opening_balance', 'opening_balance_date']
        widgets = {
            'opening_balance': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'opening_balance_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default date if not set
        if not self.instance.opening_balance_date:
            self.fields['opening_balance_date'].initial = date.today()
        
        # Make opening balance date required
        self.fields['opening_balance_date'].required = True
