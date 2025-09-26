from django.urls import path
from . import views

app_name = 'ai_assistant'

urlpatterns = [
    path('chat/', views.ai_chat_view, name='chat'),
    path('api/chat/', views.ai_chat_api, name='chat_api'),
    path('api/help/', views.contextual_help_api, name='contextual_help'),
]
