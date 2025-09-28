from typing import List, Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    """Authentication and authorization settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env/.security.env",
        env_prefix="",
        case_sensitive=False,
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # API Key Authentication
    api_key_required: bool = Field(default=False, description="Require API key for requests")
    api_keys: List[str] = Field(default_factory=list, description="Valid API keys")
    api_key_header: str = Field(default="X-API-Key", description="API key header name")
    
    # JWT Configuration
    jwt_secret_key: SecretStr = Field(description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_hours: int = Field(default=24, description="JWT token expiration in hours")
    jwt_refresh_expiration_days: int = Field(default=7, description="Refresh token expiration in days")

    hash_secret_key: SecretStr = Field(description="For password hashing")
    
    # Session Configuration
    session_timeout_minutes: int = Field(default=30, description="Session timeout in minutes")
    max_concurrent_sessions: int = Field(default=5, description="Maximum concurrent sessions per user")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=False, description="Enable rate limiting")
    rate_limit_requests_per_minute: int = Field(default=60, description="Requests per minute per user")
    rate_limit_burst: int = Field(default=10, description="Burst allowance")
    
    # User Management (for future expansion)
    allow_user_registration: bool = Field(default=False, description="Allow new user registration")
    require_email_verification: bool = Field(default=False, description="Require email verification")
    password_min_length: int = Field(default=8, description="Minimum password length")
    
    @property
    def jwt_config(self) -> dict:
        """Get JWT configuration dictionary."""
        return {
            "secret_key": self.jwt_secret_key.get_secret_value(),
            "algorithm": self.jwt_algorithm,
            "access_token_expire_hours": self.jwt_expiration_hours,
            "refresh_token_expire_days": self.jwt_refresh_expiration_days
        }
    
    def is_valid_api_key(self, api_key: str) -> bool:
        """Check if provided API key is valid."""
        if not self.api_key_required:
            return True
        return api_key in self.api_keys