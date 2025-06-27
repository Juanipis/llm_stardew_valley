from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # LLM Provider settings
    LLM_PROVIDER: str = "google"  # 'google', 'openai', or 'ollama'

    # API Keys
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Base URLs for local models
    ollama_api_base_url: Optional[str] = None

    database_url: Optional[str] = None

    # Model names (can be overridden by environment variables)
    # These are the default models if not specified in .env
    embedding_model: str = "text-embedding-004"
    dialogue_model: str = "gemini-1.5-flash-latest"
    personality_model: str = "gemini-1.5-flash-latest"
    emotional_model: str = "gemini-1.5-flash-latest"
    memory_consolidation_model: str = "gemini-1.5-flash-latest"

    # Configuraciones adicionales
    max_relevant_memories: int = 3
    conversation_timeout_minutes: int = (
        5  # Tiempo sin actividad para considerar conversación terminada
    )

    class Config:
        env_file = ".env"


settings = Settings()
