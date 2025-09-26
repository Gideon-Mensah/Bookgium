# Bookgium AI Assistant Setup Guide

## Overview
I've created a comprehensive AI assistant system for your Bookgium accounting application. Here's how to set it up and train it.

## 1. Installation

### Install Dependencies
```bash
pip install -r requirements_ai.txt
```

### Environment Setup
Create a `.env` file in your project root:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### Django Settings
Add to your `settings.py`:
```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... existing apps
    'ai_assistant',
]

# AI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

AI_ASSISTANT_CONFIG = {
    'MODEL': 'gpt-4',  # or 'gpt-3.5-turbo' for lower cost
    'MAX_TOKENS': 500,
    'TEMPERATURE': 0.7,
}
```

## 2. Training Approaches

### A. Knowledge Base Approach (Recommended)
This is what I've implemented - it uses OpenAI's API with your custom knowledge base.

**Pros:**
- Quick to implement
- Easy to update knowledge
- Cost-effective
- No model training required

**How it works:**
1. The AI assistant has built-in knowledge about Bookgium features
2. Provides contextual help based on current page
3. Uses conversation context for better responses

### B. Fine-tuning Approach (Advanced)
For a more customized AI that speaks exactly like your application.

**Steps:**
1. Generate training data using `training.py`
2. Fine-tune a model with OpenAI
3. Use the fine-tuned model in responses

**Pros:**
- More accurate responses
- Better understanding of your terminology
- Consistent tone and style

**Cons:**
- More expensive
- Requires more setup
- Needs ongoing maintenance

## 3. Features Implemented

### ✅ Smart Context Awareness
- Detects current page (accounts, invoices, reports)
- Provides relevant quick-help suggestions
- Remembers conversation context

### ✅ User-Friendly Interface
- Clean chat interface
- Quick suggestion buttons
- Typing indicators
- Error handling

### ✅ Integration
- Added AI Assistant button to top navigation
- Floating AI button on all pages
- Seamless integration with existing UI

### ✅ Knowledge Base
- Built-in accounting knowledge
- Bookgium-specific instructions
- Role-based responses (Admin, Accountant, Viewer)

## 4. How Users Will Interact

### Quick Access
- Click the "AI Assistant" button in the top toolbar
- Use the floating robot icon on any page
- Get contextual help suggestions based on current page

### Example Interactions
- "How do I create a journal entry?"
- "What's the difference between assets and liabilities?"
- "How do I generate a balance sheet?"
- "Why won't my journal entry save?"

## 5. Training the AI

### Method 1: Knowledge Base Updates
Edit `ai_assistant/assistant.py` to add more specific knowledge:

```python
def _load_knowledge_base(self):
    return """
    Your custom knowledge here...
    Add specific procedures, common issues, etc.
    """
```

### Method 2: Learning from User Interactions
The system can track user feedback and improve over time:

1. Users rate AI responses (helpful/not helpful)
2. System logs interactions
3. Use feedback to improve knowledge base

### Method 3: Fine-tuning (Advanced)
1. Collect real user questions from your support team
2. Create training examples using `training.py`
3. Fine-tune a model with OpenAI's API

## 6. Cost Considerations

### Using GPT-4
- ~$0.03 per 1K tokens input
- ~$0.06 per 1K tokens output
- Average conversation: ~$0.01-0.05

### Using GPT-3.5-turbo
- ~$0.001 per 1K tokens input
- ~$0.002 per 1K tokens output
- Average conversation: ~$0.001-0.005

### Cost Optimization Tips
- Use GPT-3.5-turbo for basic questions
- Implement response caching
- Set token limits
- Use knowledge base to reduce API calls

## 7. Maintenance & Updates

### Regular Updates
1. Monitor user feedback
2. Update knowledge base monthly
3. Add new features as you develop them
4. Review and improve unclear responses

### Performance Monitoring
- Track response times
- Monitor API usage and costs
- Analyze user satisfaction
- Review conversation logs

## 8. Testing

### Before Going Live
1. Test common accounting questions
2. Verify role-based responses
3. Test error handling
4. Check mobile responsiveness

### Sample Test Questions
- "How do I balance my books?"
- "What reports should I run monthly?"
- "How do I handle foreign currency?"
- "Why is my trial balance not balancing?"

## 9. Future Enhancements

### Phase 2 Features
- Integration with actual account data
- Automated journal entry suggestions
- Report interpretation
- Anomaly detection in financial data

### Advanced Features
- Voice interaction
- Document analysis (OCR for receipts)
- Automated bookkeeping suggestions
- Integration with bank feeds

## Getting Started Checklist

- [ ] Install dependencies
- [ ] Set up OpenAI API key
- [ ] Add to Django settings
- [ ] Run migrations
- [ ] Test basic functionality
- [ ] Customize knowledge base
- [ ] Deploy and monitor

## Support

The AI assistant is designed to reduce your support workload by handling common questions automatically. Users get instant help 24/7, and you can focus on more complex customer needs.

Start with the basic setup and gradually enhance based on user feedback and needs!
