from django.contrib import admin
from .models import AuditLog, UserSession, AuditSettings


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'content_type', 'object_repr', 'ip_address']
    list_filter = ['action', 'content_type', 'timestamp']
    search_fields = ['user__username', 'object_repr', 'notes']
    readonly_fields = ['timestamp', 'user', 'action', 'content_type', 'object_id', 
                      'object_repr', 'changes', 'ip_address', 'user_agent', 'session_key']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'login_time', 'logout_time', 'is_active', 'ip_address']
    list_filter = ['is_active', 'login_time']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['user', 'session_key', 'ip_address', 'user_agent', 'login_time', 'logout_time']
    date_hierarchy = 'login_time'
    ordering = ['-login_time']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AuditSettings)
class AuditSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Model Auditing', {
            'fields': ('audit_accounts', 'audit_journal_entries', 'audit_transactions', 
                      'audit_users', 'audit_clients', 'audit_invoices')
        }),
        ('Action Auditing', {
            'fields': ('audit_create', 'audit_update', 'audit_delete', 'audit_view', 'audit_login')
        }),
        ('Retention & Notifications', {
            'fields': ('retention_days', 'email_on_critical_changes', 'notification_email')
        }),
    )
    
    def has_add_permission(self, request):
        return not AuditSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
