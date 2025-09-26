from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    # Dashboard
    path('', views.payroll_dashboard, name='dashboard'),
    
    # Employee URLs
    path('employees/', views.EmployeeListView.as_view(), name='employee_list'),
    path('employees/new/', views.EmployeeCreateView.as_view(), name='employee_create'),
    path('employees/<int:pk>/', views.EmployeeDetailView.as_view(), name='employee_detail'),
    path('employees/<int:pk>/edit/', views.EmployeeUpdateView.as_view(), name='employee_update'),
    
    # Payroll Period URLs
    path('periods/', views.PayrollPeriodListView.as_view(), name='period_list'),
    path('periods/new/', views.PayrollPeriodCreateView.as_view(), name='period_create'),
    path('periods/<int:pk>/', views.PayrollPeriodDetailView.as_view(), name='period_detail'),
    
    # Payroll Processing
    path('periods/<int:period_id>/process/', views.process_payroll, name='process_payroll'),
    path('periods/<int:period_id>/journal/', views.create_payroll_journal_entries, name='create_journal_entries'),
]
