from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseForbidden
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.db.models import Q
from .models import CustomUser
from .forms import UserCurrencyPreferenceForm
from django.contrib.auth.forms import UserCreationForm
from django import forms

# Custom Forms
class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form with additional fields"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    role = forms.ChoiceField(
        choices=CustomUser._meta.get_field('role').choices,
        required=True
    )

    class Meta: # Tells Django which model to save the form data into and which fields to show on the form
        model = CustomUser
        fields = ("username", "first_name", "last_name", "email", "role", "password1", "password2")

    # Takes the form data and create a new custom user, make 
    # sure that all the extra fields are stored correctly, and saved it if commit is true.
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].lower().strip()
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()
        return user

class CustomUserUpdateForm(forms.ModelForm):
    """Form for updating user information"""
    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email", "role", "is_active")
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class LimitedUserUpdateForm(forms.ModelForm):
    """Limited form for regular users to update their own information"""
    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email")
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

# Helper Functions
def is_admin(user):
    """Check if user has admin role"""
    return user.is_authenticated and (user.is_superuser or user.role == 'admin')

def is_admin_or_accountant(user):
    """Check if user has admin or accountant role"""
    return user.is_authenticated and (user.is_superuser or user.role in ['admin', 'accountant'])

# Authentication Views
class CustomLoginView(LoginView):
    """Custom login view"""
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('users:dashboard')
    
    def form_valid(self, form):
        messages.success(self.request, f'Welcome back, {form.get_user().get_full_name() or form.get_user().username}!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Please check your username and password and try again.')
        return super().form_invalid(form)

class CustomLogoutView(LogoutView):
    """Custom logout view"""
    http_method_names = ['get', 'post']  # Allow both GET and POST requests
    
    def get(self, request, *args, **kwargs):
        """Handle GET request for logout"""
        if request.user.is_authenticated:
            messages.success(request, 'You have been successfully logged out.')
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """Handle POST request for logout"""
        if request.user.is_authenticated:
            messages.success(request, 'You have been successfully logged out.')
        return super().post(request, *args, **kwargs)
    
    def get_next_page(self):
        """Override to ensure redirect to login page"""
        return reverse_lazy('users:login')

# User Management Views
@method_decorator(never_cache, name='dispatch')
class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """View for admins to create new users"""
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:user_list')
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, f'User "{form.instance.username}" created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New User'
        context['submit_text'] = 'Create User'
        return context

@method_decorator(never_cache, name='dispatch')
class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View to list all users"""
    model = CustomUser
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def test_func(self):
        return is_admin_or_accountant(self.request.user)
    
    def get_queryset(self):
        queryset = CustomUser.objects.only(
            'id', 'username', 'first_name', 'last_name', 
            'email', 'role', 'is_active', 'date_joined'
        ).order_by('username')
        search = self.request.GET.get('search')
        role_filter = self.request.GET.get('role')
        status_filter = self.request.GET.get('status')
        
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        
        if role_filter and role_filter != 'all':
            queryset = queryset.filter(role=role_filter)
            
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['role_filter'] = self.request.GET.get('role', 'all')
        context['status_filter'] = self.request.GET.get('status', 'all')
        context['role_choices'] = CustomUser._meta.get_field('role').choices
        return context

@method_decorator(never_cache, name='dispatch')
class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View to display user details"""
    model = CustomUser
    template_name = 'users/user_detail.html'
    context_object_name = 'user_obj'
    
    def test_func(self):
        user = self.get_object()
        # Users can view their own profile, admins and accountants can view all
        return (self.request.user == user or 
                is_admin_or_accountant(self.request.user))

@method_decorator(never_cache, name='dispatch')
class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View to update user information"""
    model = CustomUser
    form_class = CustomUserUpdateForm
    template_name = 'users/user_form.html'
    
    def test_func(self):
        user = self.get_object()
        # Users can edit their own profile (limited), admins can edit all
        return (self.request.user == user or is_admin(self.request.user))
    
    def get_form_class(self):
        if is_admin(self.request.user):
            return CustomUserUpdateForm
        else:
            # Use the module-level form for regular users
            return LimitedUserUpdateForm
    
    def form_valid(self, form):
        messages.success(self.request, 'User information updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('users:user_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit {self.object.get_full_name() or self.object.username}'
        context['submit_text'] = 'Update User'
        return context

@method_decorator(never_cache, name='dispatch')
class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """View to delete users (admin only)"""
    model = CustomUser
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('users:user_list')
    context_object_name = 'user_obj'
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        if user == request.user:
            messages.error(request, "You cannot delete your own account.")
            return redirect('users:user_list')
        
        # Prevent deletion of the only superuser
        if user.is_superuser and CustomUser.objects.filter(is_superuser=True).count() == 1:
            messages.error(request, "You cannot delete the only superuser.")
            return redirect('users:user_list')
        
        username = user.username
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'User "{username}" deleted successfully!')
        return response

# Dashboard and Profile Views
@never_cache
@login_required
def dashboard(request):
    """Main dashboard view"""
    # Redirect HR users directly to payroll dashboard
    if hasattr(request.user, 'role') and request.user.role == 'hr':
        return redirect('payroll:dashboard')
        
    if is_admin(request.user):
        # Admin dashboard with statistics
        total_users = CustomUser.objects.count()
        active_users = CustomUser.objects.filter(is_active=True).count()
        admin_users = CustomUser.objects.filter(role='admin').count()
        accountant_users = CustomUser.objects.filter(role='accountant').count()
        viewer_users = CustomUser.objects.filter(role='viewer').count()
        recent_users = CustomUser.objects.order_by('-date_joined')[:5]
        
        context = {
            'total_users': total_users,
            'active_users': active_users,
            'admin_users': admin_users,
            'accountant_users': accountant_users,
            'viewer_users': viewer_users,
            'recent_users': recent_users,
        }
        return render(request, 'users/admin_dashboard.html', context)
    else:
        # Regular user dashboard
        return render(request, 'users/user_dashboard.html')

@never_cache
@login_required
def profile(request):
    """User profile view"""
    return render(request, 'users/profile.html', {'user_obj': request.user})

@never_cache
@login_required
@user_passes_test(is_admin)
def toggle_user_status(request, pk):
    """Toggle user active status (admin only)"""
    user = get_object_or_404(CustomUser, pk=pk)
    
    if user == request.user:
        messages.error(request, "You cannot deactivate your own account.")
    else:
        user.is_active = not user.is_active
        user.save()
        status = "activated" if user.is_active else "deactivated"
        messages.success(request, f'User "{user.username}" has been {status}.')
    
    return redirect('users:user_list')

@method_decorator(never_cache, name='dispatch')
class CurrencyPreferenceView(LoginRequiredMixin, UpdateView):
    """View for users to change their currency preference"""
    model = CustomUser
    form_class = UserCurrencyPreferenceForm
    template_name = 'users/currency_preference.html'
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        old_currency = self.request.user.preferred_currency
        new_currency = form.cleaned_data['preferred_currency']
        
        # Save the form and refresh the user from the database
        response = super().form_valid(form)
        
        # Clear any potential session currency data
        if hasattr(self.request, 'session'):
            # Remove any cached currency data from session
            for key in list(self.request.session.keys()):
                if 'currency' in key.lower():
                    del self.request.session[key]
        
        messages.success(
            self.request, 
            f'Currency preference updated from {old_currency} to {new_currency}! '
            f'All currency displays will now use {new_currency} formatting.'
        )
        return response
    
    def get_success_url(self):
        return reverse('users:currency_preference')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Currency Preference'
        return context
