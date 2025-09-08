from app.config import Settings
from functools import lru_cache

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()