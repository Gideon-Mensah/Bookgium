import re
import uuid
from typing import List, Dict, Optional, Tuple
from django.db.models import Q
from django.utils import timezone
from .models import ChatSession, ChatMessage, KnowledgeBase, FAQ

class ChatService:
    """Service class for handling chat operations and AI responses"""
    
    def __init__(self):
        self.common_greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
        self.common_thanks = ['thank you', 'thanks', 'thank', 'appreciate']
        self.common_goodbyes = ['bye', 'goodbye', 'see you', 'thanks again']
        
        # Define response templates for different types of queries
        self.response_templates = {
            'greeting': [
                "Hello! I'm your Bookgium assistant. I'm here to help you navigate and understand our accounting application. What would you like to know?",
                "Hi there! Welcome to Bookgium help chat. I can assist you with questions about transactions, journal entries, reports, and more. How can I help you today?",
                "Hey! I'm here to help you make the most of Bookgium. Feel free to ask me about any features or how to perform specific tasks."
            ],
            'thanks': [
                "You're welcome! Is there anything else I can help you with?",
                "Happy to help! Feel free to ask if you have any other questions.",
                "Glad I could assist! Let me know if you need help with anything else."
            ],
            'goodbye': [
                "Goodbye! Feel free to come back anytime if you have questions about Bookgium.",
                "See you later! I'm always here to help with your accounting questions.",
                "Take care! Don't hesitate to reach out if you need assistance with Bookgium."
            ]
        }

    def get_or_create_session(self, user, session_id: str = None) -> ChatSession:
        """Get existing session or create a new one"""
        if session_id:
            try:
                session = ChatSession.objects.get(session_id=session_id, user=user, is_active=True)
                return session
            except ChatSession.DoesNotExist:
                pass
        
        # Create new session
        session_id = str(uuid.uuid4())
        session = ChatSession.objects.create(
            user=user,
            session_id=session_id,
            title="New Chat"
        )
        return session

    def process_message(self, user, message: str, session_id: str = None) -> Tuple[ChatSession, str]:
        """Process user message and generate AI response"""
        session = self.get_or_create_session(user, session_id)
        
        # Save user message
        ChatMessage.objects.create(
            session=session,
            message_type='user',
            content=message
        )
        
        # Generate AI response
        response = self._generate_response(message.lower().strip())
        
        # Save AI response
        ChatMessage.objects.create(
            session=session,
            message_type='assistant',
            content=response
        )
        
        # Update session title if it's the first meaningful message
        if session.get_messages_count() <= 2 and session.title == "New Chat":
            session.title = self._generate_session_title(message)
            session.save()
        
        # Update session timestamp
        session.updated_at = timezone.now()
        session.save()
        
        return session, response

    def _generate_response(self, message: str) -> str:
        """Generate AI response based on user message"""
        # Check for greetings
        if any(greeting in message for greeting in self.common_greetings):
            return self._get_random_response('greeting')
        
        # Check for thanks
        if any(thanks in message for thanks in self.common_thanks):
            return self._get_random_response('thanks')
        
        # Check for goodbyes
        if any(goodbye in message for goodbye in self.common_goodbyes):
            return self._get_random_response('goodbye')
        
        # Search knowledge base and FAQs
        knowledge_response = self._search_knowledge_base(message)
        if knowledge_response:
            return knowledge_response
        
        faq_response = self._search_faqs(message)
        if faq_response:
            return faq_response
        
        # Pattern-based responses for common queries
        pattern_response = self._get_pattern_response(message)
        if pattern_response:
            return pattern_response
        
        # Default response with suggestions
        return self._get_default_response()

    def _search_knowledge_base(self, message: str) -> Optional[str]:
        """Search knowledge base for relevant information"""
        # Extract keywords from message
        keywords = self._extract_keywords(message)
        
        if not keywords:
            return None
        
        # Search in knowledge base
        query = Q()
        for keyword in keywords:
            query |= Q(title__icontains=keyword) | Q(content__icontains=keyword) | Q(keywords__icontains=keyword)
        
        knowledge_entries = KnowledgeBase.objects.filter(query, is_active=True)[:3]
        
        if knowledge_entries:
            response = "Based on your question, here's what I found:\n\n"
            for entry in knowledge_entries:
                response += f"**{entry.title}**\n{entry.content[:300]}...\n\n"
                entry.increment_view_count()
            
            response += "Would you like more specific information about any of these topics?"
            return response
        
        return None

    def _search_faqs(self, message: str) -> Optional[str]:
        """Search FAQs for relevant questions"""
        keywords = self._extract_keywords(message)
        
        if not keywords:
            return None
        
        query = Q()
        for keyword in keywords:
            query |= Q(question__icontains=keyword) | Q(answer__icontains=keyword)
        
        faqs = FAQ.objects.filter(query, is_active=True)[:2]
        
        if faqs:
            response = "Here are some frequently asked questions that might help:\n\n"
            for faq in faqs:
                response += f"**Q: {faq.question}**\n{faq.answer}\n\n"
                faq.increment_view_count()
            
            return response
        
        return None

    def _get_pattern_response(self, message: str) -> Optional[str]:
        """Generate responses based on message patterns"""
        responses = {
            # Account-related queries
            r'(?:how|create|add|new).*(?:account|chart)': 
                "To create a new account:\n1. Go to 'Chart of Accounts' in the main menu\n2. Click 'Add New Account'\n3. Select the account type (Asset, Liability, Equity, Revenue, or Expense)\n4. Enter the account name and details\n5. Click 'Save'\n\nWould you like more details about account types?",
            
            # Transaction queries
            r'(?:how|create|add|record).*(?:transaction|entry)':
                "To record a transaction:\n1. Navigate to 'Transactions' > 'New Transaction'\n2. Select the transaction date\n3. Choose the accounts to debit and credit\n4. Enter the amounts (they must balance)\n5. Add a description\n6. You can also upload source documents as evidence\n7. Click 'Save'\n\nNeed help with journal entries instead?",
            
            # Journal entry queries
            r'(?:journal|entry).*(?:how|create|add)':
                "To create a journal entry:\n1. Go to 'Journal Entries' > 'New Entry'\n2. Select the date\n3. Add multiple line items with accounts, debits, and credits\n4. Ensure total debits equal total credits\n5. Add a reference and description\n6. Upload supporting documents if needed\n7. Save the entry\n\nWould you like examples of common journal entries?",
            
            # Client queries
            r'(?:client|customer).*(?:add|create|manage)':
                "To manage clients:\n1. Go to 'Clients' in the main menu\n2. Click 'Add New Client' to create a client\n3. Fill in contact information and details\n4. You can view all clients in the client list\n5. Edit or update client information as needed\n\nClients are used for invoicing and tracking customer transactions.",
            
            # Report queries
            r'(?:report|balance|income|statement)':
                "Available reports in Bookgium:\n• **Balance Sheet** - Shows assets, liabilities, and equity\n• **Income Statement** - Shows revenue and expenses\n• **Trial Balance** - Lists all accounts with balances\n• **General Ledger** - Detailed account transactions\n\nAccess reports from the 'Reports' menu. You can filter by date ranges and export to PDF or Excel.",
            
            # Settings queries
            r'(?:setting|configure|currency|preference)':
                "In Settings, you can:\n• Change your default currency\n• Update company information\n• Manage account preferences\n• Configure system settings\n\nThe currency setting affects how amounts are displayed throughout the application. Currently supported currencies include USD, EUR, GBP, and more.",
            
            # Help with features
            r'(?:feature|what|can|do)':
                "Bookgium is a comprehensive accounting application with these key features:\n\n📊 **Chart of Accounts** - Manage your account structure\n💰 **Transactions** - Record financial transactions\n📝 **Journal Entries** - Create complex accounting entries\n👥 **Client Management** - Track customers and contacts\n🧾 **Invoicing** - Create and manage invoices\n📈 **Reports** - Generate financial statements\n⚙️ **Settings** - Customize your experience\n\nWhat specific feature would you like to learn about?"
        }
        
        for pattern, response in responses.items():
            if re.search(pattern, message, re.IGNORECASE):
                return response
        
        return None

    def _extract_keywords(self, message: str) -> List[str]:
        """Extract relevant keywords from message"""
        # Remove common words and extract meaningful terms
        common_words = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but', 'in', 'with', 'to', 'for', 'of', 'as', 'by', 'how', 'what', 'when', 'where', 'why', 'can', 'could', 'would', 'should', 'i', 'me', 'my', 'you', 'your'}
        
        words = re.findall(r'\b\w+\b', message.lower())
        keywords = [word for word in words if len(word) > 2 and word not in common_words]
        
        return keywords[:10]  # Limit to top 10 keywords

    def _generate_session_title(self, message: str) -> str:
        """Generate a title for the chat session based on first message"""
        # Extract key terms and create a title
        message = message.strip()
        if len(message) > 50:
            return message[:47] + "..."
        return message.title()

    def _get_random_response(self, response_type: str) -> str:
        """Get a random response from templates"""
        import random
        responses = self.response_templates.get(response_type, [])
        return random.choice(responses) if responses else ""

    def _get_default_response(self) -> str:
        """Default response when no specific match is found"""
        return """I'd be happy to help you with Bookgium! Here are some things I can assist you with:

🔹 **Getting Started** - How to set up and navigate the application
🔹 **Chart of Accounts** - Creating and managing your account structure  
🔹 **Transactions** - Recording financial transactions
🔹 **Journal Entries** - Creating accounting entries
🔹 **Client Management** - Managing customer information
🔹 **Invoicing** - Creating and sending invoices
🔹 **Reports** - Generating financial statements
🔹 **Settings** - Configuring your preferences

You can ask questions like:
• "How do I create a new account?"
• "How do I record a transaction?"
• "What reports are available?"
• "How do I add a new client?"

What would you like to know more about?"""

    def get_session_history(self, session: ChatSession) -> List[Dict]:
        """Get formatted message history for a session"""
        messages = session.messages.all()
        history = []
        
        for message in messages:
            history.append({
                'type': message.message_type,
                'content': message.content,
                'timestamp': message.timestamp,
                'is_helpful': message.is_helpful
            })
        
        return history

    def get_user_sessions(self, user) -> List[ChatSession]:
        """Get all active sessions for a user"""
        return ChatSession.objects.filter(user=user, is_active=True)

    def mark_message_helpful(self, message_id: int, is_helpful: bool):
        """Mark an assistant message as helpful or not"""
        try:
            message = ChatMessage.objects.get(id=message_id, message_type='assistant')
            message.is_helpful = is_helpful
            message.save()
        except ChatMessage.DoesNotExist:
            pass
