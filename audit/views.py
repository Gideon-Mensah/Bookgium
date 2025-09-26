from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from .models import AuditLog, UserSession, AuditSettings
from django.shortcuts import render
from django.http import JsonResponse
import json


class AuditLogListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View to display audit logs"""
    model = AuditLog
    template_name = 'audit/audit_log_list.html'
    context_object_name = 'logs'
    paginate_by = 50
    
    def test_func(self):
        """Only allow admin users to view audit logs"""
        return self.request.user.is_staff or self.request.user.role == 'admin'
    
    def get_queryset(self):
        queryset = AuditLog.objects.select_related('user', 'content_type').all()
        
        # Filter by user
        user_id = self.request.GET.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by action
        action = self.request.GET.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        # Filter by content type
        content_type_id = self.request.GET.get('content_type')
        if content_type_id:
            queryset = queryset.filter(content_type_id=content_type_id)
        
        # Filter by date range
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)
        
        # Search in object representation and notes
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(object_repr__icontains=search) |
                Q(notes__icontains=search) |
                Q(user__username__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter options
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        context['users'] = User.objects.filter(audit_logs__isnull=False).distinct()
        context['actions'] = AuditLog.ACTION_CHOICES
        context['content_types'] = ContentType.objects.filter(auditlog__isnull=False).distinct()
        
        # Add current filters to context
        context['current_filters'] = {
            'user': self.request.GET.get('user', ''),
            'action': self.request.GET.get('action', ''),
            'content_type': self.request.GET.get('content_type', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
            'search': self.request.GET.get('search', ''),
        }
        
        return context


class AuditLogDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View to display detailed audit log"""
    model = AuditLog
    template_name = 'audit/audit_log_detail.html'
    context_object_name = 'log'
    
    def test_func(self):
        """Only allow admin users to view audit logs"""
        return self.request.user.is_staff or self.request.user.role == 'admin'


class UserSessionListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View to display user sessions"""
    model = UserSession
    template_name = 'audit/user_session_list.html'
    context_object_name = 'sessions'
    paginate_by = 50
    
    def test_func(self):
        """Only allow admin users to view user sessions"""
        return self.request.user.is_staff or self.request.user.role == 'admin'
    
    def get_queryset(self):
        queryset = UserSession.objects.select_related('user').all()
        
        # Filter by user
        user_id = self.request.GET.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by active status
        is_active = self.request.GET.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active=is_active == 'true')
        
        return queryset


class AuditDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Dashboard view for audit overview"""
    template_name = 'audit/audit_dashboard.html'
    
    def test_func(self):
        """Only allow admin users to view audit dashboard"""
        return self.request.user.is_staff or self.request.user.role == 'admin'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date ranges
        now = timezone.now()
        today = now.date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Basic statistics
        context['total_logs'] = AuditLog.objects.count()
        context['logs_today'] = AuditLog.objects.filter(timestamp__date=today).count()
        context['logs_week'] = AuditLog.objects.filter(timestamp__date__gte=week_ago).count()
        context['logs_month'] = AuditLog.objects.filter(timestamp__date__gte=month_ago).count()
        
        # Active sessions
        context['active_sessions'] = UserSession.objects.filter(is_active=True).count()
        
        # Recent activity
        context['recent_logs'] = AuditLog.objects.select_related('user', 'content_type')[:10]
        
        # Action statistics
        context['action_stats'] = (
            AuditLog.objects
            .values('action')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        
        # User activity statistics
        context['user_stats'] = (
            AuditLog.objects
            .filter(timestamp__date__gte=week_ago)
            .values('user__username')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        
        # Model statistics
        context['model_stats'] = (
            AuditLog.objects
            .filter(timestamp__date__gte=week_ago)
            .values('content_type__model')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        
        return context


def audit_chart_data(request):
    """API endpoint for audit chart data"""
    if not (request.user.is_staff or request.user.role == 'admin'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Get activity data for the last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Daily activity count
    daily_activity = []
    current_date = start_date
    
    while current_date <= end_date:
        count = AuditLog.objects.filter(timestamp__date=current_date).count()
        daily_activity.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'count': count
        })
        current_date += timedelta(days=1)
    
    # Action distribution
    action_distribution = list(
        AuditLog.objects
        .values('action')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    return JsonResponse({
        'daily_activity': daily_activity,
        'action_distribution': action_distribution
    })
