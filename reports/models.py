from django.db import models
from django.conf import settings
from django.utils import timezone

class ReportTemplate(models.Model):
    """Template for custom reports"""
    REPORT_TYPES = [
        ('financial', 'Financial Report'),
        ('invoice', 'Invoice Report'),
        ('customer', 'Customer Report'),
        ('analytics', 'Analytics Report'),
    ]
    
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField(blank=True, null=True)
    
    # Report configuration (stored as JSON)
    filters = models.JSONField(default=dict, blank=True)
    columns = models.JSONField(default=list, blank=True)
    
    # User management
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False, help_text="Make available to all users")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"

class ReportSchedule(models.Model):
    """Schedule for automatic report generation"""
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ]
    
    name = models.CharField(max_length=200)
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    
    # Recipients
    recipients = models.JSONField(default=list, help_text="Email addresses to send reports to")
    
    # Schedule configuration
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)
    next_run = models.DateTimeField()
    last_run = models.DateTimeField(blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # User management
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.get_frequency_display()}"

class GeneratedReport(models.Model):
    """Store generated report instances"""
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='generated_reports')
    schedule = models.ForeignKey(ReportSchedule, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Report details
    file_path = models.FileField(upload_to='reports/', blank=True, null=True)
    file_format = models.CharField(max_length=10, choices=[
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ], default='pdf')
    
    # Generation info
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    generation_time = models.DurationField(blank=True, null=True)
    
    # Report period
    date_from = models.DateField()
    date_to = models.DateField()
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.template.name} - {self.generated_at.strftime('%Y-%m-%d %H:%M')}"
