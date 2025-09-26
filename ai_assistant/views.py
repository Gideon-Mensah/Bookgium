from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

from .assistant import get_ai_response

@login_required
def ai_chat_view(request):
    """Main AI chat interface"""
    return render(request, 'ai_assistant/chat.html', {
        'title': 'AI Assistant'
    })

@login_required
@require_POST
@csrf_exempt
def ai_chat_api(request):
    """API endpoint for AI chat"""
    try:
        data = json.loads(request.body)
        question = data.get('question', '')
        current_page = data.get('current_page', '')
        
        if not question:
            return JsonResponse({'error': 'Question is required'}, status=400)
        
        # Get AI response
        response = get_ai_response(
            question=question,
            user=request.user,
            current_page=current_page
        )
        
        return JsonResponse({
            'response': response,
            'success': True
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'An error occurred: {str(e)}',
            'success': False
        }, status=500)

@login_required
def contextual_help_api(request):
    """Get contextual help suggestions"""
    current_page = request.GET.get('page', '')
    
    from .assistant import BookgiumAIAssistant
    assistant = BookgiumAIAssistant()
    suggestions = assistant.get_contextual_help(current_page, request.user.role)
    
    return JsonResponse({
        'suggestions': suggestions,
        'success': True
    })
