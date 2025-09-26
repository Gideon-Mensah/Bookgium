from django.contrib import admin
from .models import Account, Transaction, JournalEntry, JournalEntryLine, SourceDocument

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'account_type', 'parent', 'is_active', 'balance', 'created_by']
    list_filter = ['account_type', 'is_active', 'created_by']
    search_fields = ['code', 'name', 'description']
    ordering = ['code']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by for new objects
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['account', 'date', 'description', 'transaction_type', 'amount', 'created_by']
    list_filter = ['date', 'transaction_type', 'account__account_type', 'created_by']
    search_fields = ['description', 'notes', 'account__name']
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by for new objects
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['id', 'date', 'description', 'reference', 'is_posted', 'total_debits', 'total_credits', 'is_balanced', 'created_by']
    list_filter = ['date', 'is_posted', 'created_by']
    search_fields = ['description', 'reference', 'notes']
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']
    readonly_fields = ['total_debits', 'total_credits', 'is_balanced']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(JournalEntryLine)
class JournalEntryLineAdmin(admin.ModelAdmin):
    list_display = ['journal_entry', 'account', 'entry_type', 'amount', 'description']
    list_filter = ['entry_type', 'account__account_type', 'journal_entry__date']
    search_fields = ['description', 'account__name', 'journal_entry__description']
    ordering = ['-journal_entry__date', 'entry_type', 'account__code']


@admin.register(SourceDocument)
class SourceDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'transaction', 'journal_entry', 'file_size_formatted', 'uploaded_by', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at', 'uploaded_by']
    search_fields = ['title', 'description', 'transaction__description', 'journal_entry__description']
    date_hierarchy = 'uploaded_at'
    ordering = ['-uploaded_at']
    readonly_fields = ['file_size', 'content_type', 'uploaded_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
    
    def has_change_permission(self, request, obj=None):
        # Only allow editing by the uploader or superuser
        if obj and obj.uploaded_by != request.user and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        # Only allow deletion by the uploader or superuser
        if obj and obj.uploaded_by != request.user and not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)
