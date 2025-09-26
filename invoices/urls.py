from django.urls import path
from . import views

app_name = 'invoices'

urlpatterns = [
    # Dashboard
    path('', views.invoices_dashboard, name='dashboard'),
    
    # Invoice URLs
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/create/', views.InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:pk>/edit/', views.InvoiceUpdateView.as_view(), name='invoice_update'),
    path('invoices/<int:pk>/delete/', views.InvoiceDeleteView.as_view(), name='invoice_delete'),
    
    # Customer URLs
    path('customers/', views.CustomerListView.as_view(), name='customer_list'),
    path('customers/create/', views.CustomerCreateView.as_view(), name='customer_create'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/<int:pk>/edit/', views.CustomerUpdateView.as_view(), name='customer_update'),
    path('customers/<int:pk>/delete/', views.CustomerDeleteView.as_view(), name='customer_delete'),
    
    # AJAX URLs for invoice items
    path('invoices/<int:invoice_id>/add-item/', views.add_invoice_item, name='add_invoice_item'),
    path('invoice-items/<int:item_id>/delete/', views.delete_invoice_item, name='delete_invoice_item'),
    
    # Payment URLs
    path('invoices/<int:invoice_id>/add-payment/', views.add_payment, name='add_payment'),
    
    # Reports
    path('reports/', views.invoice_reports, name='reports'),
]
