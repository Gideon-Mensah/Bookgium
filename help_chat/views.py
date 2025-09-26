from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import models
import json
from .models import ChatSession, ChatMessage, KnowledgeBase, FAQ
from .services import ChatService

class ChatView(LoginRequiredMixin, TemplateView):
    """Main chat interface view"""
    template_name = 'help_chat/chat.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chat_service = ChatService()
        
        # Get user's chat sessions
        context['sessions'] = chat_service.get_user_sessions(self.request.user)
        
        # Get current session if provided
        session_id = self.request.GET.get('session')
        if session_id:
            try:
                current_session = ChatSession.objects.get(
                    session_id=session_id, 
                    user=self.request.user, 
                    is_active=True
                )
                context['current_session'] = current_session
                context['messages'] = chat_service.get_session_history(current_session)
            except ChatSession.DoesNotExist:
                pass
        
        return context

@login_required
@require_http_methods(["POST"])
def send_message(request):
    """Handle sending a message to the chat"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not message:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)
        
        chat_service = ChatService()
        session, response = chat_service.process_message(
            user=request.user,
            message=message,
            session_id=session_id
        )
        
        return JsonResponse({
            'success': True,
            'response': response,
            'session_id': session.session_id,
            'session_title': session.title
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def new_chat(request):
    """Create a new chat session"""
    try:
        chat_service = ChatService()
        session = chat_service.get_or_create_session(request.user)
        
        return JsonResponse({
            'success': True,
            'session_id': session.session_id,
            'redirect_url': f'/help-chat/?session={session.session_id}'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def get_session_messages(request, session_id):
    """Get messages for a specific session"""
    try:
        session = get_object_or_404(
            ChatSession, 
            session_id=session_id, 
            user=request.user, 
            is_active=True
        )
        
        chat_service = ChatService()
        messages = chat_service.get_session_history(session)
        
        return JsonResponse({
            'success': True,
            'messages': messages,
            'session_title': session.title
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def rate_message(request):
    """Rate an assistant message as helpful or not"""
    try:
        data = json.loads(request.body)
        message_id = data.get('message_id')
        is_helpful = data.get('is_helpful')
        
        if message_id is None or is_helpful is None:
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
        
        chat_service = ChatService()
        chat_service.mark_message_helpful(message_id, is_helpful)
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["DELETE"])
def delete_session(request, session_id):
    """Delete a chat session"""
    try:
        session = get_object_or_404(
            ChatSession, 
            session_id=session_id, 
            user=request.user
        )
        
        session.is_active = False
        session.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

class KnowledgeBaseView(LoginRequiredMixin, TemplateView):
    """View for browsing the knowledge base"""
    template_name = 'help_chat/knowledge_base.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        category = self.request.GET.get('category')
        search = self.request.GET.get('search')
        
        # Get knowledge base entries
        knowledge_base = KnowledgeBase.objects.filter(is_active=True)
        
        if category:
            knowledge_base = knowledge_base.filter(category=category)
        
        if search:
            knowledge_base = knowledge_base.filter(
                models.Q(title__icontains=search) |
                models.Q(content__icontains=search) |
                models.Q(keywords__icontains=search)
            )
        
        context['knowledge_base'] = knowledge_base
        context['categories'] = KnowledgeBase.CATEGORY_CHOICES
        context['current_category'] = category
        context['search_query'] = search
        
        return context

class FAQView(LoginRequiredMixin, TemplateView):
    """View for frequently asked questions"""
    template_name = 'help_chat/faq.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        category = self.request.GET.get('category')
        
        # Get FAQs
        faqs = FAQ.objects.filter(is_active=True)
        
        if category:
            faqs = faqs.filter(category=category)
        
        context['faqs'] = faqs
        context['categories'] = FAQ._meta.get_field('category').choices
        context['current_category'] = category
        
        return context

@login_required
def knowledge_base_detail(request, kb_id):
    """View a specific knowledge base entry"""
    entry = get_object_or_404(KnowledgeBase, id=kb_id, is_active=True)
    entry.increment_view_count()
    
    return render(request, 'help_chat/knowledge_base_detail.html', {
        'entry': entry
    })
