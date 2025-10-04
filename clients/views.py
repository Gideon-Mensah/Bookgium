from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Client, ClientNote
from .forms import ClientForm, ClientNoteForm, ClientSearchForm

# Helper Functions
def is_admin_or_accountant(user):
    """Check if user has admin or accountant role"""
    return user.is_authenticated and (user.is_superuser or user.role in ['admin', 'accountant'])

def can_manage_clients(user):
    """Check if user can manage clients"""
    return user.is_authenticated and (user.is_superuser or user.role in ['admin', 'accountant'])

# Dashboard View
@never_cache
@login_required
def dashboard(request):
    """Clients dashboard view"""
    if not can_manage_clients(request.user):
        messages.error(request, "You don't have permission to access client management.")
        return redirect('users:dashboard')
    
    # Get client statistics
    total_clients = Client.objects.count()
    active_clients = Client.objects.filter(status='active').count()
    prospective_clients = Client.objects.filter(status='prospective').count()
    
    # Recent clients
    recent_clients = Client.objects.select_related('created_by').order_by('-created_at')[:5]
    
    # Client status distribution
    status_stats = (
        Client.objects
        .values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )
    
    context = {
        'title': 'Clients Dashboard',
        'total_clients': total_clients,
        'active_clients': active_clients,
        'prospective_clients': prospective_clients,
        'recent_clients': recent_clients,
        'status_stats': status_stats,
    }
    
    return render(request, 'clients/dashboard.html', context)

# Client CRUD Views
@method_decorator(never_cache, name='dispatch')
class ClientCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """View for creating new clients"""
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    success_url = reverse_lazy('clients:list')
    
    def test_func(self):
        return can_manage_clients(self.request.user)
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Client "{form.instance.name}" created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Client'
        context['submit_text'] = 'Create Client'
        return context

@method_decorator(never_cache, name='dispatch')
class ClientListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View to list all clients"""
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    paginate_by = 20
    
    def test_func(self):
        return can_manage_clients(self.request.user)
    
    def get_queryset(self):
        queryset = Client.objects.select_related('created_by').order_by('name')
        
        # Apply search filters
        search = self.request.GET.get('search')
        status_filter = self.request.GET.get('status')
        company_type_filter = self.request.GET.get('company_type')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search) |
                Q(contact_person__icontains=search)
            )
        
        if status_filter and status_filter != 'all':
            queryset = queryset.filter(status=status_filter)
            
        if company_type_filter and company_type_filter != 'all':
            queryset = queryset.filter(company_type=company_type_filter)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ClientSearchForm(self.request.GET)
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', 'all')
        context['company_type_filter'] = self.request.GET.get('company_type', 'all')
        return context

@method_decorator(never_cache, name='dispatch')
class ClientDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View to display client details"""
    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'
    
    def test_func(self):
        return can_manage_clients(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get recent notes for this client
        context['recent_notes'] = (
            self.object.client_notes
            .select_related('created_by')
            .order_by('-created_at')[:10]
        )
        context['note_form'] = ClientNoteForm()
        return context

@method_decorator(never_cache, name='dispatch')
class ClientUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View to update client information"""
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    
    def test_func(self):
        return can_manage_clients(self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Client information updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('clients:detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit {self.object.name}'
        context['submit_text'] = 'Update Client'
        return context

@method_decorator(never_cache, name='dispatch')
class ClientDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """View to delete clients"""
    model = Client
    template_name = 'clients/client_confirm_delete.html'
    success_url = reverse_lazy('clients:list')
    context_object_name = 'client'
    
    def test_func(self):
        return can_manage_clients(self.request.user)
    
    def delete(self, request, *args, **kwargs):
        client = self.get_object()
        client_name = client.name
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Client "{client_name}" deleted successfully!')
        return response

# Client Notes Views
@never_cache
@login_required
@user_passes_test(can_manage_clients)
def add_client_note(request, pk):
    """Add a note to a client"""
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        form = ClientNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.client = client
            note.created_by = request.user
            note.save()
            messages.success(request, 'Note added successfully!')
            return redirect('clients:detail', pk=client.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    
    return redirect('clients:detail', pk=client.pk)

@never_cache
@login_required
@user_passes_test(can_manage_clients)
def delete_client_note(request, pk, note_pk):
    """Delete a client note"""
    client = get_object_or_404(Client, pk=pk)
    note = get_object_or_404(ClientNote, pk=note_pk, client=client)
    
    if request.method == 'POST':
        note.delete()
        messages.success(request, 'Note deleted successfully!')
    
    return redirect('clients:detail', pk=client.pk)

# Utility Views
@never_cache
@login_required
@user_passes_test(can_manage_clients)
def toggle_client_status(request, pk):
    """Toggle client status between active and inactive"""
    client = get_object_or_404(Client, pk=pk)
    
    if client.status == 'active':
        client.status = 'inactive'
        status_msg = "deactivated"
    else:
        client.status = 'active'
        status_msg = "activated"
    
    client.save()
    messages.success(request, f'Client "{client.name}" has been {status_msg}.')
    
    return redirect('clients:detail', pk=client.pk)

@never_cache
@login_required
@user_passes_test(can_manage_clients)
def client_search_ajax(request):
    """AJAX endpoint for client search"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'clients': []})
    
    clients = Client.objects.filter(
        Q(name__icontains=query) |
        Q(email__icontains=query)
    ).order_by('name')[:10]
    
    client_data = []
    for client in clients:
        client_data.append({
            'id': client.id,
            'name': client.name,
            'email': client.email,
            'status': client.get_status_display(),
            'url': reverse('clients:detail', kwargs={'pk': client.pk})
        })
    
    return JsonResponse({'clients': client_data})
