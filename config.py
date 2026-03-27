"""
Centralized configuration for the chatbot system.
Loads from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""
    
    # Application
    APP_NAME: str = "Universal Chatbot Backend"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = ENVIRONMENT == "development"
    
    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    
    # Paths
    DATA_RAW_DIR: str = "data/raw"
    DATA_PROCESSED_DIR: str = "data/processed"
    LOGS_DIR: str = "logs"
    
    # Web Crawler Settings
    CRAWLER_TIMEOUT: int = 30  # seconds per page
    CRAWLER_MAX_DEPTH: int = 5
    CRAWLER_MAX_PAGES: int = 500
    CRAWLER_CONCURRENT_REQUESTS: int = 3
    CRAWLER_USER_AGENT: str = "ChatbotScraper/1.0 (+https://example.com/bot)"
    CRAWLER_RESPECT_ROBOTS_TXT: bool = True
    CRAWLER_RETRY_ATTEMPTS: int = 3
    
    # Chunking Settings
    CHUNK_SIZE: int = 500  # tokens
    CHUNK_OVERLAP: int = 50  # tokens
    CHUNK_MIN_SIZE: int = 100
    
    # Embedding Settings
    EMBEDDING_PROVIDER: str = "huggingface"  # "huggingface", "openai", "google"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_BATCH_SIZE: int = 32
    EMBEDDING_DIMENSION: int = 384  # For MiniLM-L6-v2; 1536 for OpenAI
    
    # OpenAI Settings (Optional for production)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"
    OPENAI_EMBEDDING_DIMENSION: int = 1536
    OPENAI_LLM_MODEL: str = "gpt-4"
    OPENAI_LLM_TEMPERATURE: float = 0.7
    OPENAI_REQUEST_TIMEOUT: int = 30
    
    # Google Gemini Settings (Optional for production)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_EMBEDDING_MODEL: str = "models/embedding-001"
    GEMINI_EMBEDDING_DIMENSION: int = 768
    GEMINI_LLM_MODEL: str = "gemini-1.5-flash"
    GEMINI_LLM_TEMPERATURE: float = 0.7
    
    # Vector Database Settings
    VECTOR_DB_PROVIDER: str = "faiss"  # "faiss" currently implemented
    CHROMADB_PATH: str = ".chroma_db"
    CHROMADB_COLLECTION_NAME: str = "chatbot_embeddings"
    
    # Pinecone Settings (Optional for production)
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    PINECONE_INDEX_NAME: str = "chatbot-index"
    
    # RAG Settings
    RAG_TOP_K_CHUNKS: int = 4
    RAG_CONFIDENCE_THRESHOLD: float = 0.5
    RAG_MAX_CONTEXT_LENGTH: int = 3000  # characters
    
    # Default Brand Rules
    DEFAULT_BRAND_TONE: str = "professional"
    DEFAULT_MAX_SENTENCES: int = 4
    DEFAULT_LANGUAGE: str = "en"
    
    # Database Settings
    DATABASE_URL: str = "sqlite:///./chatbot.db"
    # For PostgreSQL: "postgresql://user:password@localhost/chatbot_db"
    
    # Supabase PostgreSQL Settings
    SUPABASE_URL: str = "https://wzlkabxfdcxgvrqauiee.supabase.co"
    SUPABASE_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind6bGthYnhmZGN4Z3ZycWF1aWVlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTEyNzg2MTgsImV4cCI6MTc0Mjk5OTAyOH0.RfWE1Pz_Yx7kKYzXGlJJoRH9_pZBhNfZFGf0U5rI_N0"
    SUPABASE_PASSWORD: str = "Raju@3321##"
    USE_SUPABASE: bool = True  # Enable/disable Supabase integration
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" or "text"
    
    # CORS Settings
    CORS_ORIGINS: list = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    API_KEY_HEADER: str = "X-API-Key"
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }


# Global settings instance
settings = Settings()


def validate_settings() -> bool:
    """
    Validate critical settings based on environment.
    Returns True if valid, False otherwise.
    """
    if settings.ENVIRONMENT == "production":
        if not settings.OPENAI_API_KEY and settings.EMBEDDING_PROVIDER == "openai":
            logger.error("OPENAI_API_KEY is required for production with OpenAI embeddings")
            return False
        
        if not settings.GEMINI_API_KEY and settings.EMBEDDING_PROVIDER == "google":
            logger.error("GEMINI_API_KEY is required for production with Google Gemini embeddings")
            return False
        
        if not settings.SECRET_KEY.startswith("sk_"):
            logger.warning("SECRET_KEY should be changed from default in production")
    
    return True


if __name__ == "__main__":
    print("Configuration loaded successfully")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"API Server: {settings.API_HOST}:{settings.API_PORT}")
