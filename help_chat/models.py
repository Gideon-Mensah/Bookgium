from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class ChatSession(models.Model):
    """A chat session between a user and the AI assistant"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    session_id = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255, default='New Chat')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def get_messages_count(self):
        return self.messages.count()

class ChatMessage(models.Model):
    """Individual messages in a chat session"""
    MESSAGE_TYPES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_helpful = models.BooleanField(null=True, blank=True)  # User feedback on assistant messages
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.session.title} - {self.message_type}: {self.content[:50]}..."

class KnowledgeBase(models.Model):
    """Knowledge base entries for the AI assistant"""
    CATEGORY_CHOICES = [
        ('getting_started', 'Getting Started'),
        ('accounts', 'Chart of Accounts'),
        ('transactions', 'Transactions'),
        ('journal_entries', 'Journal Entries'),
        ('clients', 'Client Management'),
        ('invoices', 'Invoicing'),
        ('reports', 'Reports'),
        ('settings', 'Settings'),
        ('troubleshooting', 'Troubleshooting'),
        ('general', 'General'),
    ]
    
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    content = models.TextField()
    keywords = models.TextField(help_text="Comma-separated keywords for search")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    view_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['category', 'title']
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.title}"
    
    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])

class FAQ(models.Model):
    """Frequently Asked Questions"""
    question = models.CharField(max_length=500)
    answer = models.TextField()
    category = models.CharField(max_length=50, choices=KnowledgeBase.CATEGORY_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    view_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-view_count', 'question']
    
    def __str__(self):
        return self.question
    
    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])

class UserFeedback(models.Model):
    """User feedback on chat responses"""
    RATING_CHOICES = [
        (1, 'Very Poor'),
        (2, 'Poor'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Excellent'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, null=True, blank=True)
    rating = models.IntegerField(choices=RATING_CHOICES)
    feedback_text = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user.username} - Rating: {self.rating}/5"
