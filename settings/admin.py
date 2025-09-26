from django.contrib import admin
from .models import CompanySettings

@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = ['organization_name', 'organization_email', 'currency', 'fiscal_year_start']
    fieldsets = (
        ('Organization Information', {
            'fields': ('organization_name', 'organization_address', 'organization_phone', 
                      'organization_email', 'organization_website', 'organization_logo')
        }),
        ('Financial Settings', {
            'fields': ('fiscal_year_start', 'currency', 'tax_rate')
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one company settings instance
        if CompanySettings.objects.exists():
            return False
        return super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of company settings
        return False
