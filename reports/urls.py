from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Dashboard
    path('', views.reports_dashboard, name='dashboard'),
    
    # Financial Reports
    path('trial-balance/', views.trial_balance, name='trial_balance'),
    path('income-statement/', views.income_statement, name='income_statement'),
    path('balance-sheet/', views.balance_sheet, name='balance_sheet'),
    
    # Invoice Reports
    path('invoice-summary/', views.invoice_summary, name='invoice_summary'),
    path('aged-receivables/', views.aged_receivables, name='aged_receivables'),
    
    # Customer Reports
    path('customer-statement/<int:customer_id>/', views.customer_statement, name='customer_statement'),
    
    # Analytics
    path('revenue-analytics/', views.revenue_analytics, name='revenue_analytics'),
    
    # Report Templates
    path('templates/', views.ReportTemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.ReportTemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/edit/', views.ReportTemplateUpdateView.as_view(), name='template_edit'),
    path('templates/<int:pk>/delete/', views.ReportTemplateDeleteView.as_view(), name='template_delete'),
]
