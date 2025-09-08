# app/config/__init__.py
from pydantic import BaseModel
from functools import lru_cache

from .auth import AuthSettings
from .documents import DocumentSettings
from .embeddings import EmbeddingSettings
from .environment import EnvironmentSettings
from .llm import LLMSettings
from .logging import LoggingSettings
from .redis import RedisSettings
from .vectors import VectorSettings


class Settings(BaseModel):
    """Composed settings with all configuration sections."""
    
    environment: EnvironmentSettings = EnvironmentSettings()
    auth: AuthSettings = AuthSettings()
    documents: DocumentSettings = DocumentSettings()
    embeddings: EmbeddingSettings = EmbeddingSettings()
    vectors: VectorSettings = VectorSettings()
    llm: LLMSettings = LLMSettings()
    redis: RedisSettings = RedisSettings()
    logging: LoggingSettings = LoggingSettings()


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience instance
settings = get_settings()

__all__ = [
    "Settings", 
    "settings",
    # Individual settings classes
    "EnvironmentSettings",
    "AuthSettings",
    "DocumentSettings",
    "EmbeddingSettings",
    "VectorSettings", 
    "LLMSettings",
    "RedisSettings",
    "LoggingSettings",
]