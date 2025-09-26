from django.urls import path
from . import views

app_name = 'settings'

urlpatterns = [
    path('company/', views.company_settings, name='company_settings'),
]
