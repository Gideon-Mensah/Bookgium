from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Sum
from django.http import JsonResponse, HttpResponse
from decimal import Decimal
from datetime import date, timedelta
from .models import Employee, PayrollPeriod, PayrollEntry, PayrollDeduction
from .forms import EmployeeForm, PayrollPeriodForm, PayrollEntryForm
from accounts.models import Account, JournalEntry, JournalEntryLine

def can_access_payroll(user):
    """Check if user can access payroll features"""
    return user.is_authenticated and (user.is_staff or user.is_superuser or user.role == 'hr')

@login_required
def payroll_dashboard(request):
    """Payroll dashboard view"""
    if not can_access_payroll(request.user):
        messages.error(request, "You don't have permission to access payroll.")
        return redirect('dashboard')
    
    # Get current payroll period
    today = date.today()
    current_period = PayrollPeriod.objects.filter(
        start_date__lte=today,
        end_date__gte=today
    ).first()
    
    # Get recent payroll periods
    recent_periods = PayrollPeriod.objects.all()[:5]
    
    # Get employee statistics
    total_employees = Employee.objects.filter(employment_status='active').count()
    total_inactive = Employee.objects.exclude(employment_status='active').count()
    
    # Get payroll statistics for current period
    current_period_stats = {}
    if current_period:
        entries = PayrollEntry.objects.filter(payroll_period=current_period)
        current_period_stats = {
            'total_gross': entries.aggregate(Sum('regular_pay'))['regular_pay__sum'] or 0,
            'total_net': sum(entry.net_pay for entry in entries),
            'employee_count': entries.count()
        }
    
    context = {
        'current_period': current_period,
        'recent_periods': recent_periods,
        'total_employees': total_employees,
        'total_inactive': total_inactive,
        'current_period_stats': current_period_stats,
    }
    
    # Add currency symbol for proper currency display
    from accounts.utils import get_currency_symbol
    context['currency_symbol'] = get_currency_symbol(user=request.user)
    
    return render(request, 'payroll/dashboard.html', context)

# Employee Views
class EmployeeListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Employee
    template_name = 'payroll/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 25
    
    def test_func(self):
        return can_access_payroll(self.request.user)
    
    def get_queryset(self):
        queryset = Employee.objects.all().order_by('last_name', 'first_name')
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(employee_id__icontains=search) |
                Q(email__icontains=search) |
                Q(position__icontains=search)
            )
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(employment_status=status)
        
        return queryset

class EmployeeDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Employee
    template_name = 'payroll/employee_detail.html'
    context_object_name = 'employee'
    
    def test_func(self):
        return can_access_payroll(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.get_object()
        
        # Get recent payroll entries
        recent_entries = PayrollEntry.objects.filter(
            employee=employee
        ).select_related('payroll_period').order_by('-payroll_period__start_date')[:10]
        
        context['recent_entries'] = recent_entries
        return context

class EmployeeCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'payroll/employee_form.html'
    success_url = reverse_lazy('payroll:employee_list')
    
    def test_func(self):
        return can_access_payroll(self.request.user)
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Employee "{form.instance.full_name}" created successfully!')
        return super().form_valid(form)

class EmployeeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'payroll/employee_form.html'
    
    def test_func(self):
        return can_access_payroll(self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, f'Employee "{form.instance.full_name}" updated successfully!')
        return super().form_valid(form)

# Payroll Period Views
class PayrollPeriodListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = PayrollPeriod
    template_name = 'payroll/period_list.html'
    context_object_name = 'periods'
    paginate_by = 20
    
    def test_func(self):
        return can_access_payroll(self.request.user)

class PayrollPeriodDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = PayrollPeriod
    template_name = 'payroll/period_detail.html'
    context_object_name = 'period'
    
    def test_func(self):
        return can_access_payroll(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period = self.get_object()
        
        # Get payroll entries for this period
        entries = PayrollEntry.objects.filter(
            payroll_period=period
        ).select_related('employee').order_by('employee__last_name')
        
        context['entries'] = entries
        context['total_gross'] = sum(entry.gross_pay for entry in entries)
        context['total_net'] = sum(entry.net_pay for entry in entries)
        
        # Add currency symbol for proper currency display
        from accounts.utils import get_currency_symbol
        context['currency_symbol'] = get_currency_symbol(user=self.request.user)
        
        return context

class PayrollPeriodCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = PayrollPeriod
    form_class = PayrollPeriodForm
    template_name = 'payroll/period_form.html'
    success_url = reverse_lazy('payroll:period_list')
    
    def test_func(self):
        return can_access_payroll(self.request.user)
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Payroll period "{form.instance.name}" created successfully!')
        return super().form_valid(form)

@login_required
def process_payroll(request, period_id):
    """Process payroll for a specific period"""
    if not can_access_payroll(request.user):
        messages.error(request, "You don't have permission to process payroll.")
        return redirect('payroll:dashboard')
    
    period = get_object_or_404(PayrollPeriod, id=period_id)
    
    if request.method == 'POST':
        # Get all active employees
        active_employees = Employee.objects.filter(employment_status='active')
        
        created_count = 0
        for employee in active_employees:
            # Check if entry already exists
            entry, created = PayrollEntry.objects.get_or_create(
                employee=employee,
                payroll_period=period,
                defaults={
                    'regular_hours': 40 if employee.employment_type == 'full_time' else 20,
                    'regular_pay': employee.base_salary if employee.base_salary else employee.hourly_rate * 40,
                    'created_by': request.user
                }
            )
            
            if created:
                # Calculate taxes
                entry.calculate_taxes()
                created_count += 1
        
        if created_count > 0:
            messages.success(request, f'Created payroll entries for {created_count} employees.')
        else:
            messages.info(request, 'All payroll entries already exist for this period.')
        
        return redirect('payroll:period_detail', pk=period.pk)
    
    context = {
        'period': period,
        'active_employees': Employee.objects.filter(employment_status='active'),
    }
    
    return render(request, 'payroll/process_payroll.html', context)

@login_required
def create_payroll_journal_entries(request, period_id):
    """Create journal entries for payroll"""
    if not can_access_payroll(request.user):
        messages.error(request, "You don't have permission to create journal entries.")
        return redirect('payroll:dashboard')
    
    period = get_object_or_404(PayrollPeriod, id=period_id)
    entries = PayrollEntry.objects.filter(payroll_period=period)
    
    if not entries.exists():
        messages.error(request, "No payroll entries found for this period.")
        return redirect('payroll:period_detail', pk=period.pk)
    
    # Calculate totals
    total_gross = sum(entry.gross_pay for entry in entries)
    total_net = sum(entry.net_pay for entry in entries)
    total_deductions = total_gross - total_net
    
    try:
        # Get payroll accounts (you'll need to create these)
        salary_expense = Account.objects.get(code='5100')  # Salary Expense
        payroll_liability = Account.objects.get(code='2100')  # Payroll Liability
        cash_account = Account.objects.get(code='1000')  # Cash
        
        # Create journal entry
        journal_entry = JournalEntry.objects.create(
            date=period.pay_date,
            description=f"Payroll for {period.name}",
            reference=f"PAY-{period.id}",
            created_by=request.user,
            is_posted=True
        )
        
        # Debit salary expense
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            account=salary_expense,
            entry_type='debit',
            amount=total_gross,
            description=f"Salary expense for {period.name}"
        )
        
        # Credit payroll liability (for deductions)
        if total_deductions > 0:
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                account=payroll_liability,
                entry_type='credit',
                amount=total_deductions,
                description=f"Payroll deductions for {period.name}"
            )
        
        # Credit cash (net pay)
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            account=cash_account,
            entry_type='credit',
            amount=total_net,
            description=f"Net payroll payment for {period.name}"
        )
        
        # Update payroll entries to reference the journal entry
        entries.update(journal_entry=journal_entry)
        
        messages.success(request, f'Journal entry created successfully! Entry ID: {journal_entry.id}')
        
    except Account.DoesNotExist as e:
        messages.error(request, f'Required payroll account not found. Please create accounts with codes: 5100 (Salary Expense), 2100 (Payroll Liability), 1000 (Cash)')
    except Exception as e:
        messages.error(request, f'Error creating journal entry: {str(e)}')
    
    return redirect('payroll:period_detail', pk=period.pk)
