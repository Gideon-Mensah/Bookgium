from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    path('', views.AuditDashboardView.as_view(), name='dashboard'),
    path('logs/', views.AuditLogListView.as_view(), name='log_list'),
    path('logs/<int:pk>/', views.AuditLogDetailView.as_view(), name='log_detail'),
    path('sessions/', views.UserSessionListView.as_view(), name='session_list'),
    path('api/chart-data/', views.audit_chart_data, name='chart_data'),
]
