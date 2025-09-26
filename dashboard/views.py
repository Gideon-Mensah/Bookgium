from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from accounts.models import Transaction

def dashboard_view(request):
    # Aggregate totals
    return render(request, 'dashboard/index.html', {
        'total_revenue': ...,
        'total_expenses': ...,
        'net_profit': ...,
    })

