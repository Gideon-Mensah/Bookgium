from django.contrib import admin
from .models import Client, ClientNote

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'status', 'company_type', 'created_at', 'created_by']
    list_filter = ['status', 'company_type', 'created_at']
    search_fields = ['name', 'email', 'contact_person', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'email', 'phone', 'website')
        }),
        ('Company Information', {
            'fields': ('company_type', 'registration_number', 'tax_id')
        }),
        ('Contact Person', {
            'fields': ('contact_person', 'contact_title')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country')
        }),
        ('Business Information', {
            'fields': ('status', 'credit_limit', 'payment_terms')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ClientNote)
class ClientNoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'client', 'created_by', 'created_at']
    list_filter = ['created_at', 'client']
    search_fields = ['title', 'content', 'client__name']
    readonly_fields = ['created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
