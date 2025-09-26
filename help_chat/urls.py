from django.urls import path
from . import views

app_name = 'help_chat'

urlpatterns = [
    # Chat interface
    path('', views.ChatView.as_view(), name='chat'),
    path('new/', views.new_chat, name='new_chat'),
    path('send/', views.send_message, name='send_message'),
    path('session/<str:session_id>/messages/', views.get_session_messages, name='get_session_messages'),
    path('session/<str:session_id>/delete/', views.delete_session, name='delete_session'),
    path('rate/', views.rate_message, name='rate_message'),
    
    # Knowledge base
    path('knowledge-base/', views.KnowledgeBaseView.as_view(), name='knowledge_base'),
    path('knowledge-base/<int:kb_id>/', views.knowledge_base_detail, name='knowledge_base_detail'),
    
    # FAQ
    path('faq/', views.FAQView.as_view(), name='faq'),
]
