# AI Assistant Settings Configuration

# Add this to your Django settings.py file:

# AI Assistant Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')  # Set this in your environment variables

# Add 'ai_assistant' to your INSTALLED_APPS
INSTALLED_APPS = [
    # ... your existing apps
    'ai_assistant',
]

# Optional: AI Assistant specific settings
AI_ASSISTANT_CONFIG = {
    'MODEL': 'gpt-4',  # or 'gpt-3.5-turbo' for lower cost
    'MAX_TOKENS': 500,
    'TEMPERATURE': 0.7,
    'ENABLE_CONTEXT_AWARENESS': True,
    'CACHE_RESPONSES': True,
    'CACHE_TIMEOUT': 3600,  # 1 hour
}

# Environment Variables (.env file):
# OPENAI_API_KEY=your_openai_api_key_here
