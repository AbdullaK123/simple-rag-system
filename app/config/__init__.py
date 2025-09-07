import os
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

from .auth import AuthSettings
from .documents import DocumentSettings
from .embeddings import EmbeddingSettings
from .environment import EnvironmentSettings
from .llm import LLMSettings
from .logging import LoggingSettings
from .redis import RedisSettings
from .vectors import VectorSettings


def get_env_files() -> List[str]:
    """Get list of .env files to load, in order of precedence."""
    base_path = Path(__file__).parent.parent.parent
    env_dir = base_path / ".env"
    
    # Base files (loaded first)
    base_files = [
        ".core.env",
        ".llm.env", 
        ".storage.env",
        ".logging.env",
        ".security.env",
        ".evaluation.env"
    ]
    
    env_files = []
    
    # Add base files that exist
    for file in base_files:
        file_path = env_dir / file
        if file_path.exists():
            env_files.append(str(file_path))
    
    # Environment-specific overrides
    environment = os.getenv("ENVIRONMENT", "development")
    env_specific_files = [
        f".{environment}.env",
        ".dev.env" if environment == "development" else None,
        ".prod.env" if environment == "production" else None,
    ]
    
    for file in env_specific_files:
        if file:
            file_path = env_dir / file
            if file_path.exists():
                env_files.append(str(file_path))
    
    # Local overrides (loaded last)
    local_env = env_dir / ".local.env"
    if local_env.exists():
        env_files.append(str(local_env))
    
    return env_files


class Settings:
    """Master settings class that composes all configuration sections."""
    
    def __init__(self):
        """Initialize all configuration sections."""
        # Load environment files first
        env_files = get_env_files()
        
        # Initialize each settings class with the same env files
        self.environment = EnvironmentSettings(_env_file=env_files)
        self.auth = AuthSettings(_env_file=env_files)
        self.documents = DocumentSettings(_env_file=env_files)
        self.embeddings = EmbeddingSettings(_env_file=env_files)
        self.vectors = VectorSettings(_env_file=env_files)
        self.llm = LLMSettings(_env_file=env_files)
        self.redis = RedisSettings(_env_file=env_files)
        self.logging = LoggingSettings(_env_file=env_files)
    
    def model_dump_config(self) -> dict:
        """Export all configuration sections as a dictionary."""
        return {
            "environment": self.environment.model_dump(),
            "auth": self.auth.model_dump(exclude={"jwt_secret_key", "api_keys"}),  # Exclude sensitive data
            "documents": self.documents.model_dump(),
            "embeddings": self.embeddings.model_dump(),
            "vectors": self.vectors.model_dump(),
            "llm": self.llm.model_dump(exclude={"openai_api_key"}),  # Exclude sensitive data
            "redis": self.redis.model_dump(exclude={"password", "sentinel_password"}),  # Exclude sensitive data
            "logging": self.logging.model_dump()
        }
    
    def get_loaded_env_files(self) -> List[str]:
        """Get list of .env files that were actually loaded."""
        return get_env_files()
    
    def validate_configuration(self) -> bool:
        """Validate the entire configuration setup."""
        try:
            # Check required API keys
            if not self.llm.openai_api_key or not self.llm.openai_api_key.get_secret_value():
                raise ValueError("OpenAI API key is required")
            
            # Validate JWT secret in production
            if self.environment.is_production and self.auth.jwt_secret_key.get_secret_value() == "your_jwt_secret_here":
                raise ValueError("JWT secret key must be changed in production")
            
            # Validate directory permissions
            if not self.documents.upload_dir.exists():
                self.documents.upload_dir.mkdir(parents=True, exist_ok=True)
            
            if not self.vectors.chroma_persist_dir.exists():
                self.vectors.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
            
            if not self.logging.file_path.parent.exists():
                self.logging.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Validate model compatibility
            embedding_dims = self.embeddings.current_model_dimensions
            if embedding_dims <= 0:
                raise ValueError(f"Invalid embedding dimensions: {embedding_dims}")
            
            return True
            
        except Exception as e:
            if self.environment.is_development:
                print(f"Configuration validation failed: {e}")
                print(f"Loaded env files: {self.get_loaded_env_files()}")
            return False
    
    @property
    def cache_settings(self) -> dict:
        """Get unified cache configuration."""
        return {
            "backend": "redis" if self.redis.host else "memory",
            "redis_url": self.redis.connection_url if self.redis.host else None,
            "default_ttl": 3600,
            "key_prefix": f"{self.environment.environment}:rag:",
            "compress": True
        }


# Export all classes for direct import
__all__ = [
    "Settings",
    "EnvironmentSettings",
    "AuthSettings", 
    "DocumentSettings",
    "EmbeddingSettings",
    "VectorSettings", 
    "LLMSettings",
    "RedisSettings",
    "LoggingSettings"
]