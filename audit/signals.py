from django.db.models.signals import post_save, post_delete, pre_save
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import AuditLog, UserSession, AuditSettings
from .utils import get_client_ip, get_user_agent, get_model_changes
import threading

User = get_user_model()

# Thread-local storage to store request information
_thread_locals = threading.local()


def set_current_request(request):
    """Set the current request in thread-local storage"""
    _thread_locals.request = request


def get_current_request():
    """Get the current request from thread-local storage"""
    return getattr(_thread_locals, 'request', None)


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log user login"""
    settings = AuditSettings.get_settings()
    if not settings.audit_login:
        return
    
    # Create or update user session
    session_key = request.session.session_key
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # End any existing active sessions for this user
    UserSession.objects.filter(user=user, is_active=True).update(
        is_active=False,
        logout_time=timezone.now()
    )
    
    # Create new session
    UserSession.objects.create(
        user=user,
        session_key=session_key,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    # Create audit log
    AuditLog.objects.create(
        user=user,
        action='login',
        ip_address=ip_address,
        user_agent=user_agent,
        session_key=session_key,
        notes=f'User logged in from {ip_address}'
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout"""
    settings = AuditSettings.get_settings()
    if not settings.audit_login:
        return
    
    if user and hasattr(request, 'session'):
        session_key = request.session.session_key
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        # Update user session
        UserSession.objects.filter(
            user=user,
            session_key=session_key,
            is_active=True
        ).update(
            is_active=False,
            logout_time=timezone.now()
        )
        
        # Create audit log
        AuditLog.objects.create(
            user=user,
            action='logout',
            ip_address=ip_address,
            user_agent=user_agent,
            session_key=session_key,
            notes=f'User logged out from {ip_address}'
        )


@receiver(pre_save)
def store_original_instance(sender, instance, **kwargs):
    """Store original instance data before save for comparison"""
    if not should_audit_model(sender):
        return
    
    if instance.pk:  # Only for updates
        try:
            original = sender.objects.get(pk=instance.pk)
            instance._original_instance = original
        except sender.DoesNotExist:
            instance._original_instance = None


@receiver(post_save)
def log_model_save(sender, instance, created, **kwargs):
    """Log model creation and updates"""
    if not should_audit_model(sender):
        return
    
    settings = AuditSettings.get_settings()
    if created and not settings.audit_create:
        return
    if not created and not settings.audit_update:
        return
    
    request = get_current_request()
    user = getattr(request, 'user', None) if request else None
    
    # Skip if user is not authenticated or is anonymous
    if not user or not user.is_authenticated:
        return
    
    action = 'create' if created else 'update'
    changes = {}
    
    if not created and hasattr(instance, '_original_instance') and instance._original_instance:
        changes = get_model_changes(instance._original_instance, instance)
    
    # Don't log if no changes were made
    if not created and not changes:
        return
    
    content_type = ContentType.objects.get_for_model(sender)
    
    AuditLog.objects.create(
        user=user,
        action=action,
        content_type=content_type,
        object_id=instance.pk,
        object_repr=str(instance)[:200],
        changes=changes,
        ip_address=get_client_ip(request) if request else None,
        user_agent=get_user_agent(request) if request else None,
        session_key=request.session.session_key if request and hasattr(request, 'session') else None,
        notes=f'{action.title()} {sender._meta.verbose_name}'
    )


@receiver(post_delete)
def log_model_delete(sender, instance, **kwargs):
    """Log model deletion"""
    if not should_audit_model(sender):
        return
    
    settings = AuditSettings.get_settings()
    if not settings.audit_delete:
        return
    
    request = get_current_request()
    user = getattr(request, 'user', None) if request else None
    
    # Skip if user is not authenticated or is anonymous
    if not user or not user.is_authenticated:
        return
    
    content_type = ContentType.objects.get_for_model(sender)
    
    AuditLog.objects.create(
        user=user,
        action='delete',
        content_type=content_type,
        object_id=instance.pk,
        object_repr=str(instance)[:200],
        ip_address=get_client_ip(request) if request else None,
        user_agent=get_user_agent(request) if request else None,
        session_key=request.session.session_key if request and hasattr(request, 'session') else None,
        notes=f'Deleted {sender._meta.verbose_name}'
    )


def should_audit_model(model):
    """Determine if a model should be audited based on settings"""
    model_name = model._meta.model_name.lower()
    app_name = model._meta.app_label.lower()
    
    # Don't audit the audit models themselves
    if app_name == 'audit':
        return False
    
    # During migrations, just audit important models with default settings
    try:
        from .models import AuditSettings
        settings = AuditSettings.get_settings()
        
        # Check specific model settings
        if model_name == 'account' and app_name == 'accounts':
            return settings.audit_accounts
        elif model_name == 'journalentry' and app_name == 'accounts':
            return settings.audit_journal_entries
        elif model_name == 'transaction' and app_name == 'accounts':
            return settings.audit_transactions
        elif model_name == 'customuser' and app_name == 'users':
            return settings.audit_users
        elif app_name == 'clients':
            return settings.audit_clients
        elif app_name == 'invoices':
            return settings.audit_invoices
    except:
        # If we can't get settings (e.g., during migrations), use defaults
        pass
    
    # Default to auditing important models
    important_models = [
        'account', 'journalentry', 'journalentryline', 'transaction',
        'customuser', 'client', 'invoice'
    ]
    
    return model_name in important_models


def log_journal_posting(journal_entry, user, request=None):
    """Manually log journal entry posting/unposting"""
    action = 'post_journal' if journal_entry.is_posted else 'unpost_journal'
    
    AuditLog.objects.create(
        user=user,
        action=action,
        content_type=ContentType.objects.get_for_model(journal_entry),
        object_id=journal_entry.pk,
        object_repr=str(journal_entry)[:200],
        ip_address=get_client_ip(request) if request else None,
        user_agent=get_user_agent(request) if request else None,
        session_key=request.session.session_key if request and hasattr(request, 'session') else None,
        notes=f'Journal entry {action.replace("_", " ")}'
    )
