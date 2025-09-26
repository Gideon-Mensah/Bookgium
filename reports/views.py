from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from accounts.models import Account, Transaction, JournalEntry, JournalEntryLine
from invoices.models import Invoice, Customer, Payment
from .models import ReportTemplate, ReportSchedule, GeneratedReport
from .forms import ReportTemplateForm, ReportScheduleForm, ReportFiltersForm

def can_access_reports(user):
    """Check if user can access reports features (everyone except HR)"""
    return user.is_authenticated and (user.role != 'hr' or user.is_superuser)

def calculate_account_balance_for_period(account, from_date, to_date=None):
    """
    Calculate account balance for a specific period.
    For trial balance: calculates balance including opening balance + period activity
    For balance sheet: calculates balance up to the as_of_date (to_date)
    For income statement: calculates period activity only
    """
    # Start with the account's opening balance
    opening_balance = account.opening_balance or Decimal('0')
    
    # If we need balance up to a date (balance sheet), include all transactions up to that date
    if to_date and not from_date:
        # Balance sheet case: all transactions up to as_of_date
        journal_lines = JournalEntryLine.objects.filter(
            account=account,
            journal_entry__date__lte=to_date,
            journal_entry__is_posted=True
        )
    elif from_date and to_date:
        # Trial balance case: opening balance + transactions in period
        # First get transactions before the period for dynamic opening balance
        pre_period_lines = JournalEntryLine.objects.filter(
            account=account,
            journal_entry__date__lt=from_date,
            journal_entry__is_posted=True
        )
        
        # Add pre-period effect to opening balance based on account type
        pre_period_debits = pre_period_lines.filter(entry_type='debit').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        pre_period_credits = pre_period_lines.filter(entry_type='credit').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        if account.account_type in ['asset', 'expense']:
            # For assets and expenses: debits increase balance, credits decrease balance
            pre_period_effect = pre_period_debits - pre_period_credits
        else:
            # For liabilities, equity, and income: credits increase balance, debits decrease balance
            pre_period_effect = pre_period_credits - pre_period_debits
            
        opening_balance += pre_period_effect
        
        # Get period transactions
        journal_lines = JournalEntryLine.objects.filter(
            account=account,
            journal_entry__date__gte=from_date,
            journal_entry__date__lte=to_date,
            journal_entry__is_posted=True
        )
    elif from_date and not to_date:
        # Income statement case: period activity only, starting from calculated opening balance
        pre_period_lines = JournalEntryLine.objects.filter(
            account=account,
            journal_entry__date__lt=from_date,
            journal_entry__is_posted=True
        )
        
        # Calculate dynamic opening balance based on account type
        pre_period_debits = pre_period_lines.filter(entry_type='debit').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        pre_period_credits = pre_period_lines.filter(entry_type='credit').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        if account.account_type in ['asset', 'expense']:
            pre_period_effect = pre_period_debits - pre_period_credits
        else:
            pre_period_effect = pre_period_credits - pre_period_debits
            
        opening_balance += pre_period_effect
        
        # Get period transactions from from_date onwards
        journal_lines = JournalEntryLine.objects.filter(
            account=account,
            journal_entry__date__gte=from_date,
            journal_entry__is_posted=True
        )
    else:
        # Default case: all transactions
        journal_lines = JournalEntryLine.objects.filter(
            account=account,
            journal_entry__is_posted=True
        )
    
    # Calculate period activity using entry_type and amount
    period_debits = journal_lines.filter(entry_type='debit').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    period_credits = journal_lines.filter(entry_type='credit').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    # Calculate final balance and period effect based on account type
    if account.account_type in ['asset', 'expense']:
        # For assets and expenses: debits increase balance, credits decrease balance
        period_effect = period_debits - period_credits
        final_balance = opening_balance + period_effect
    else:
        # For liabilities, equity, and income: credits increase balance, debits decrease balance
        period_effect = period_credits - period_debits
        final_balance = opening_balance + period_effect
    
    return {
        'opening_balance': opening_balance,
        'period_debits': period_debits,
        'period_credits': period_credits,
        'period_effect': period_effect,
        'final_balance': final_balance
    }

