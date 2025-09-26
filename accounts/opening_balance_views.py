from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import TemplateView
from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse, HttpResponse
from django.core.management import call_command
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from decimal import Decimal
from datetime import date
import csv
import io
import tempfile
import os

from .models import Account, JournalEntry, JournalEntryLine
from .opening_balance_forms import (
    OpeningBalanceForm, 
    BulkOpeningBalanceForm,
    CSVOpeningBalanceUploadForm,
    SingleAccountOpeningBalanceForm
)


def can_manage_opening_balances(user):
    """Check if user can manage opening balances"""
    return user.is_authenticated and user.is_staff


@method_decorator(never_cache, name='dispatch')
class OpeningBalanceManagementView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Main view for opening balance management"""
    template_name = 'accounts/opening_balance_management.html'
    
    def test_func(self):
        return can_manage_opening_balances(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all accounts with their current opening balances
        accounts = Account.objects.filter(is_active=True).order_by('code')
        
        # Calculate statistics
        accounts_with_balances = accounts.exclude(opening_balance=0)
        accounts_without_balances = accounts.filter(opening_balance=0)
        total_opening_balance = sum(acc.opening_balance for acc in accounts)
        
        context.update({
            'accounts': accounts,
            'accounts_with_balances': accounts_with_balances,
            'accounts_without_balances': accounts_without_balances,
            'total_accounts': accounts.count(),
            'accounts_with_balances_count': accounts_with_balances.count(),
            'accounts_without_balances_count': accounts_without_balances.count(),
            'total_opening_balance': total_opening_balance,
            'form': OpeningBalanceForm(),
        })
        
        return context


@login_required
@user_passes_test(can_manage_opening_balances)
@never_cache
def process_opening_balances(request):
    """Process opening balance form submission"""
    if request.method != 'POST':
        return redirect('accounts:opening_balance_management')
    
    form = OpeningBalanceForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, 'Please correct the errors in the form.')
        return redirect('accounts:opening_balance_management')
    
    method = form.cleaned_data['method']
    opening_date = form.cleaned_data['opening_date']
    
    try:
        if method == 'calculate':
            return process_calculate_method(request, form)
        elif method == 'import':
            return process_import_method(request, form)
        elif method == 'zero':
            return process_zero_method(request, form)
        elif method == 'manual':
            return redirect('accounts:bulk_opening_balance_edit')
    except Exception as e:
        messages.error(request, f'Error processing opening balances: {str(e)}')
        return redirect('accounts:opening_balance_management')


def process_calculate_method(request, form):
    """Process calculate method using management command"""
    cutoff_date = form.cleaned_data['cutoff_date']
    opening_date = form.cleaned_data['opening_date']
    create_journal_entry = form.cleaned_data.get('create_journal_entry', False)
    
    # Use management command
    try:
        # Capture command output
        from io import StringIO
        import sys
        
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        
        call_command(
            'generate_opening_balances',
            method='calculate',
            cutoff_date=cutoff_date.strftime('%Y-%m-%d'),
            opening_date=opening_date.strftime('%Y-%m-%d'),
            create_journal_entry=create_journal_entry,
            verbosity=1
        )
        
        sys.stdout = old_stdout
        output = mystdout.getvalue()
        
        # Parse the output to show user
        if 'Updated' in output:
            messages.success(request, f'Opening balances calculated successfully. {output}')
        else:
            messages.info(request, 'No accounts needed updating.')
            
    except Exception as e:
        messages.error(request, f'Error calculating opening balances: {str(e)}')
    
    return redirect('accounts:opening_balance_management')


def process_import_method(request, form):
    """Process CSV import method"""
    csv_file = form.cleaned_data['csv_file']
    opening_date = form.cleaned_data['opening_date']
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(mode='w+b', suffix='.csv', delete=False) as temp_file:
        for chunk in csv_file.chunks():
            temp_file.write(chunk)
        temp_file_path = temp_file.name
    
    try:
        # Use management command
        from io import StringIO
        import sys
        
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        
        call_command(
            'generate_opening_balances',
            method='import',
            csv_file=temp_file_path,
            opening_date=opening_date.strftime('%Y-%m-%d'),
            verbosity=1
        )
        
        sys.stdout = old_stdout
        output = mystdout.getvalue()
        
        if 'Updated' in output:
            messages.success(request, f'Opening balances imported successfully. {output}')
        else:
            messages.info(request, 'No accounts were updated from the CSV file.')
            
    except Exception as e:
        messages.error(request, f'Error importing opening balances: {str(e)}')
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_file_path)
        except:
            pass
    
    return redirect('accounts:opening_balance_management')


def process_zero_method(request, form):
    """Process zero method"""
    opening_date = form.cleaned_data['opening_date']
    
    try:
        from io import StringIO
        import sys
        
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        
        call_command(
            'generate_opening_balances',
            method='zero',
            opening_date=opening_date.strftime('%Y-%m-%d'),
            verbosity=1
        )
        
        sys.stdout = old_stdout
        output = mystdout.getvalue()
        
        if 'Updated' in output:
            messages.success(request, f'Opening balances reset to zero. {output}')
        else:
            messages.info(request, 'All accounts already had zero opening balances.')
            
    except Exception as e:
        messages.error(request, f'Error resetting opening balances: {str(e)}')
    
    return redirect('accounts:opening_balance_management')


@method_decorator(never_cache, name='dispatch')
class BulkOpeningBalanceEditView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """View for bulk editing opening balances"""
    template_name = 'accounts/bulk_opening_balance_edit.html'
    
    def test_func(self):
        return can_manage_opening_balances(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        accounts = Account.objects.filter(is_active=True).order_by('code')
        form = BulkOpeningBalanceForm(accounts=accounts)
        
        context.update({
            'form': form,
            'accounts': accounts,
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        accounts = Account.objects.filter(is_active=True).order_by('code')
        form = BulkOpeningBalanceForm(request.POST, accounts=accounts)
        
        if form.is_valid():
            opening_date = form.cleaned_data['opening_date']
            updated_count = 0
            
            with transaction.atomic():
                for field_name, field in form.get_account_fields():
                    balance = form.cleaned_data.get(field_name, Decimal('0.00'))
                    account = field.account
                    
                    if account.opening_balance != balance or account.opening_balance_date != opening_date:
                        account.opening_balance = balance or Decimal('0.00')
                        account.opening_balance_date = opening_date
                        account.save()
                        updated_count += 1
            
            messages.success(request, f'Updated opening balances for {updated_count} accounts.')
            return redirect('accounts:opening_balance_management')
        else:
            messages.error(request, 'Please correct the errors in the form.')
            return self.render_to_response(self.get_context_data(form=form))


@login_required
@user_passes_test(can_manage_opening_balances)
def download_opening_balance_template(request):
    """Download CSV template for opening balance import"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="opening_balance_template.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['account_code', 'opening_balance'])
    
    # Add sample data
    accounts = Account.objects.filter(is_active=True).order_by('code')[:10]
    for account in accounts:
        writer.writerow([account.code, '0.00'])
    
    return response


