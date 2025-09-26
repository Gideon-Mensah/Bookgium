from django.urls import path
from . import views
from . import opening_balance_views

app_name = 'accounts'

urlpatterns = [
    # Dashboard and Chart of Accounts
    path('', views.accounts_dashboard, name='dashboard'),
    path('chart/', views.chart_of_accounts, name='chart_of_accounts'),
    path('accounts/<int:account_id>/statement/', views.account_statement, name='account_statement'),
    
    # Opening Balance Management URLs
    path('opening-balances/', opening_balance_views.OpeningBalanceManagementView.as_view(), name='opening_balance_management'),
    path('opening-balances/process/', opening_balance_views.process_opening_balances, name='process_opening_balances'),
    path('opening-balances/bulk-edit/', opening_balance_views.BulkOpeningBalanceEditView.as_view(), name='bulk_opening_balance_edit'),
    path('opening-balances/template/', opening_balance_views.download_opening_balance_template, name='download_opening_balance_template'),
    path('opening-balances/export/', opening_balance_views.export_current_opening_balances, name='export_current_opening_balances'),
    path('opening-balances/preview/', opening_balance_views.opening_balance_preview, name='opening_balance_preview'),
    path('accounts/<int:account_id>/opening-balance/', opening_balance_views.single_account_opening_balance, name='single_account_opening_balance'),
    
    # Account Statement Export URLs
    path('accounts/<int:account_id>/statement/export/excel/', views.export_account_statement_excel, name='export_account_statement_excel'),
    path('accounts/<int:account_id>/statement/export/csv/', views.export_account_statement_csv, name='export_account_statement_csv'),
    path('accounts/<int:account_id>/statement/export/pdf/', views.export_account_statement_pdf, name='export_account_statement_pdf'),
    
    # Debug URLs (only for staff users)
    path('accounts/<int:account_id>/debug/', views.debug_revenue_account, name='debug_account'),
    path('revenue-overview/', views.revenue_accounts_overview, name='revenue_overview'),
    
    # Account URLs
    path('accounts/', views.AccountListView.as_view(), name='account_list'),
    path('accounts/create/', views.AccountCreateView.as_view(), name='account_create'),
    path('accounts/<int:pk>/', views.AccountDetailView.as_view(), name='account_detail'),
    path('accounts/<int:pk>/edit/', views.AccountUpdateView.as_view(), name='account_update'),
    path('accounts/<int:pk>/delete/', views.AccountDeleteView.as_view(), name='account_delete'),
    
    # Transaction URLs (Deprecated - use Journal Entries instead)
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/create/', views.TransactionCreateView.as_view(), name='transaction_create'),
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    path('transactions/<int:pk>/edit/', views.TransactionUpdateView.as_view(), name='transaction_update'),
    path('transactions/<int:pk>/delete/', views.TransactionDeleteView.as_view(), name='transaction_delete'),
    
    # Journal Entry URLs (Double-Entry System)
    path('journal-entries/', views.JournalEntryListView.as_view(), name='journal_entry_list'),
    path('journal-entries/create/', views.JournalEntryCreateView.as_view(), name='journal_entry_create'),
    path('journal-entries/quick/', views.QuickJournalEntryCreateView.as_view(), name='quick_journal_entry_create'),
    path('journal-entries/<int:pk>/', views.JournalEntryDetailView.as_view(), name='journal_entry_detail'),
    # path('journal-entries/<int:pk>/post/', views.post_journal_entry, name='post_journal_entry'),
    
    # Source Document URLs - Temporarily commented out
    # path('documents/<int:pk>/download/', views.download_source_document, name='download_source_document'),
    # path('documents/<int:pk>/delete/', views.delete_source_document, name='delete_source_document'),
]
