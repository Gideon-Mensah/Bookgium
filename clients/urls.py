from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Client CRUD
    path('', views.ClientListView.as_view(), name='list'),
    path('create/', views.ClientCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ClientDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ClientUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.ClientDeleteView.as_view(), name='delete'),
    
    # Client utilities
    path('<int:pk>/toggle-status/', views.toggle_client_status, name='toggle_status'),
    
    # Client notes
    path('<int:pk>/notes/add/', views.add_client_note, name='add_note'),
    path('<int:pk>/notes/<int:note_pk>/delete/', views.delete_client_note, name='delete_note'),
    
    # AJAX endpoints
    path('search/', views.client_search_ajax, name='search_ajax'),
]
