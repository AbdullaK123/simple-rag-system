from typing import List, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentSettings(BaseSettings):
    """Environment and application settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        env_file_encoding="utf-8"
    )
    
    # Environment
    environment: Literal["development", "staging", "production"] = Field(default="development", description="Application environment")
    debug: bool = Field(default=True, description="Enable debug mode")
    
    # API Server
    api_host: str = Field(default="0.0.0.0", description="API host address")
    api_port: int = Field(default=8000, ge=1, le=65535, description="API port")
    
    # Security
    api_key_required: bool = Field(default=False, description="Require API key for requests")
    allowed_origins: List[str] = Field(default_factory=lambda: ["*"], description="CORS allowed origins")
    cors_enabled: bool = Field(default=True, description="Enable CORS")
    max_request_size_mb: int = Field(default=100, description="Maximum request size in MB")
    
    # Content Security
    scan_for_pii: bool = Field(default=False, description="Scan uploaded content for PII")
    block_malicious_files: bool = Field(default=True, description="Block potentially malicious files")
    virus_scan_enabled: bool = Field(default=False, description="Enable virus scanning")
    
    # Development Features
    dev_mode: bool = Field(default=True, description="Development mode")
    reload_on_change: bool = Field(default=True, description="Auto-reload on file changes")
    detailed_errors: bool = Field(default=True, description="Show detailed error messages")
    
    # Testing
    run_startup_tests: bool = Field(default=False, description="Run tests on startup")
    mock_external_apis: bool = Field(default=False, description="Mock external API calls")
    test_data_dir: str = Field(default="./tests/data", description="Test data directory")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    @property
    def server_config(self) -> dict:
        """Get server configuration for uvicorn."""
        return {
            "host": self.api_host,
            "port": self.api_port,
            "reload": self.reload_on_change and self.is_development,
            "debug": self.debug and self.is_development
        }