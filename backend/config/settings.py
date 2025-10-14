import os
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
APP_CONFIG = {
    # API configuration
    'GROQ_API_URL': 'https://neuron.npci.org.in/autopilot70b/v1/chat/completions',
    'LLAMA_MODEL': 'llama-3.3-70b-versatile',
    'GROQ_API_KEY': os.getenv('GROQ_API_KEY', ''),
    'PROVIDER': 'openai',

    # Embedding Configuration
    'EMBEDDING_MODEL': 'all-MiniLM-L6-v2',
    'SIMILARITY_THRESHOLD': 0.1,
    'MAX_RETRIEVAL_CHUNKS': 5,

    # Text Processing
    'CHUNK_SIZE': 500,
    'CHUNK_OVERLAP': 50,
    'MAX_TOKENS': 1000,
    'TEMPERATURE': 0.7,

    # File Handling
    'UPLOAD_DIR': 'data/uploads',
    'CACHE_DIR': 'data/cache',
    'MAX_FILE_SIZE': 10 * 1024 * 1024, # 10MB
    'ALLOWED_EXTENSIONS': ['.pdf', '.xlsx', '.xls'], # Added Excel extensions

    # UI Configuration
    'MAX_CONVERSATION_HISTORY': 6, # Last 3 exchanges
    'PAGE_TITLE': 'PDF Chatbot',
    'PAGE_ICON': '⚙️'
}
