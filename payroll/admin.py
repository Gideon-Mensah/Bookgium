from django.contrib import admin
from .models import Employee, PayrollPeriod, PayrollEntry, PayrollDeduction

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'full_name', 'position', 'department', 'employment_status', 'hire_date']
    list_filter = ['employment_status', 'employment_type', 'department', 'pay_frequency']
    search_fields = ['employee_id', 'first_name', 'last_name', 'email', 'position']
    ordering = ['last_name', 'first_name']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('employee_id', 'first_name', 'last_name', 'email', 'phone', 'address', 'date_of_birth')
        }),
        ('Employment Details', {
            'fields': ('hire_date', 'termination_date', 'employment_status', 'employment_type', 
                      'department', 'position')
        }),
        ('Compensation', {
            'fields': ('base_salary', 'hourly_rate', 'pay_frequency')
        }),
        ('Tax Information', {
            'fields': ('tax_id', 'tax_exemptions')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']

@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = ['name', 'period_type', 'start_date', 'end_date', 'pay_date', 'status']
    list_filter = ['period_type', 'status', 'start_date']
    search_fields = ['name']
    ordering = ['-start_date']
    
    readonly_fields = ['created_at', 'updated_at']

@admin.register(PayrollEntry)
class PayrollEntryAdmin(admin.ModelAdmin):
    list_display = ['employee', 'payroll_period', 'gross_pay', 'total_deductions', 'net_pay']
    list_filter = ['payroll_period__status', 'payroll_period__period_type']
    search_fields = ['employee__first_name', 'employee__last_name', 'employee__employee_id']
    ordering = ['-payroll_period__start_date', 'employee__last_name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('employee', 'payroll_period')
        }),
        ('Hours and Earnings', {
            'fields': ('regular_hours', 'overtime_hours', 'regular_pay', 'overtime_pay', 
                      'bonus', 'commission')
        }),
        ('Deductions', {
            'fields': ('federal_tax', 'state_tax', 'social_security', 'medicare', 
                      'health_insurance', 'retirement_401k', 'other_deductions')
        }),
        ('Additional Information', {
            'fields': ('notes', 'journal_entry')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']

@admin.register(PayrollDeduction)
class PayrollDeductionAdmin(admin.ModelAdmin):
    list_display = ['name', 'deduction_type', 'amount', 'is_percentage', 'is_active']
    list_filter = ['deduction_type', 'is_percentage', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['deduction_type', 'name']
