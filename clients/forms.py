from django import forms
from .models import Client, ClientNote

class ClientForm(forms.ModelForm):
    """Form for creating and updating clients"""
    
    class Meta:
        model = Client
        fields = [
            'name', 'email', 'phone', 'website', 'company_type',
            'registration_number', 'tax_id', 'contact_person', 'contact_title',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country',
            'status', 'credit_limit', 'payment_terms', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Client/Company Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'client@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1-555-123-4567'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
            'company_type': forms.Select(attrs={'class': 'form-select'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Registration Number'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tax ID/VAT Number'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Person Name'}),
            'contact_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Job Title'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street Address'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apartment, Suite, etc.'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State/Province'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postal Code'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'payment_terms': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Net 30 days'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Additional notes about this client...'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            # Check for duplicate email, excluding current instance
            queryset = Client.objects.filter(email=email)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise forms.ValidationError("A client with this email already exists.")
        return email
    
    def clean_credit_limit(self):
        credit_limit = self.cleaned_data.get('credit_limit')
        if credit_limit and credit_limit < 0:
            raise forms.ValidationError("Credit limit cannot be negative.")
        return credit_limit

class ClientNoteForm(forms.ModelForm):
    """Form for adding notes to clients"""
    
    class Meta:
        model = ClientNote
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Note title...'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 5, 
                'placeholder': 'Enter your note here...'
            }),
        }

class ClientSearchForm(forms.Form):
    """Form for searching clients"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, email, phone...',
            'id': 'client-search'
        })
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('all', 'All Status')] + Client.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    company_type = forms.ChoiceField(
        required=False,
        choices=[('all', 'All Types')] + Client.COMPANY_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
