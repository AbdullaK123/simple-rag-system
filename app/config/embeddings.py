from typing import Dict

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EmbeddingSettings(BaseSettings):
    """Embedding model configuration settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        env_file_encoding="utf-8"
    )
    
    # Model Configuration
    embedding_model: str = Field(default="text-embedding-3-small", description="Primary embedding model")
    embedding_model_fallback: str = Field(default="text-embedding-ada-002", description="Fallback embedding model")
    embedding_dimensions: int = Field(default=1536, description="Embedding vector dimensions")
    
    # Processing Settings
    embedding_batch_size: int = Field(default=100, description="Batch size for embedding requests")
    embedding_max_retries: int = Field(default=3, description="Maximum retry attempts")
    embedding_timeout: int = Field(default=30, description="Request timeout in seconds")
    
    @property
    def model_configs(self) -> Dict[str, Dict[str, any]]:
        """Available embedding model configurations."""
        return {
            "text-embedding-3-small": {
                "dimensions": 1536,
                "max_tokens": 8191,
                "cost_per_1k": 0.00002
            },
            "text-embedding-3-large": {
                "dimensions": 3072,
                "max_tokens": 8191,
                "cost_per_1k": 0.00013
            },
            "text-embedding-ada-002": {
                "dimensions": 1536,
                "max_tokens": 8191,
                "cost_per_1k": 0.0001
            }
        }
    
    def get_model_info(self, model_name: str = None) -> Dict[str, any]:
        """Get configuration info for specified model or current model."""
        model = model_name or self.embedding_model
        return self.model_configs.get(model, {})
    
    @property
    def current_model_dimensions(self) -> int:
        """Get dimensions for the current embedding model."""
        model_info = self.get_model_info()
        return model_info.get("dimensions", self.embedding_dimensions)