import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # YouTube API
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', 'your_youtube_api_key_here')
    
    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT', 'https://your-resource.openai.azure.com/')
    AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY', 'your_azure_openai_key_here')
    AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-35-turbo-16k')
    AZURE_OPENAI_VERSION = os.getenv('AZURE_OPENAI_VERSION', '2023-05-15')
    AZURE_EMBEDDING_DEPLOYMENT = os.getenv('AZURE_EMBEDDING_DEPLOYMENT', 'text-embedding-ada-002')
    
    # Azure AI Search
    AZURE_SEARCH_ENDPOINT = os.getenv('AZURE_SEARCH_ENDPOINT', 'https://your-search-service.search.windows.net')
    AZURE_SEARCH_KEY = os.getenv('AZURE_SEARCH_KEY', 'your_search_key_here')
    AZURE_SEARCH_INDEX_NAME = os.getenv('AZURE_SEARCH_INDEX_NAME', 'tennis-ai-index')
    
    # Azure Blob Storage
    AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING', 'your_connection_string_here')
    AZURE_STORAGE_CONTAINER_NAME = os.getenv('AZURE_STORAGE_CONTAINER_NAME', 'transcripts')
    
    # Database configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/tennis_ai_db')
    
    # SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Local captions directory
    CAPTIONS_DIR = os.path.join(os.getcwd(), "captions")
    
    # Flag to use Azure Blob Storage instead of local files
    USE_BLOB_STORAGE = True
    
    # Application settings
    MAX_PLAYLIST_VIDEOS = 3
    CAPTIONS_DIR = os.path.join(os.getcwd(), "captions")