from django.urls import path
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

app_name = 'clients'

@login_required
def dashboard(request):
    """Temporary clients dashboard view"""
    return render(request, 'clients/dashboard.html', {
        'title': 'Clients Dashboard',
        'message': 'Clients management coming soon!'
    })

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
]
