from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()


class AuditLog(models.Model):
    """
    Model to track all changes to important models in the system.
    Uses Django's ContentType framework to track changes to any model.
    """
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('post_journal', 'Post Journal Entry'),
        ('unpost_journal', 'Unpost Journal Entry'),
    ]

    # User who performed the action
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='audit_logs'
    )
    
    # Action performed
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    
    # Object that was affected (using generic foreign key)
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Object representation (to keep record even if object is deleted)
    object_repr = models.CharField(max_length=200, blank=True)
    
    # Changes made (stored as JSON)
    changes = models.JSONField(default=dict, blank=True)
    
    # Additional context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Additional notes
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        return f"{self.user} {self.action} {self.object_repr} at {self.timestamp}"

    @property
    def changes_display(self):
        """Return a user-friendly display of changes"""
        if not self.changes:
            return "No changes recorded"
        
        changes_list = []
        for field, change_data in self.changes.items():
            if isinstance(change_data, dict) and 'old' in change_data and 'new' in change_data:
                old_val = change_data.get('old', 'None')
                new_val = change_data.get('new', 'None')
                changes_list.append(f"{field}: '{old_val}' → '{new_val}'")
            else:
                changes_list.append(f"{field}: {change_data}")
        
        return "; ".join(changes_list)


class UserSession(models.Model):
    """
    Track user sessions for audit purposes
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='audit_sessions'
    )
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    login_time = models.DateTimeField(default=timezone.now)
    logout_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-login_time']
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'

    def __str__(self):
        return f"{self.user.username} - {self.login_time}"

    @property
    def duration(self):
        """Calculate session duration"""
        if self.logout_time:
            return self.logout_time - self.login_time
        return timezone.now() - self.login_time


class AuditSettings(models.Model):
    """
    Settings for audit logging
    """
    # Which models to audit
    audit_accounts = models.BooleanField(default=True, help_text="Audit Account model changes")
    audit_journal_entries = models.BooleanField(default=True, help_text="Audit Journal Entry changes")
    audit_transactions = models.BooleanField(default=True, help_text="Audit Transaction changes")
    audit_users = models.BooleanField(default=True, help_text="Audit User changes")
    audit_clients = models.BooleanField(default=False, help_text="Audit Client changes")
    audit_invoices = models.BooleanField(default=False, help_text="Audit Invoice changes")
    
    # Retention settings
    retention_days = models.PositiveIntegerField(
        default=365,
        help_text="Number of days to keep audit logs (0 = forever)"
    )
    
    # Audit actions
    audit_create = models.BooleanField(default=True, help_text="Audit create actions")
    audit_update = models.BooleanField(default=True, help_text="Audit update actions")
    audit_delete = models.BooleanField(default=True, help_text="Audit delete actions")
    audit_view = models.BooleanField(default=False, help_text="Audit view actions (creates many logs)")
    audit_login = models.BooleanField(default=True, help_text="Audit login/logout actions")
    
    # Email notifications
    email_on_critical_changes = models.BooleanField(
        default=False,
        help_text="Send email notifications for critical changes"
    )
    notification_email = models.EmailField(
        blank=True,
        help_text="Email address for audit notifications"
    )
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Audit Settings'
        verbose_name_plural = 'Audit Settings'

    def __str__(self):
        return "Audit Settings"

    @classmethod
    def get_settings(cls):
        """Get or create audit settings"""
        try:
            settings, created = cls.objects.get_or_create(pk=1)
            return settings
        except Exception:
            # Return a default settings object if we can't access the database
            # (e.g., during migrations)
            default_settings = cls()
            default_settings.pk = 1
            return default_settings
