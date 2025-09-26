from django.contrib import admin
from .models import Customer, Invoice, InvoiceItem, Payment

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'city', 'created_at', 'is_active']
    list_filter = ['is_active', 'country', 'created_at']
    search_fields = ['name', 'email', 'phone']
    ordering = ['name']

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'issue_date', 'due_date', 'status', 'total_amount']
    list_filter = ['status', 'issue_date', 'due_date']
    search_fields = ['invoice_number', 'customer__name', 'customer__email']
    inlines = [InvoiceItemInline]
    ordering = ['-created_at']

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'description', 'quantity', 'unit_price', 'total']
    list_filter = ['invoice__status']
    search_fields = ['description', 'invoice__invoice_number']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'payment_date', 'payment_method', 'created_by']
    list_filter = ['payment_method', 'payment_date']
    search_fields = ['invoice__invoice_number', 'reference']
    ordering = ['-payment_date']
