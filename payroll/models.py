from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid
from datetime import date

class Employee(models.Model):
    EMPLOYMENT_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('terminated', 'Terminated'),
        ('on_leave', 'On Leave')
    ]
    
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('intern', 'Intern')
    ]
    
    PAY_FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('bi_weekly', 'Bi-Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly')
    ]
    
    # Personal Information
    employee_id = models.CharField(max_length=20, unique=True, help_text="Unique employee identifier")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    # Employment Information
    hire_date = models.DateField()
    termination_date = models.DateField(blank=True, null=True)
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS_CHOICES, default='active')
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default='full_time')
    department = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=100)
    
    # Compensation
    base_salary = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    pay_frequency = models.CharField(max_length=20, choices=PAY_FREQUENCY_CHOICES, default='monthly')
    
    # Tax Information
    tax_id = models.CharField(max_length=20, blank=True, null=True, help_text="Social Security Number or Tax ID")
    tax_exemptions = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # Metadata
    created_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
        
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_active(self):
        return self.employment_status == 'active'
    
    def get_absolute_url(self):
        return reverse('payroll:employee_detail', kwargs={'pk': self.pk})

class PayrollPeriod(models.Model):
    PERIOD_TYPE_CHOICES = [
        ('weekly', 'Weekly'),
        ('bi_weekly', 'Bi-Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly')
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('approved', 'Approved'),
        ('paid', 'Paid')
    ]
    
    name = models.CharField(max_length=100, help_text="e.g., 'January 2024' or 'Week 12-2024'")
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    pay_date = models.DateField(help_text="Date when employees will be paid")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Metadata
    created_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        unique_together = ['period_type', 'start_date', 'end_date']
        
    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"
    
    @property
    def is_current(self):
        today = date.today()
        return self.start_date <= today <= self.end_date
    
    @property
    def total_gross_pay(self):
        return sum(entry.gross_pay for entry in self.payroll_entries.all())
    
    @property
    def total_net_pay(self):
        return sum(entry.net_pay for entry in self.payroll_entries.all())
    
    def get_absolute_url(self):
        return reverse('payroll:period_detail', kwargs={'pk': self.pk})

class PayrollEntry(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payroll_entries')
    payroll_period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='payroll_entries')
    
    # Hours and Pay
    regular_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    overtime_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    regular_pay = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    overtime_pay = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    commission = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Deductions
    federal_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    state_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    social_security = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    medicare = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    health_insurance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    retirement_401k = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    # Journal Entry Reference
    journal_entry = models.ForeignKey('accounts.JournalEntry', on_delete=models.SET_NULL, 
                                    null=True, blank=True, related_name='payroll_entries')
    
    # Metadata
    created_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-payroll_period__start_date', 'employee__last_name']
        unique_together = ['employee', 'payroll_period']
        
    def __str__(self):
        return f"{self.employee.full_name} - {self.payroll_period.name}"
    
    @property
    def gross_pay(self):
        """Calculate total gross pay"""
        return self.regular_pay + self.overtime_pay + self.bonus + self.commission
    
    @property
    def total_deductions(self):
        """Calculate total deductions"""
        return (self.federal_tax + self.state_tax + self.social_security + 
                self.medicare + self.health_insurance + self.retirement_401k + 
                self.other_deductions)
    
    @property
    def net_pay(self):
        """Calculate net pay after deductions"""
        return self.gross_pay - self.total_deductions
    
    def calculate_taxes(self):
        """Calculate tax deductions based on gross pay"""
        gross = self.gross_pay
        
        # Simple tax calculations (you can make these more sophisticated)
        self.social_security = gross * Decimal('0.062')  # 6.2%
        self.medicare = gross * Decimal('0.0145')  # 1.45%
        
        # Federal tax (simplified - should be based on tax brackets)
        self.federal_tax = gross * Decimal('0.12')  # 12% bracket
        
        # State tax (simplified - varies by state)
        self.state_tax = gross * Decimal('0.05')  # 5%
        
        self.save()
    
    def get_absolute_url(self):
        return reverse('payroll:entry_detail', kwargs={'pk': self.pk})

class PayrollDeduction(models.Model):
    DEDUCTION_TYPE_CHOICES = [
        ('tax', 'Tax'),
        ('insurance', 'Insurance'),
        ('retirement', 'Retirement'),
        ('loan', 'Loan Repayment'),
        ('garnishment', 'Wage Garnishment'),
        ('other', 'Other')
    ]
    
    name = models.CharField(max_length=100)
    deduction_type = models.CharField(max_length=20, choices=DEDUCTION_TYPE_CHOICES)
    is_percentage = models.BooleanField(default=False, help_text="If true, amount is percentage of gross pay")
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.is_percentage:
            return f"{self.name} ({self.amount}%)"
        return f"{self.name} (${self.amount})"
    
    class Meta:
        ordering = ['deduction_type', 'name']
