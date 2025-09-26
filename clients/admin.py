from django.contrib import admin
from .models import Client, Domain, ClientContact, ClientUsageLog

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'email', 'subscription_status', 'plan_type', 'currency', 
        'monthly_fee', 'is_active', 'created_on'
    ]
    list_filter = [
        'subscription_status', 'plan_type', 'currency', 'is_active', 
        'on_trial', 'created_on'
    ]
    search_fields = ['name', 'email', 'slug']
    readonly_fields = ['created_on', 'updated_on']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'email', 'phone', 'website', 'is_active')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country'),
            'classes': ('collapse',)
        }),
        ('Subscription & Billing', {
            'fields': (
                'subscription_status', 'plan_type', 'currency', 'monthly_fee', 
                'paid_until', 'on_trial', 'trial_ends'
            )
        }),
        ('Usage Limits', {
            'fields': ('max_users', 'max_invoices_per_month', 'max_storage_gb'),
            'classes': ('collapse',)
        }),
        ('Management', {
            'fields': ('account_manager', 'primary_color', 'logo', 'notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_on', 'updated_on'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'tenant', 'is_primary', 'is_active', 'ssl_enabled', 'created_on']
    list_filter = ['is_primary', 'is_active', 'ssl_enabled', 'created_on']
    search_fields = ['domain', 'tenant__name']

@admin.register(ClientContact)
class ClientContactAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'client', 'email', 'role', 'is_primary', 'is_active']
    list_filter = ['role', 'is_primary', 'is_active', 'created_on']
    search_fields = ['first_name', 'last_name', 'email', 'client__name']

@admin.register(ClientUsageLog)
class ClientUsageLogAdmin(admin.ModelAdmin):
    list_display = ['client', 'metric_type', 'value', 'date_recorded', 'created_on']
    list_filter = ['metric_type', 'date_recorded', 'created_on']
    search_fields = ['client__name', 'metric_type', 'notes']
    readonly_fields = ['created_on']