@login_required
@user_passes_test(can_manage_opening_balances)
def export_current_opening_balances(request):
    """Export current opening balances to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="current_opening_balances.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['account_code', 'account_name', 'account_type', 'opening_balance', 'opening_balance_date'])
    
    accounts = Account.objects.filter(is_active=True).order_by('code')
    for account in accounts:
        writer.writerow([
            account.code,
            account.name,
            account.get_account_type_display(),
            str(account.opening_balance),
            account.opening_balance_date.strftime('%Y-%m-%d') if account.opening_balance_date else ''
        ])
    
    return response


@login_required
@user_passes_test(can_manage_opening_balances)
def single_account_opening_balance(request, account_id):
    """Edit opening balance for a single account"""
    account = get_object_or_404(Account, pk=account_id, is_active=True)
    
    if request.method == 'POST':
        form = SingleAccountOpeningBalanceForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            messages.success(
                request, 
                f'Opening balance updated for {account.code} - {account.name}'
            )
            return JsonResponse({'success': True})
        else:
            return JsonResponse({
                'success': False, 
                'errors': form.errors
            })
    
    form = SingleAccountOpeningBalanceForm(instance=account)
    return render(request, 'accounts/single_account_opening_balance.html', {
        'form': form,
        'account': account
    })


@login_required
@user_passes_test(can_manage_opening_balances)
def opening_balance_preview(request):
    """Preview opening balance calculations without saving"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'})
    
    method = request.POST.get('method')
    cutoff_date_str = request.POST.get('cutoff_date')
    
    if method != 'calculate' or not cutoff_date_str:
        return JsonResponse({'error': 'Invalid parameters'})
    
    try:
        from datetime import datetime
        cutoff_date = datetime.strptime(cutoff_date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'})
    
    # Calculate preview without saving
    accounts = Account.objects.filter(is_active=True).order_by('code')
    preview_data = []
    
    for account in accounts:
        # Calculate what the opening balance would be
        journal_lines = JournalEntryLine.objects.filter(
            account=account,
            journal_entry__date__lte=cutoff_date,
            journal_entry__is_posted=True
        )
        
        credits = journal_lines.filter(entry_type='credit').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        debits = journal_lines.filter(entry_type='debit').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        # Calculate balance based on account type
        if account.account_type in ['asset', 'expense']:
            calculated_balance = debits - credits
        else:
            calculated_balance = credits - debits
        
        if calculated_balance != account.opening_balance:
            preview_data.append({
                'code': account.code,
                'name': account.name,
                'current_balance': str(account.opening_balance),
                'calculated_balance': str(calculated_balance),
                'difference': str(calculated_balance - account.opening_balance)
            })
    
    return JsonResponse({
        'success': True,
        'preview_data': preview_data,
        'total_accounts': len(preview_data)
    })
