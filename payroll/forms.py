from django import forms
from django.core.validators import MinValueValidator
from decimal import Decimal
from .models import Employee, PayrollPeriod, PayrollEntry, PayrollDeduction

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'employee_id', 'first_name', 'last_name', 'email', 'phone',
            'address', 'date_of_birth', 'hire_date', 'position', 'department', 
            'employment_type', 'employment_status', 'base_salary', 'hourly_rate',
            'pay_frequency', 'tax_id', 'tax_exemptions'
        ]
        
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hire_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'employment_type': forms.Select(attrs={'class': 'form-control'}),
            'employment_status': forms.Select(attrs={'class': 'form-control'}),
            'pay_frequency': forms.Select(attrs={'class': 'form-control'}),
            'base_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SSN or Tax ID'}),
            'tax_exemptions': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        employment_type = cleaned_data.get('employment_type')
        base_salary = cleaned_data.get('base_salary')
        hourly_rate = cleaned_data.get('hourly_rate')
        
        # Validation based on employment type
        if employment_type == 'full_time':
            if not base_salary or base_salary <= 0:
                raise forms.ValidationError("Full-time employees must have a valid base salary.")
        
        if employment_type in ['part_time', 'contract', 'intern']:
            if not hourly_rate or hourly_rate <= 0:
                raise forms.ValidationError("Part-time, contract, and intern employees must have a valid hourly rate.")
        
        return cleaned_data

class PayrollPeriodForm(forms.ModelForm):
    class Meta:
        model = PayrollPeriod
        fields = ['name', 'start_date', 'end_date', 'pay_date', 'period_type', 'status']
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'pay_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'period_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        pay_date = cleaned_data.get('pay_date')
        
        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError("End date must be after start date.")
        
        if pay_date and end_date and pay_date < end_date:
            raise forms.ValidationError("Pay date should not be before the end date.")
        
        return cleaned_data

class PayrollEntryForm(forms.ModelForm):
    class Meta:
        model = PayrollEntry
        fields = [
            'employee', 'payroll_period', 'regular_hours', 'overtime_hours',
            'regular_pay', 'overtime_pay', 'bonus', 'commission',
            'federal_tax', 'state_tax', 'social_security', 'medicare',
            'health_insurance', 'retirement_401k', 'other_deductions', 'notes'
        ]
        
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'payroll_period': forms.Select(attrs={'class': 'form-control'}),
            'regular_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25'}),
            'overtime_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25'}),
            'regular_pay': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'overtime_pay': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'bonus': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'commission': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'federal_tax': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'state_tax': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'social_security': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'medicare': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'health_insurance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'retirement_401k': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'other_deductions': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        regular_hours = cleaned_data.get('regular_hours', 0)
        overtime_hours = cleaned_data.get('overtime_hours', 0)
        
        if regular_hours < 0:
            raise forms.ValidationError("Regular hours cannot be negative.")
        
        if overtime_hours < 0:
            raise forms.ValidationError("Overtime hours cannot be negative.")
        
        if regular_hours + overtime_hours > 168:  # Max hours in a week
            raise forms.ValidationError("Total hours cannot exceed 168 hours per week.")
        
        return cleaned_data

class PayrollDeductionForm(forms.ModelForm):
    class Meta:
        model = PayrollDeduction
        fields = ['name', 'deduction_type', 'is_percentage', 'amount', 'is_active', 'description']
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'deduction_type': forms.Select(attrs={'class': 'form-control'}),
            'is_percentage': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        is_percentage = cleaned_data.get('is_percentage')
        amount = cleaned_data.get('amount')
        
        if not amount or amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0.")
        
        if is_percentage and amount > 100:
            raise forms.ValidationError("Percentage cannot be greater than 100.")
        
        return cleaned_data

class PayrollReportForm(forms.Form):
    """Form for generating payroll reports"""
    REPORT_TYPES = [
        ('summary', 'Payroll Summary'),
        ('detail', 'Detailed Payroll Report'),
        ('tax_summary', 'Tax Summary'),
        ('employee_summary', 'Employee Summary'),
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    employees = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.filter(employment_status='active'),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '10'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Start date must be before end date.")
        
        return cleaned_data
