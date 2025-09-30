from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    # Dashboard
    path('', views.ClientDashboardView.as_view(), name='dashboard'),
    
    # Client CRUD
    path('list/', views.ClientListView.as_view(), name='list'),
    path('create/', views.ClientCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ClientDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ClientUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.ClientDeleteView.as_view(), name='delete'),
    
    # Client Actions
    path('<int:pk>/extend-trial/', views.ExtendTrialView.as_view(), name='extend_trial'),
    path('<int:pk>/suspend/', views.SuspendClientView.as_view(), name='suspend'),
    path('<int:pk>/activate/', views.ActivateClientView.as_view(), name='activate'),
    
    # Domain Management
    path('<int:client_pk>/domains/', views.DomainListView.as_view(), name='domains'),
    path('<int:client_pk>/domains/create/', views.DomainCreateView.as_view(), name='domain_create'),
    path('domains/<int:pk>/edit/', views.DomainUpdateView.as_view(), name='domain_edit'),
    path('domains/<int:pk>/delete/', views.DomainDeleteView.as_view(), name='domain_delete'),
    
    # Contact Management
    path('<int:client_pk>/contacts/', views.ContactListView.as_view(), name='contacts'),
    path('<int:client_pk>/contacts/create/', views.ContactCreateView.as_view(), name='contact_create'),
    path('contacts/<int:pk>/edit/', views.ContactUpdateView.as_view(), name='contact_edit'),
    path('contacts/<int:pk>/delete/', views.ContactDeleteView.as_view(), name='contact_delete'),
    
    # AJAX Endpoints
    path('ajax/search/', views.ClientSearchAjaxView.as_view(), name='ajax_search'),
    path('ajax/<int:pk>/stats/', views.ClientStatsAjaxView.as_view(), name='ajax_stats'),
]
