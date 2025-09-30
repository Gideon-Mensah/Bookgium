from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import Client, Domain, ClientContact, ClientUsageLog
from .forms import ClientForm, DomainForm, ClientContactForm, ClientSearchForm
from users.models import CustomUser

def is_admin_or_superuser(user):
    """Check if user is admin or superuser"""
    return user.is_superuser or (hasattr(user, 'role') and user.role == 'admin')

class ClientDashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Main dashboard for client management"""
    model = Client
    template_name = 'clients/dashboard.html'
    context_object_name = 'clients'
    
    def test_func(self):
        return is_admin_or_superuser(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get statistics
        total_clients = Client.objects.count()
        active_clients = Client.objects.filter(is_active=True).count()
        trial_clients = Client.objects.filter(on_trial=True, is_active=True).count()
        expired_clients = Client.objects.filter(subscription_status='expired').count()
        
        # Get clients expiring soon (within 7 days)
        soon_expiring = Client.objects.filter(
            paid_until__lte=timezone.now().date() + timedelta(days=7),
            paid_until__gte=timezone.now().date(),
            is_active=True
        ).order_by('paid_until')
        
        # Get recent clients
        recent_clients = Client.objects.filter(is_active=True).order_by('-created_on')[:5]
        
        # Monthly revenue calculation
        monthly_revenue = Client.objects.filter(
            is_active=True,
            subscription_status='active'
        ).aggregate(total=Sum('monthly_fee'))['total'] or 0
        
        # Calculate average revenue per client
        average_per_client = monthly_revenue / active_clients if active_clients > 0 else 0
        
        # Currency distribution
        currency_distribution = Client.objects.filter(is_active=True).values('currency').annotate(
            count=Count('currency'),
            revenue=Sum('monthly_fee')
        ).order_by('-count')
        
        # Client growth over last 6 months
        client_growth = []
        for i in range(6):
            date = timezone.now().date().replace(day=1) - timedelta(days=30*i)
            count = Client.objects.filter(created_on__month=date.month, created_on__year=date.year).count()
            client_growth.append({
                'month': date.strftime('%b %Y'),
                'count': count
            })
        client_growth.reverse()
        
        from accounts.utils import get_currency_symbol
        
        context.update({
            'total_clients': total_clients,
            'active_clients': active_clients,
            'trial_clients': trial_clients,
            'expired_clients': expired_clients,
            'soon_expiring': soon_expiring,
            'recent_clients': recent_clients,
            'monthly_revenue': monthly_revenue,
            'average_per_client': average_per_client,
            'client_growth': client_growth,
            'currency_distribution': currency_distribution,
            'currency_symbol': get_currency_symbol(user=self.request.user),
        })
        
        return context

class ClientListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all clients with search and filtering"""
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    paginate_by = 20
    
    def test_func(self):
        return is_admin_or_superuser(self.request.user)
    
    def get_queryset(self):
        queryset = Client.objects.select_related('account_manager').prefetch_related('domains', 'contacts')
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(slug__icontains=search_query)
            )
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(subscription_status=status)
        
        # Filter by plan
        plan = self.request.GET.get('plan')
        if plan:
            queryset = queryset.filter(plan_type=plan)
        
        # Filter by active status
        active = self.request.GET.get('active')
        if active == 'true':
            queryset = queryset.filter(is_active=True)
        elif active == 'false':
            queryset = queryset.filter(is_active=False)
        
        # Filter by currency
        currency = self.request.GET.get('currency')
        if currency:
            queryset = queryset.filter(currency=currency)
        
        return queryset.order_by('-created_on')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ClientSearchForm(self.request.GET)
        context['subscription_statuses'] = Client.SUBSCRIPTION_STATUS
        context['plan_types'] = Client.PLAN_TYPES
        return context

class ClientDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Detailed view of a single client"""
    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'
    
    def test_func(self):
        return is_admin_or_superuser(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.object
        
        # Get usage statistics for the last 30 days
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        usage_logs = ClientUsageLog.objects.filter(
            client=client,
            date_recorded__gte=thirty_days_ago
        ).order_by('-date_recorded')
        
        # Get billing history (placeholder - would integrate with actual billing system)
        billing_history = []
        
        # Get activity timeline
        activity_timeline = []
        
        context.update({
            'usage_logs': usage_logs,
            'billing_history': billing_history,
            'activity_timeline': activity_timeline,
            'days_until_expiry': client.days_until_expiry,
        })
        
        return context

class ClientCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new client"""
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    success_url = reverse_lazy('clients:list')
    
    def test_func(self):
        return is_admin_or_superuser(self.request.user)
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Client "{form.instance.name}" has been created successfully.')
        return super().form_valid(form)

class ClientUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update an existing client"""
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    
    def test_func(self):
        return is_admin_or_superuser(self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, f'Client "{form.instance.name}" has been updated successfully.')
        return super().form_valid(form)

class ClientDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a client (soft delete - set inactive)"""
    model = Client
    template_name = 'clients/client_confirm_delete.html'
    success_url = reverse_lazy('clients:list')
    
    def test_func(self):
        return is_admin_or_superuser(self.request.user)
    
    def delete(self, request, *args, **kwargs):
        # Soft delete - just set inactive
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save()
        messages.success(request, f'Client "{self.object.name}" has been deactivated.')
        return redirect(self.success_url)