@login_required
@user_passes_test(can_access_reports)
def reports_dashboard(request):
    """Main reports dashboard with overview and quick access"""
    context = {
        'total_templates': ReportTemplate.objects.filter(
            Q(created_by=request.user) | Q(is_public=True)
        ).count(),
        'scheduled_reports': ReportSchedule.objects.filter(
            created_by=request.user, status='active'
        ).count(),
        'recent_reports': GeneratedReport.objects.filter(
            generated_by=request.user
        )[:5],
        'quick_stats': get_quick_stats(request.user),
    }
    return render(request, 'reports/dashboard.html', context)

def get_quick_stats(user):
    """Get quick statistics for dashboard"""
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    # Invoice statistics
    total_invoices = Invoice.objects.count()
    paid_invoices = Invoice.objects.filter(status='paid').count()
    overdue_invoices = Invoice.objects.filter(
        status='sent', due_date__lt=today
    ).count()
    
    # Revenue statistics
    total_revenue = Invoice.objects.filter(status='paid').aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0')
    
    monthly_revenue = Invoice.objects.filter(
        status='paid', paid_date__gte=thirty_days_ago
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    # Customer statistics
    total_customers = Customer.objects.count()
    active_customers = Customer.objects.filter(is_active=True).count()
    
    return {
        'total_invoices': total_invoices,
        'paid_invoices': paid_invoices,
        'overdue_invoices': overdue_invoices,
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'total_customers': total_customers,
        'active_customers': active_customers,
    }

# Financial Reports
@login_required
def trial_balance(request):
    """Generate trial balance report"""
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Default to current month if no dates provided
    if not date_from or not date_to:
        today = timezone.now().date()
        date_from = today.replace(day=1)
        date_to = today
    else:
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
    
    accounts = Account.objects.filter(is_active=True).order_by('code')
    trial_balance_data = []
    total_debits = Decimal('0')
    total_credits = Decimal('0')
    
    for account in accounts:
        # Calculate balance using the new helper function
        balance_info = calculate_account_balance_for_period(account, date_from, date_to)
        
        # Determine debit/credit balances based on account type
        if account.account_type in ['asset', 'expense']:
            # Assets and Expenses: Positive balance = Debit, Negative balance = Credit
            debit_balance = balance_info['final_balance'] if balance_info['final_balance'] > 0 else Decimal('0')
            credit_balance = abs(balance_info['final_balance']) if balance_info['final_balance'] < 0 else Decimal('0')
        else:
            # Liabilities, Equity, and Revenue: Positive balance = Credit, Negative balance = Debit
            credit_balance = balance_info['final_balance'] if balance_info['final_balance'] > 0 else Decimal('0')
            debit_balance = abs(balance_info['final_balance']) if balance_info['final_balance'] < 0 else Decimal('0')
        
        # Include accounts with any balance or activity
        if (debit_balance > 0 or credit_balance > 0 or 
            balance_info['period_debits'] > 0 or balance_info['period_credits'] > 0):
            trial_balance_data.append({
                'account': account,
                'debit_balance': debit_balance,
                'credit_balance': credit_balance,
                'total_debits': balance_info['period_debits'],
                'total_credits': balance_info['period_credits'],
                'opening_balance': balance_info['opening_balance'],
            })
            
            total_debits += debit_balance
            total_credits += credit_balance
    
    context = {
        'trial_balance_data': trial_balance_data,
        'total_debits': total_debits,
        'total_credits': total_credits,
        'date_from': date_from,
        'date_to': date_to,
        'is_balanced': total_debits == total_credits,
    }
    
    return render(request, 'reports/trial_balance.html', context)

@login_required
def income_statement(request):
    """Generate income statement (P&L)"""
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Default to current month if no dates provided
    if not date_from or not date_to:
        today = timezone.now().date()
        date_from = today.replace(day=1)
        date_to = today
    else:
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
    
    # Get income and expense accounts
    income_accounts = Account.objects.filter(
        account_type='income', is_active=True
    ).order_by('code')
    
    expense_accounts = Account.objects.filter(
        account_type='expense', is_active=True
    ).order_by('code')
    
    income_data = []
    expense_data = []
    total_income = Decimal('0')
    total_expenses = Decimal('0')
    
    # Calculate income using the helper function
    for account in income_accounts:
        balance_info = calculate_account_balance_for_period(account, date_from, date_to)
        
        # For income accounts, credits increase income
        # The period effect already considers debits - credits
        # For income accounts, we want credits - debits (reverse of the calculation)
        income_amount = balance_info['period_credits'] - balance_info['period_debits']
        
        if income_amount > 0:
            income_data.append({
                'account': account,
                'amount': income_amount,
            })
            total_income += income_amount
    
    # Calculate expenses using the helper function
    for account in expense_accounts:
        balance_info = calculate_account_balance_for_period(account, date_from, date_to)
        
        # For expense accounts, debits increase expenses
        expense_amount = balance_info['period_debits'] - balance_info['period_credits']
        
        if expense_amount > 0:
            expense_data.append({
                'account': account,
                'amount': expense_amount,
            })
            total_expenses += expense_amount
    
    net_income = total_income - total_expenses
    
    context = {
        'income_data': income_data,
        'expense_data': expense_data,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_income': net_income,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'reports/income_statement.html', context)

@login_required
def balance_sheet(request):
    """Generate balance sheet"""
    as_of_date = request.GET.get('as_of_date')
    
    if not as_of_date:
        as_of_date = timezone.now().date()
    else:
        as_of_date = datetime.strptime(as_of_date, '%Y-%m-%d').date()
    
    # Get accounts by type
    asset_accounts = Account.objects.filter(
        account_type='asset', is_active=True
    ).order_by('code')
    
    liability_accounts = Account.objects.filter(
        account_type='liability', is_active=True
    ).order_by('code')
    
    equity_accounts = Account.objects.filter(
        account_type='equity', is_active=True
    ).order_by('code')
    
    assets_data = []
    liabilities_data = []
    equity_data = []
    total_assets = Decimal('0')
    total_liabilities = Decimal('0')
    total_equity = Decimal('0')
    
    # Calculate assets using the helper function
    for account in asset_accounts:
        balance_info = calculate_account_balance_for_period(account, None, as_of_date)
        balance = balance_info['final_balance']
        
        if balance != 0:
            assets_data.append({
                'account': account,
                'amount': balance,
            })
            total_assets += balance
    
    # Calculate liabilities using the helper function
    for account in liability_accounts:
        balance_info = calculate_account_balance_for_period(account, None, as_of_date)
        balance = balance_info['final_balance']
        
        if balance != 0:
            liabilities_data.append({
                'account': account,
                'amount': balance,
            })
            total_liabilities += balance
    
    # Calculate equity using the helper function
    for account in equity_accounts:
        balance_info = calculate_account_balance_for_period(account, None, as_of_date)
        balance = balance_info['final_balance']
        
        if balance != 0:
            equity_data.append({
                'account': account,
                'amount': balance,
            })
            total_equity += balance
    
    # Add retained earnings (net income from all income and expense accounts up to date)
    income_accounts = Account.objects.filter(account_type='income', is_active=True)
    expense_accounts = Account.objects.filter(account_type='expense', is_active=True)
    
    total_income_all_time = Decimal('0')
    for account in income_accounts:
        balance_info = calculate_account_balance_for_period(account, None, as_of_date)
        # For income accounts, positive balance means more credits than debits
        balance = balance_info['final_balance']
        if balance > 0:  # Income accounts normally have credit balances
            total_income_all_time += balance
        else:  # Negative means debits exceeded credits
            total_income_all_time -= abs(balance)
    
    total_expenses_all_time = Decimal('0')
    for account in expense_accounts:
        balance_info = calculate_account_balance_for_period(account, None, as_of_date)
        # For expense accounts, positive balance means more debits than credits
        balance = balance_info['final_balance']
        if balance > 0:  # Expense accounts normally have debit balances
            total_expenses_all_time += balance
        else:  # Negative means credits exceeded debits
            total_expenses_all_time -= abs(balance)
    
    retained_earnings = total_income_all_time - total_expenses_all_time
    total_equity += retained_earnings
    total_liabilities_and_equity = total_liabilities + total_equity
    balance_difference = total_assets - total_liabilities_and_equity
    
    context = {
        'assets_data': assets_data,
        'liabilities_data': liabilities_data,
        'equity_data': equity_data,
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'total_equity': total_equity,
        'retained_earnings': retained_earnings,
        'total_liabilities_and_equity': total_liabilities_and_equity,
        'balance_difference': balance_difference,
        'as_of_date': as_of_date,
        'is_balanced': total_assets == total_liabilities_and_equity,
    }
    
    return render(request, 'reports/balance_sheet.html', context)

# Invoice Reports
@login_required
def invoice_summary(request):
    """Invoice summary report"""
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    status = request.GET.get('status', '')
    customer_id = request.GET.get('customer')
    
    # Default to current month if no dates provided
    if not date_from or not date_to:
        today = timezone.now().date()
        date_from = today.replace(day=1)
        date_to = today
    else:
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
    
    # Build base filter conditions
    base_filters = {'issue_date__range': [date_from, date_to]}
    if status:
        base_filters['status'] = status
    if customer_id:
        base_filters['customer_id'] = customer_id
    
    # Get invoices for display (separate queryset)
    invoices = Invoice.objects.filter(**base_filters)
    
    # Calculate summary statistics with completely fresh queryset
    summary_queryset = Invoice.objects.filter(**base_filters)
    summary_stats = {
        'total_count': summary_queryset.count(),
        'total_amount': summary_queryset.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0'),
        'avg_amount': summary_queryset.aggregate(Avg('total_amount'))['total_amount__avg'] or Decimal('0'),
    }
    
    # Status breakdown (use base date filter only)
    status_breakdown = {}
    base_date_filter = {'issue_date__range': [date_from, date_to]}
    if customer_id:
        base_date_filter['customer_id'] = customer_id
        
    for status_code, status_label in Invoice.STATUS_CHOICES:
        status_filter = base_date_filter.copy()
        status_filter['status'] = status_code
        
        count = Invoice.objects.filter(**status_filter).count()
        amount = Invoice.objects.filter(**status_filter).aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0')
        
        status_breakdown[status_code] = {
            'label': status_label,
            'count': count,
            'amount': amount,
        }
    
    # Customer breakdown (completely separate queryset)
    customer_filters = {'issue_date__range': [date_from, date_to]}
    if status:
        customer_filters['status'] = status
    if customer_id:
        customer_filters['customer_id'] = customer_id
        
    customer_breakdown = Invoice.objects.filter(**customer_filters).values(
        'customer__name'
    ).annotate(
        count=Count('id'),
        customer_total=Sum('total_amount')  # Different field name to avoid conflicts
    ).order_by('-customer_total')[:10]
    
    context = {
        'invoices': invoices.order_by('-issue_date'),
        'summary_stats': summary_stats,
        'status_breakdown': status_breakdown,
        'customer_breakdown': customer_breakdown,
        'date_from': date_from,
        'date_to': date_to,
        'selected_status': status,
        'selected_customer': customer_id,
        'customers': Customer.objects.filter(is_active=True).order_by('name'),
        'status_choices': Invoice.STATUS_CHOICES,
    }
    
    return render(request, 'reports/invoice_summary.html', context)

@login_required
def aged_receivables(request):
    """Aged receivables report"""
    as_of_date = request.GET.get('as_of_date')
    
    if not as_of_date:
        as_of_date = timezone.now().date()
    else:
        as_of_date = datetime.strptime(as_of_date, '%Y-%m-%d').date()
    
    # Get unpaid invoices
    unpaid_invoices = Invoice.objects.filter(
        status__in=['sent', 'overdue'],
        issue_date__lte=as_of_date
    ).select_related('customer')
    
    aged_data = []
    totals = {
        'current': Decimal('0'),
        '1_30': Decimal('0'),
        '31_60': Decimal('0'),
        '61_90': Decimal('0'),
        'over_90': Decimal('0'),
    }
    
    for invoice in unpaid_invoices:
        days_outstanding = (as_of_date - invoice.issue_date).days
        
        # Categorize by age
        if days_outstanding <= 30:
            category = 'current'
        elif days_outstanding <= 60:
            category = '1_30'
        elif days_outstanding <= 90:
            category = '31_60'
        elif days_outstanding <= 120:
            category = '61_90'
        else:
            category = 'over_90'
        
        aged_data.append({
            'invoice': invoice,
            'days_outstanding': days_outstanding,
            'category': category,
        })
        
        totals[category] += invoice.total_amount
    
    total_outstanding = sum(totals.values())
    
    context = {
        'aged_data': aged_data,
        'totals': totals,
        'total_outstanding': total_outstanding,
        'as_of_date': as_of_date,
    }
    
    return render(request, 'reports/aged_receivables.html', context)

# Customer Reports
@login_required
def customer_statement(request, customer_id):
    """Customer statement report"""
    customer = get_object_or_404(Customer, id=customer_id)
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Default to last 3 months if no dates provided
    if not date_from or not date_to:
        today = timezone.now().date()
        date_from = today - timedelta(days=90)
        date_to = today
    else:
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
    
    # Get customer's invoices and payments in the date range
    invoices = customer.invoices.filter(
        issue_date__range=[date_from, date_to]
    ).order_by('issue_date')
    
    payments = Payment.objects.filter(
        invoice__customer=customer,
        payment_date__range=[date_from, date_to]
    ).order_by('payment_date')
    
    # Calculate summary
    total_invoiced = invoices.aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0')
    
    total_paid = payments.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    outstanding_balance = customer.invoices.filter(
        status__in=['sent', 'overdue']
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    context = {
        'customer': customer,
        'invoices': invoices,
        'payments': payments,
        'total_invoiced': total_invoiced,
        'total_paid': total_paid,
        'outstanding_balance': outstanding_balance,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'reports/customer_statement.html', context)

# Analytics and Charts Data
@login_required
def revenue_analytics(request):
    """Revenue analytics with charts"""
    # Get monthly revenue for the last 12 months
    today = timezone.now().date()
    twelve_months_ago = today - timedelta(days=365)
    
    monthly_revenue = []
    current_month = twelve_months_ago.replace(day=1)
    
    while current_month <= today:
        next_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)
        
        revenue = Invoice.objects.filter(
            status='paid',
            paid_date__gte=current_month,
            paid_date__lt=next_month
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        monthly_revenue.append({
            'month': current_month.strftime('%Y-%m'),
            'month_name': current_month.strftime('%B %Y'),
            'revenue': float(revenue),
        })
        
        current_month = next_month
    
    # Get top customers by revenue
    top_customers = Customer.objects.annotate(
        total_revenue=Sum('invoices__total_amount', filter=Q(invoices__status='paid')),
        paid_invoice_count=Count('invoices', filter=Q(invoices__status='paid'))
    ).filter(total_revenue__isnull=False).order_by('-total_revenue')[:10]
    
    # Calculate average invoice amount for each customer
    for customer in top_customers:
        if customer.paid_invoice_count > 0:
            customer.avg_invoice = customer.total_revenue / customer.paid_invoice_count
        else:
            customer.avg_invoice = Decimal('0')
    
    context = {
        'monthly_revenue': monthly_revenue,
        'top_customers': top_customers,
    }
    
    return render(request, 'reports/revenue_analytics.html', context)

# Report Templates (Class-based views)
class ReportTemplateListView(LoginRequiredMixin, ListView):
    model = ReportTemplate
    template_name = 'reports/template_list.html'
    context_object_name = 'templates'
    paginate_by = 20
    
    def get_queryset(self):
        return ReportTemplate.objects.filter(
            Q(created_by=self.request.user) | Q(is_public=True)
        ).order_by('name')

class ReportTemplateCreateView(LoginRequiredMixin, CreateView):
    model = ReportTemplate
    form_class = ReportTemplateForm
    template_name = 'reports/template_form.html'
    success_url = reverse_lazy('reports:template_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class ReportTemplateUpdateView(LoginRequiredMixin, UpdateView):
    model = ReportTemplate
    form_class = ReportTemplateForm
    template_name = 'reports/template_form.html'
    success_url = reverse_lazy('reports:template_list')
    
    def get_queryset(self):
        return ReportTemplate.objects.filter(created_by=self.request.user)

class ReportTemplateDeleteView(LoginRequiredMixin, DeleteView):
    model = ReportTemplate
    template_name = 'reports/template_confirm_delete.html'
    success_url = reverse_lazy('reports:template_list')
    
    def get_queryset(self):
        return ReportTemplate.objects.filter(created_by=self.request.user)

