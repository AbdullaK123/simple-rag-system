import os
from pathlib import Path
from typing import List, Optional
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ValidationError

from .auth import AuthSettings
from .documents import DocumentSettings
from .embeddings import EmbeddingSettings
from .environment import EnvironmentSettings
from .llm import LLMSettings
from .logging import LoggingSettings
from .redis import RedisSettings
from .vectors import VectorSettings


class EnvFileManager:
    """Manages environment file loading and discovery."""
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path(__file__).parent.parent.parent
        self.env_dir = self.base_path / ".env"
    
    def get_base_files(self) -> List[str]:
        """Get base configuration files that should always be loaded."""
        base_files = [
            ".core.env",
            ".llm.env", 
            ".storage.env",
            ".logging.env",
            ".security.env",
            ".evaluation.env"
        ]
        return [str(self.env_dir / f) for f in base_files if (self.env_dir / f).exists()]
    
    def get_environment_files(self, environment: str) -> List[str]:
        """Get environment-specific files."""
        env_files = []
        candidates = [
            f".{environment}.env",
            ".dev.env" if environment == "development" else None,
            ".production.env" if environment == "production" else None,
        ]
        
        for file in candidates:
            if file and (self.env_dir / file).exists():
                env_files.append(str(self.env_dir / file))
        
        return env_files
    
    def get_local_overrides(self) -> List[str]:
        """Get local override files."""
        local_files = [".local.env"]
        return [str(self.env_dir / f) for f in local_files if (self.env_dir / f).exists()]
    
    def get_all_env_files(self, environment: Optional[str] = None) -> List[str]:
        """Get all environment files in order of precedence."""
        environment = environment or os.getenv("ENVIRONMENT", "development")
        
        env_files = []
        env_files.extend(self.get_base_files())
        env_files.extend(self.get_environment_files(environment))
        env_files.extend(self.get_local_overrides())
        
        return env_files


class SettingsValidator:
    """Validates configuration across all settings classes."""
    
    def __init__(self, settings: 'Settings'):
        self.settings = settings
    
    def validate_api_keys(self) -> None:
        """Validate required API keys."""
        # OpenAI API key validation
        api_key_value = self.settings.llm.openai_api_key.get_secret_value() if self.settings.llm.openai_api_key else ""
        if not api_key_value or api_key_value.strip() == "":
            raise ValueError("OpenAI API key is required")
    
    def validate_production_security(self) -> None:
        """Validate production-specific security requirements."""
        if not self.settings.environment.is_production:
            return
            
        # JWT secret validation
        jwt_secret = self.settings.auth.jwt_secret_key.get_secret_value()
        if jwt_secret == "your_jwt_secret_here":
            raise ValueError("JWT secret key must be changed in production")
    
    def validate_directories(self) -> None:
        """Ensure required directories exist."""
        directories = [
            self.settings.documents.upload_dir,
            self.settings.vectors.chroma_persist_dir,
            self.settings.logging.file_path.parent,
        ]
        
        for directory in directories:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
    
    def validate_model_compatibility(self) -> None:
        """Validate model configurations."""
        embedding_dims = self.settings.embeddings.current_model_dimensions
        if embedding_dims <= 0:
            raise ValueError(f"Invalid embedding dimensions: {embedding_dims}")
    
    def validate_all(self) -> bool:
        """Run all validations."""
        try:
            self.validate_api_keys()
            self.validate_production_security()
            self.validate_directories()
            self.validate_model_compatibility()
            return True
        except Exception as e:
            if self.settings.environment.is_development:
                print(f"Configuration validation failed: {e}")
                print(f"Loaded env files: {self.settings.get_loaded_env_files()}")
            return False


class Settings:
    """Master settings class that composes all configuration sections."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize all configuration sections."""
        self._env_manager = EnvFileManager(base_path)
        self._env_files = self._env_manager.get_all_env_files()
        
        # Initialize settings classes
        self._initialize_settings()
        
        # Setup validator
        self._validator = SettingsValidator(self)
    
    def _initialize_settings(self) -> None:
        """Initialize all settings classes with environment files."""
        try:
            self.environment = EnvironmentSettings(_env_file=self._env_files)
            self.auth = AuthSettings(_env_file=self._env_files)
            self.documents = DocumentSettings(_env_file=self._env_files)
            self.embeddings = EmbeddingSettings(_env_file=self._env_files)
            self.vectors = VectorSettings(_env_file=self._env_files)
            self.llm = LLMSettings(_env_file=self._env_files)
            self.redis = RedisSettings(_env_file=self._env_files)
            self.logging = LoggingSettings(_env_file=self._env_files)
        except ValidationError as e:
            print(f"Configuration validation error: {e}")
            raise
    
    def model_dump_config(self) -> dict:
        """Export all configuration sections as a dictionary."""
        return {
            "environment": self.environment.model_dump(),
            "auth": self.auth.model_dump(exclude={"jwt_secret_key", "api_keys"}),
            "documents": self.documents.model_dump(),
            "embeddings": self.embeddings.model_dump(),
            "vectors": self.vectors.model_dump(),
            "llm": self.llm.model_dump(exclude={"openai_api_key"}),
            "redis": self.redis.model_dump(exclude={"password", "sentinel_password"}),
            "logging": self.logging.model_dump()
        }
    
    def get_loaded_env_files(self) -> List[str]:
        """Get list of .env files that were actually loaded."""
        return self._env_files
    
    def validate_configuration(self) -> bool:
        """Validate the entire configuration setup."""
        return self._validator.validate_all()
    
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
    
    def reload_settings(self) -> None:
        """Reload all settings from environment files."""
        self._env_files = self._env_manager.get_all_env_files()
        self._initialize_settings()

    
    __all__ = [
        "Settings",
        "EnvironmentSettings",
        "AuthSettings", 
        "DocumentSettings",
        "EmbeddingSettings",
        "VectorSettings", 
        "LLMSettings",
        "RedisSettings",
        "LoggingSettings",
        "EnvFileManager",
        "SettingsValidator",
    ]