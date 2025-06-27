from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    gemini_api_key: Optional[str] = None
    database_url: Optional[str] = None

    # Modelos de Gemini configurables
    embedding_model: str = "text-embedding-004"  # Modelo para embeddings
    dialogue_model: str = "gemma-3n-e4b-it"  # Modelo para generación de diálogo
    personality_model: str = "gemma-3n-e4b-it"  # Modelo para análisis de personalidad
    emotional_model: str = "gemma-3n-e4b-it"  # Modelo para análisis emocional
    memory_consolidation_model: str = (
        "gemma-3n-e4b-it"  # Modelo para consolidación de memoria
    )

    # Configuraciones adicionales
    max_relevant_memories: int = 3
    conversation_timeout_minutes: int = (
        5  # Tiempo sin actividad para considerar conversación terminada
    )

    class Config:
        env_file = ".env"


settings = Settings()
