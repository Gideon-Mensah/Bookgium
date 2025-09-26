from django import forms
from django.utils import timezone
from datetime import datetime, timedelta
from .models import ReportTemplate, ReportSchedule

class ReportTemplateForm(forms.ModelForm):
    """Form for creating and editing report templates"""
    
    class Meta:
        model = ReportTemplate
        fields = ['name', 'report_type', 'description', 'is_public']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter report name'
            }),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter report description'
            }),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ReportScheduleForm(forms.ModelForm):
    """Form for scheduling automatic reports"""
    
    class Meta:
        model = ReportSchedule
        fields = ['name', 'template', 'frequency', 'recipients', 'start_date', 'end_date']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter schedule name'
            }),
            'template': forms.Select(attrs={'class': 'form-select'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'value': timezone.now().date()
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    recipients = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter email addresses separated by commas'
        }),
        help_text="Enter email addresses separated by commas"
    )
    
    def clean_recipients(self):
        recipients_text = self.cleaned_data.get('recipients', '')
        if recipients_text:
            # Split by comma and validate emails
            emails = [email.strip() for email in recipients_text.split(',')]
            validated_emails = []
            
            for email in emails:
                if email:  # Skip empty strings
                    forms.EmailField().clean(email)  # This will raise ValidationError if invalid
                    validated_emails.append(email)
            
            return validated_emails
        return []

class ReportFiltersForm(forms.Form):
    """Generic form for report filters"""
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='From Date'
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='To Date'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default date range to current month
        today = timezone.now().date()
        first_day = today.replace(day=1)
        
        self.fields['date_from'].initial = first_day
        self.fields['date_to'].initial = today

class InvoiceReportFiltersForm(ReportFiltersForm):
    """Extended filters for invoice reports"""
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses'), ('draft', 'Draft'), ('sent', 'Sent'), ('paid', 'Paid'), ('overdue', 'Overdue'), ('cancelled', 'Cancelled')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Invoice Status'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Import here to avoid circular imports
        from invoices.models import Customer
        
        self.fields['customer'] = forms.ModelChoiceField(
            queryset=Customer.objects.filter(is_active=True).order_by('name'),
            required=False,
            empty_label='All Customers',
            widget=forms.Select(attrs={'class': 'form-select'}),
            label='Customer'
        )

class FinancialReportFiltersForm(ReportFiltersForm):
    """Extended filters for financial reports"""
    
    ACCOUNT_TYPE_CHOICES = [
        ('', 'All Account Types'),
        ('asset', 'Assets'),
        ('liability', 'Liabilities'),
        ('equity', 'Equity'),
        ('income', 'Income'),
        ('expense', 'Expenses'),
    ]
    
    account_type = forms.ChoiceField(
        choices=ACCOUNT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Account Type'
    )
    
    show_zero_balances = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Show accounts with zero balances'
    )

class CustomerReportFiltersForm(ReportFiltersForm):
    """Extended filters for customer reports"""
    
    include_payments = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Include payment details'
    )
    
    include_overdue_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Show overdue invoices only'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Import here to avoid circular imports
        from invoices.models import Customer
        
        self.fields['customer'] = forms.ModelChoiceField(
            queryset=Customer.objects.filter(is_active=True).order_by('name'),
            required=True,
            widget=forms.Select(attrs={'class': 'form-select'}),
            label='Customer'
        )

class DateRangeForm(forms.Form):
    """Simple date range form for various reports"""
    
    as_of_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'value': timezone.now().date()
        }),
        label='As of Date',
        initial=timezone.now().date()
    )