# Domain Management Views
class DomainListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List domains for a specific client"""
    model = Domain
    template_name = 'clients/domain_list.html'
    context_object_name = 'domains'
    
    def test_func(self):
        return is_admin_or_superuser(self.request.user)
    
    def get_queryset(self):
        client_pk = self.kwargs.get('client_pk')
        return Domain.objects.filter(tenant_id=client_pk).order_by('-is_primary', 'domain')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = get_object_or_404(Client, pk=self.kwargs.get('client_pk'))
        return context

class DomainCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Add a new domain to a client"""
    model = Domain
    form_class = DomainForm
    template_name = 'clients/domain_form.html'
    
    def test_func(self):
        return is_admin_or_superuser(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = get_object_or_404(Client, pk=self.kwargs.get('client_pk'))
        return context
    
    def form_valid(self, form):
        form.instance.tenant_id = self.kwargs.get('client_pk')
        messages.success(self.request, f'Domain "{form.instance.domain}" has been added.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('clients:domains', kwargs={'client_pk': self.kwargs.get('client_pk')})

# Contact Management Views
class ContactListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List contacts for a specific client"""
    model = ClientContact
    template_name = 'clients/contact_list.html'
    context_object_name = 'contacts'
    
    def test_func(self):
        return is_admin_or_superuser(self.request.user)
    
    def get_queryset(self):
        client_pk = self.kwargs.get('client_pk')
        return ClientContact.objects.filter(client_id=client_pk).order_by('-is_primary', 'last_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = get_object_or_404(Client, pk=self.kwargs.get('client_pk'))
        return context

class ContactCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Add a new contact to a client"""
    model = ClientContact
    form_class = ClientContactForm
    template_name = 'clients/contact_form.html'
    
    def test_func(self):
        return is_admin_or_superuser(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = get_object_or_404(Client, pk=self.kwargs.get('client_pk'))
        return context
    
    def form_valid(self, form):
        form.instance.client_id = self.kwargs.get('client_pk')
        messages.success(self.request, f'Contact "{form.instance.full_name}" has been added.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('clients:contacts', kwargs={'client_pk': self.kwargs.get('client_pk')})

# Additional views for the URL patterns
class ExtendTrialView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View to extend client trial period"""
    model = Client
    fields = []
    template_name = 'clients/extend_trial.html'
    
    def test_func(self):
        return is_admin_or_superuser(self.request.user)
    
    def post(self, request, *args, **kwargs):
        client = self.get_object()
        days = int(request.POST.get('days', 30))
        
        if client.trial_ends:
            client.trial_ends += timedelta(days=days)
        else:
            client.trial_ends = timezone.now().date() + timedelta(days=days)
        
        client.on_trial = True
        client.save()
        
        messages.success(request, f'Trial extended by {days} days for {client.name}')
        return redirect('clients:detail', pk=client.pk)

class SuspendClientView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Suspend a client account"""
    model = Client
    fields = []
    
    def test_func(self):
        return is_admin_or_superuser(self.request.user)
    
    def post(self, request, *args, **kwargs):
        client = self.get_object()
        client.is_active = False
        client.subscription_status = 'suspended'
        client.save()
        
        messages.success(request, f'Client {client.name} has been suspended.')
        return redirect('clients:detail', pk=client.pk)

class ActivateClientView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Activate a client account"""
    model = Client
    fields = []
    
    def test_func(self):
        return is_admin_or_superuser(self.request.user)
    
    def post(self, request, *args, **kwargs):
        client = self.get_object()
        client.is_active = True
        client.subscription_status = 'active'
        client.save()
        
        messages.success(request, f'Client {client.name} has been activated.')
        return redirect('clients:detail', pk=client.pk)

class DomainUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update a domain"""
    model = Domain
    form_class = DomainForm
    template_name = 'clients/domain_form.html'
    
    def test_func(self):
        return is_admin_or_superuser(self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('clients:domains', kwargs={'client_pk': self.object.tenant_id})

class DomainDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a domain"""
    model = Domain
    template_name = 'clients/domain_confirm_delete.html'
    
    def test_func(self):
        return is_admin_or_superuser(self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('clients:domains', kwargs={'client_pk': self.object.tenant_id})

class ContactUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update a contact"""
    model = ClientContact
    form_class = ClientContactForm
    template_name = 'clients/contact_form.html'
    
    def test_func(self):
        return is_admin_or_superuser(self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('clients:contacts', kwargs={'client_pk': self.object.client_id})

class ContactDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a contact"""
    model = ClientContact
    template_name = 'clients/contact_confirm_delete.html'
    
    def test_func(self):
        return is_admin_or_superuser(self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('clients:contacts', kwargs={'client_pk': self.object.client_id})

# AJAX Views
from django.views import View

class ClientSearchAjaxView(LoginRequiredMixin, UserPassesTestMixin, View):
    """AJAX endpoint for client search"""
    
    def test_func(self):
        return is_admin_or_superuser(self.request.user)
    
    def get(self, request):
        query = request.GET.get('q', '')
        clients = Client.objects.filter(
            Q(name__icontains=query) | Q(email__icontains=query)
        )[:10]
        
        data = [{
            'id': client.id,
            'name': client.name,
            'email': client.email,
            'status': client.subscription_status
        } for client in clients]
        
        return JsonResponse({'clients': data})

class ClientStatsAjaxView(LoginRequiredMixin, UserPassesTestMixin, View):
    """AJAX endpoint for client statistics"""
    
    def test_func(self):
        return is_admin_or_superuser(self.request.user)
    
    def get(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        
        # Get usage data for the last 30 days
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        usage_logs = ClientUsageLog.objects.filter(
            client=client,
            date_recorded__gte=thirty_days_ago
        ).order_by('date_recorded')
        
        usage_data = []
        for log in usage_logs:
            usage_data.append({
                'date': log.date_recorded.isoformat(),
                'users': log.active_users,
                'invoices': log.invoices_created,
                'storage': log.storage_used_gb
            })
        
        return JsonResponse({
            'usage_data': usage_data,
            'client_name': client.name,
            'subscription_status': client.subscription_status
        })
