from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from .models import Client, Domain, ClientContact

class ClientForm(forms.ModelForm):
    """Form for creating and editing clients"""
    
    class Meta:
        model = Client
        fields = [
            'name', 'slug', 'description', 'email', 'phone', 'website',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country',
            'subscription_status', 'plan_type', 'paid_until', 'on_trial', 'trial_ends',
            'currency', 'monthly_fee', 'max_users', 'max_invoices_per_month', 'max_storage_gb',
            'account_manager', 'primary_color', 'notes'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter client organization name'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'url-friendly-name (auto-generated if left blank)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of the organization'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@company.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 (555) 123-4567'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.company.com'
            }),
            'address_line1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '123 Main Street'
            }),
            'address_line2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Suite 100'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'New York'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'NY'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '10001'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'subscription_status': forms.Select(attrs={'class': 'form-select'}),
            'plan_type': forms.Select(attrs={'class': 'form-select'}),
            'paid_until': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'on_trial': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'trial_ends': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'monthly_fee': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'max_users': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'max_invoices_per_month': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'max_storage_gb': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'account_manager': forms.Select(attrs={'class': 'form-select'}),
            'primary_color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Internal notes about this client...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default dates
        if not self.instance.pk:  # New client
            self.fields['paid_until'].initial = timezone.now().date() + timedelta(days=30)
            self.fields['trial_ends'].initial = timezone.now().date() + timedelta(days=30)
        
        # Filter account managers (admin users only)
        from users.models import CustomUser
        self.fields['account_manager'].queryset = CustomUser.objects.filter(
            role__in=['admin', 'manager']
        ).order_by('first_name', 'last_name')
        self.fields['account_manager'].empty_label = "Select an account manager"
    
    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if not slug:
            # Auto-generate slug from name
            name = self.cleaned_data.get('name', '')
            slug = name.lower().replace(' ', '-').replace('&', 'and')
            # Remove special characters
            import re
            slug = re.sub(r'[^a-z0-9\-]', '', slug)
            slug = re.sub(r'-+', '-', slug).strip('-')
        
        # Check for uniqueness
        if Client.objects.filter(slug=slug).exclude(pk=self.instance.pk).exists():
            raise ValidationError(f'A client with slug "{slug}" already exists.')
        
        return slug
    
    def clean(self):
        cleaned_data = super().clean()
        paid_until = cleaned_data.get('paid_until')
        on_trial = cleaned_data.get('on_trial')
        trial_ends = cleaned_data.get('trial_ends')
        
        # Validate trial dates
        if on_trial and not trial_ends:
            raise ValidationError('Trial end date is required when client is on trial.')
        
        # Validate subscription dates
        if paid_until and paid_until < timezone.now().date():
            cleaned_data['subscription_status'] = 'expired'
        
        return cleaned_data

class DomainForm(forms.ModelForm):
    """Form for adding/editing domains"""
    
    class Meta:
        model = Domain
        fields = ['domain', 'is_primary', 'is_active', 'ssl_enabled']
        
        widgets = {
            'domain': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'client.bookgium.com'
            }),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ssl_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_domain(self):
        domain = self.cleaned_data.get('domain', '').lower().strip()
        
        # Basic domain validation
        import re
        if not re.match(r'^[a-z0-9.-]+\.[a-z]{2,}$', domain):
            raise ValidationError('Please enter a valid domain name.')
        
        # Check for uniqueness
        if Domain.objects.filter(domain=domain).exclude(pk=self.instance.pk).exists():
            raise ValidationError(f'Domain "{domain}" is already in use.')
        
        return domain

class ClientContactForm(forms.ModelForm):
    """Form for adding/editing client contacts"""
    
    class Meta:
        model = ClientContact
        fields = [
            'first_name', 'last_name', 'email', 'phone', 
            'role', 'title', 'is_primary', 'is_active'
        ]
        
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'John'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Doe'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'john.doe@company.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 (555) 123-4567'
            }),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'CEO, CTO, Manager, etc.'
            }),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ClientSearchForm(forms.Form):
    """Form for searching and filtering clients"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search clients...'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + Client.SUBSCRIPTION_STATUS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    plan = forms.ChoiceField(
        required=False,
        choices=[('', 'All Plans')] + Client.PLAN_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    active = forms.ChoiceField(
        required=False,
        choices=[('', 'All'), ('true', 'Active Only'), ('false', 'Inactive Only')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    currency = forms.ChoiceField(
        required=False,
        choices=[('', 'All Currencies')] + Client.CURRENCY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class ExtendTrialForm(forms.Form):
    """Form for extending client trial period"""
    
    days = forms.IntegerField(
        min_value=1,
        max_value=365,
        initial=30,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '365'
        })
    )
    
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Reason for extension (optional)...'
        })
    )
