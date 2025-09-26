from django.contrib import admin
from .models import ReportTemplate, ReportSchedule, GeneratedReport

@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'created_by', 'is_public', 'created_at']
    list_filter = ['report_type', 'is_public', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'report_type', 'description', 'is_public')
        }),
        ('Configuration', {
            'fields': ('filters', 'columns'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = ['name', 'template', 'frequency', 'status', 'next_run', 'created_by']
    list_filter = ['frequency', 'status', 'created_at']
    search_fields = ['name', 'template__name']
    readonly_fields = ['created_at', 'updated_at', 'last_run']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'template', 'frequency', 'status')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'next_run', 'last_run')
        }),
        ('Recipients', {
            'fields': ('recipients',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ['template', 'generated_at', 'generated_by', 'file_format', 'date_from', 'date_to']
    list_filter = ['file_format', 'generated_at', 'template__report_type']
    search_fields = ['template__name', 'generated_by__username']
    readonly_fields = ['generated_at', 'generation_time']
    
    fieldsets = (
        (None, {
            'fields': ('template', 'schedule', 'file_format')
        }),
        ('Report Period', {
            'fields': ('date_from', 'date_to')
        }),
        ('File', {
            'fields': ('file_path',)
        }),
        ('Generation Info', {
            'fields': ('generated_by', 'generated_at', 'generation_time'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Prevent manual creation of generated reports
        return False
