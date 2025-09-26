from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Sum, Count
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from decimal import Decimal
from .models import Invoice, Customer, InvoiceItem, Payment
from .forms import InvoiceForm, CustomerForm, InvoiceItemForm, PaymentForm

def can_access_invoices(user):
    """Check if user can access invoice features (everyone except HR)"""
    return user.is_authenticated and (user.role != 'hr' or user.is_superuser)

# Dashboard View
@login_required
@user_passes_test(can_access_invoices)
def invoices_dashboard(request):
    """Invoice dashboard with key metrics and recent invoices"""
    # Key metrics
    total_invoices = Invoice.objects.filter(created_by=request.user).count()
    total_revenue = Invoice.objects.filter(
        created_by=request.user, 
        status='paid'
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    
    pending_invoices = Invoice.objects.filter(
        created_by=request.user, 
        status__in=['sent', 'draft']
    ).count()
    
    overdue_invoices = Invoice.objects.filter(
        created_by=request.user,
        status='sent',
        due_date__lt=timezone.now().date()
    ).count()

    # Recent invoices
    recent_invoices = Invoice.objects.filter(
        created_by=request.user
    ).order_by('-created_at')[:5]

    # Monthly revenue data for chart
    from django.db.models.functions import TruncMonth
    monthly_revenue = Invoice.objects.filter(
        created_by=request.user,
        status='paid'
    ).annotate(
        month=TruncMonth('paid_date')
    ).values('month').annotate(
        revenue=Sum('total_amount')
    ).order_by('-month')[:6]

    context = {
        'total_invoices': total_invoices,
        'total_revenue': total_revenue,
        'pending_invoices': pending_invoices,
        'overdue_invoices': overdue_invoices,
        'recent_invoices': recent_invoices,
        'monthly_revenue': monthly_revenue,
    }
    return render(request, 'invoices/dashboard.html', context)

# Invoice Views
class InvoiceListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Invoice
    template_name = 'invoices/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20

    def test_func(self):
        return can_access_invoices(self.request.user)

    def get_queryset(self):
        queryset = Invoice.objects.filter(created_by=self.request.user)
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(invoice_number__icontains=search) |
                Q(customer__name__icontains=search) |
                Q(customer__email__icontains=search)
            )
        
        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from accounts.utils import get_currency_symbol
        context['status_choices'] = Invoice.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        context['currency_symbol'] = get_currency_symbol(user=self.request.user)
        return context

class InvoiceDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Invoice
    template_name = 'invoices/invoice_detail.html'
    context_object_name = 'invoice'

    def test_func(self):
        return can_access_invoices(self.request.user)

    def get_queryset(self):
        return Invoice.objects.filter(created_by=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from accounts.utils import get_currency_symbol
        context['payments'] = self.object.payments.all()
        context['payment_form'] = PaymentForm()
        context['currency_symbol'] = get_currency_symbol(user=self.request.user)
        return context

class InvoiceCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoices/invoice_form.html'

    def test_func(self):
        return can_access_invoices(self.request.user)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from accounts.utils import get_currency_symbol
        context['title'] = 'Create Invoice'
        context['currency_symbol'] = get_currency_symbol(user=self.request.user)
        return context

class InvoiceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoices/invoice_form.html'

    def test_func(self):
        return can_access_invoices(self.request.user)

    def get_queryset(self):
        return Invoice.objects.filter(created_by=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from accounts.utils import get_currency_symbol
        context['title'] = 'Edit Invoice'
        context['currency_symbol'] = get_currency_symbol(user=self.request.user)
        return context

class InvoiceDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Invoice
    template_name = 'invoices/invoice_delete.html'
    success_url = reverse_lazy('invoices:invoice_list')

    def test_func(self):
        return can_access_invoices(self.request.user)

    def get_queryset(self):
        return Invoice.objects.filter(created_by=self.request.user)

# Customer Views
class CustomerListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Customer
    template_name = 'invoices/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 20

    def test_func(self):
        return can_access_invoices(self.request.user)

    def get_queryset(self):
        queryset = Customer.objects.filter(created_by=self.request.user, is_active=True)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )
        
        return queryset.order_by('name')

class CustomerDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Customer
    template_name = 'invoices/customer_detail.html'
    context_object_name = 'customer'

    def test_func(self):
        return can_access_invoices(self.request.user)

    def get_queryset(self):
        return Customer.objects.filter(created_by=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invoices'] = self.object.invoices.all().order_by('-created_at')
        return context

class CustomerCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'invoices/customer_form.html'

    def test_func(self):
        return can_access_invoices(self.request.user)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class CustomerUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'invoices/customer_form.html'

    def test_func(self):
        return can_access_invoices(self.request.user)

    def get_queryset(self):
        return Customer.objects.filter(created_by=self.request.user)

class CustomerDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Customer
    template_name = 'invoices/customer_delete.html'
    success_url = reverse_lazy('invoices:customer_list')

    def test_func(self):
        return can_access_invoices(self.request.user)

    def get_queryset(self):
        return Customer.objects.filter(created_by=self.request.user)

# AJAX Views for Invoice Items
@login_required
@user_passes_test(can_access_invoices)
def add_invoice_item(request, invoice_id):
    """Add item to invoice via AJAX"""
    invoice = get_object_or_404(Invoice, id=invoice_id, created_by=request.user)
    
    if request.method == 'POST':
        form = InvoiceItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.invoice = invoice
            item.save()
            return JsonResponse({
                'success': True,
                'item_id': item.id,
                'description': item.description,
                'quantity': str(item.quantity),
                'unit_price': str(item.unit_price),
                'total': str(item.total),
                'invoice_total': str(invoice.total_amount)
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({'success': False})

@login_required
@user_passes_test(can_access_invoices)
def delete_invoice_item(request, item_id):
    """Delete invoice item via AJAX"""
    item = get_object_or_404(InvoiceItem, id=item_id, invoice__created_by=request.user)
    invoice = item.invoice
    item.delete()
    invoice.calculate_totals()
    invoice.save()
    
    return JsonResponse({
        'success': True,
        'invoice_total': str(invoice.total_amount)
    })

# Payment Views
@login_required
@user_passes_test(can_access_invoices)
def add_payment(request, invoice_id):
    """Add payment to invoice"""
    invoice = get_object_or_404(Invoice, id=invoice_id, created_by=request.user)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.created_by = request.user
            payment.save()
            
            # Update invoice status if fully paid
            total_payments = invoice.payments.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            if total_payments >= invoice.total_amount:
                invoice.status = 'paid'
                invoice.paid_date = payment.payment_date
                invoice.save()
            
            messages.success(request, 'Payment added successfully!')
            return redirect('invoices:invoice_detail', pk=invoice.id)
    
    return redirect('invoices:invoice_detail', pk=invoice.id)

# Report Views
@login_required
@user_passes_test(can_access_invoices)
def invoice_reports(request):
    """Invoice reports and analytics"""
    # Summary stats
    invoices = Invoice.objects.filter(created_by=request.user)
    
    stats = {
        'total_invoices': invoices.count(),
        'total_revenue': invoices.filter(status='paid').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
        'pending_amount': invoices.filter(status__in=['sent', 'draft']).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
        'overdue_amount': invoices.filter(status='sent', due_date__lt=timezone.now().date()).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
    }
    
    # Status breakdown
    status_breakdown = invoices.values('status').annotate(
        count=Count('id'),
        amount=Sum('total_amount')
    )
    
    context = {
        'stats': stats,
        'status_breakdown': status_breakdown,
    }
    return render(request, 'invoices/reports.html', context)
