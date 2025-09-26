from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import ModelForm
from django import forms
from .models import CompanySettings

class CompanySettingsForm(ModelForm):
    class Meta:
        model = CompanySettings
        fields = ['organization_name', 'organization_address', 'organization_phone',
                 'organization_email', 'organization_website', 'organization_logo',
                 'fiscal_year_start', 'currency', 'tax_rate']
        widgets = {
            'organization_name': forms.TextInput(attrs={'class': 'form-control'}),
            'organization_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'organization_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'organization_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'organization_website': forms.URLInput(attrs={'class': 'form-control'}),
            'organization_logo': forms.FileInput(attrs={'class': 'form-control'}),
            'fiscal_year_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

@login_required
def company_settings(request):
    """View to manage company settings"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access company settings.")
        return redirect('dashboard')
    
    # Get or create company settings
    settings_obj, created = CompanySettings.objects.get_or_create(
        defaults={
            'organization_name': 'Your Organization Name',
            'fiscal_year_start': '2024-01-01',
            'currency': 'USD',
            'tax_rate': 0.00
        }
    )
    
    if request.method == 'POST':
        form = CompanySettingsForm(request.POST, request.FILES, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company settings updated successfully.')
            return redirect('settings:company_settings')
    else:
        form = CompanySettingsForm(instance=settings_obj)
    
    return render(request, 'settings/company_settings.html', {
        'form': form,
        'settings': settings_obj
    })
