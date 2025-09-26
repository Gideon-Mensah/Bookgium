from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django_tenants.models import TenantMixin, DomainMixin

class Client(TenantMixin):
    """Client organizations that use the multi-tenant system"""
    
    SUBSCRIPTION_STATUS = [
        ('trial', 'Free Trial'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
    ]
    
    PLAN_TYPES = [
        ('starter', 'Starter Plan'),
        ('professional', 'Professional Plan'),
        ('enterprise', 'Enterprise Plan'),
        ('custom', 'Custom Plan'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=200, help_text="The name of the client organization")
    slug = models.SlugField(max_length=200, unique=True, help_text="URL-friendly identifier")
    description = models.TextField(blank=True, null=True, help_text="Brief description of the organization")
    
    # Contact Information
    email = models.EmailField(help_text="Primary contact email")
    phone = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    
    # Address Information
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default='United States')
    
    # Currency Choices
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar ($)'),
        ('EUR', 'Euro (€)'),
        ('GBP', 'British Pound (£)'),
        ('CAD', 'Canadian Dollar (C$)'),
        ('AUD', 'Australian Dollar (A$)'),
        ('JPY', 'Japanese Yen (¥)'),
        ('CHF', 'Swiss Franc (CHF)'),
        ('CNY', 'Chinese Yuan (¥)'),
        ('INR', 'Indian Rupee (₹)'),
        ('BRL', 'Brazilian Real (R$)'),
        ('ZAR', 'South African Rand (R)'),
        ('MXN', 'Mexican Peso ($)'),
        ('SGD', 'Singapore Dollar (S$)'),
        ('HKD', 'Hong Kong Dollar (HK$)'),
        ('NZD', 'New Zealand Dollar (NZ$)'),
        ('SEK', 'Swedish Krona (kr)'),
        ('NOK', 'Norwegian Krone (kr)'),
        ('DKK', 'Danish Krone (kr)'),
        ('PLN', 'Polish Złoty (zł)'),
        ('RUB', 'Russian Ruble (₽)'),
    ]
    
    # Subscription & Billing
    subscription_status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS, default='trial')
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, default='starter')
    paid_until = models.DateField(help_text="The date their subscription is valid until")
    on_trial = models.BooleanField(default=True, help_text="If the organization is on trial")
    trial_ends = models.DateField(blank=True, null=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD', help_text="Preferred currency for billing and invoices")
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Usage Limits
    max_users = models.PositiveIntegerField(default=5)
    max_invoices_per_month = models.PositiveIntegerField(default=100)
    max_storage_gb = models.PositiveIntegerField(default=1)
    
    # Management
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_clients')
    account_manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_clients')
    
    # Timestamps
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(blank=True, null=True)
    
    # Additional Settings
    logo = models.ImageField(upload_to='client_logos/', blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#007bff', help_text="Brand primary color (hex)")
    notes = models.TextField(blank=True, null=True, help_text="Internal notes about the client")

    class Meta:
        ordering = ['name']
        verbose_name = 'Client Organization'
        verbose_name_plural = 'Client Organizations'

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('clients:client_detail', kwargs={'pk': self.pk})
    
    @property
    def is_trial_expired(self):
        """Check if trial period has expired"""
        if self.on_trial and self.trial_ends:
            return timezone.now().date() > self.trial_ends
        return False
    
    @property
    def is_subscription_expired(self):
        """Check if subscription has expired"""
        return timezone.now().date() > self.paid_until
    
    @property
    def days_until_expiry(self):
        """Days until subscription expires"""
        if self.paid_until:
            delta = self.paid_until - timezone.now().date()
            return delta.days
        return 0
    
    @property
    def current_user_count(self):
        """Get current number of users for this client"""
        # This would be implemented with proper tenant filtering
        return 0  # Placeholder
    
    @property
    def subscription_color(self):
        """Get color class for subscription status"""
        colors = {
            'trial': 'warning',
            'active': 'success',
            'expired': 'danger',
            'suspended': 'secondary',
            'cancelled': 'dark',
        }
        return colors.get(self.subscription_status, 'secondary')
    
    @property
    def currency_symbol(self):
        """Get the currency symbol for this client's currency"""
        symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'CAD': 'C$',
            'AUD': 'A$',
            'JPY': '¥',
            'CHF': 'CHF',
            'CNY': '¥',
            'INR': '₹',
            'BRL': 'R$',
            'ZAR': 'R',
            'MXN': '$',
            'SGD': 'S$',
            'HKD': 'HK$',
            'NZD': 'NZ$',
            'SEK': 'kr',
            'NOK': 'kr',
            'DKK': 'kr',
            'PLN': 'zł',
            'RUB': '₽',
        }
        return symbols.get(self.currency, '$')
    
    def formatted_monthly_fee(self):
        """Get formatted monthly fee with currency symbol"""
        return f"{self.currency_symbol}{self.monthly_fee:.2f}"
    
    def save(self, *args, **kwargs):
        # Set trial end date if not set
        if self.on_trial and not self.trial_ends:
            self.trial_ends = timezone.now().date() + timedelta(days=30)
        
        # Auto-update subscription status based on dates
        if self.is_subscription_expired:
            self.subscription_status = 'expired'
        elif self.on_trial and self.is_trial_expired:
            self.subscription_status = 'expired'
        
        super().save(*args, **kwargs)

class Domain(DomainMixin):
    """Domains associated with client organizations for multi-tenancy"""
    
    tenant = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='domains')
    is_active = models.BooleanField(default=True)
    ssl_enabled = models.BooleanField(default=True)
    
    # Timestamps
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['domain']
    
    def __str__(self):
        primary_indicator = " (Primary)" if self.is_primary else ""
        return f"{self.domain}{primary_indicator}"
    
    def get_full_url(self):
        """Get full URL with protocol"""
        protocol = "https" if self.ssl_enabled else "http"
        return f"{protocol}://{self.domain}"

class ClientContact(models.Model):
    """Contact persons for client organizations"""
    
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('billing', 'Billing Contact'),
        ('technical', 'Technical Contact'),
        ('primary', 'Primary Contact'),
        ('other', 'Other'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contacts')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='other')
    title = models.CharField(max_length=100, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
        unique_together = ['client', 'is_primary']  # Only one primary contact per client
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.client.name})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class ClientUsageLog(models.Model):
    """Track usage statistics for clients"""
    
    METRIC_TYPES = [
        ('users', 'Active Users'),
        ('invoices', 'Invoices Created'),
        ('storage', 'Storage Used (MB)'),
        ('api_calls', 'API Calls'),
        ('login', 'User Login'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='usage_logs')
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES)
    value = models.PositiveIntegerField()
    date_recorded = models.DateField(default=timezone.now)
    notes = models.CharField(max_length=255, blank=True, null=True)
    
    # Timestamps
    created_on = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date_recorded', 'metric_type']
        unique_together = ['client', 'metric_type', 'date_recorded']
    
    def __str__(self):
        return f"{self.client.name} - {self.get_metric_type_display()}: {self.value}"
