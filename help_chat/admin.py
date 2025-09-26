from django.contrib import admin
from .models import ChatSession, ChatMessage, KnowledgeBase, FAQ, UserFeedback

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'created_at', 'updated_at', 'is_active', 'get_messages_count']
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['title', 'user__username', 'user__email']
    readonly_fields = ['session_id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'message_type', 'timestamp', 'content_preview', 'is_helpful']
    list_filter = ['message_type', 'timestamp', 'is_helpful']
    search_fields = ['content', 'session__title', 'session__user__username']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'

@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'is_active', 'view_count', 'created_at', 'updated_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['title', 'content', 'keywords']
    readonly_fields = ['view_count', 'created_at', 'updated_at']
    fieldsets = [
        (None, {
            'fields': ['title', 'category', 'is_active']
        }),
        ('Content', {
            'fields': ['content', 'keywords']
        }),
        ('Statistics', {
            'fields': ['view_count', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'is_active', 'view_count', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['question', 'answer']
    readonly_fields = ['view_count', 'created_at']
    fieldsets = [
        (None, {
            'fields': ['question', 'category', 'is_active']
        }),
        ('Answer', {
            'fields': ['answer']
        }),
        ('Statistics', {
            'fields': ['view_count', 'created_at'],
            'classes': ['collapse']
        })
    ]

@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'rating', 'created_at', 'feedback_preview']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__username', 'feedback_text']
    readonly_fields = ['created_at']
    
    def feedback_preview(self, obj):
        return obj.feedback_text[:100] + '...' if len(obj.feedback_text) > 100 else obj.feedback_text
    feedback_preview.short_description = 'Feedback Preview'
