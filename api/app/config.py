from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    gemini_api_key: Optional[str] = None
    database_url: Optional[str] = None
    embedding_model: str = "text-embedding-004"  # Google's embedding model
    max_relevant_memories: int = 3
    conversation_timeout_minutes: int = (
        5  # Tiempo sin actividad para considerar conversación terminada
    )

    class Config:
        env_file = ".env"


settings = Settings()
