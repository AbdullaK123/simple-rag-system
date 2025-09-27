from typing import Dict, Optional, Any

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """Large Language Model configuration settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env/.llm.env",
        env_prefix="",
        case_sensitive=False,
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # OpenAI Configuration
    openai_api_key: SecretStr = Field(default="", description="OpenAI API key")
    openai_org_id: Optional[str] = Field(default=None, description="OpenAI organization ID")
    
    # Model Selection
    chat_model: str = Field(default="gpt-4o-mini", description="Primary chat model")
    chat_model_fallback: str = Field(default="gpt-3.5-turbo", description="Fallback chat model")
    
    # Chat Model Parameters
    chat_temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    chat_max_tokens: int = Field(default=1000, ge=1, description="Maximum tokens in response")
    chat_top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    chat_frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    chat_presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Presence penalty")
    
    # Rate Limiting
    openai_rpm_limit: int = Field(default=3000, description="Requests per minute limit")
    openai_tpm_limit: int = Field(default=40000, description="Tokens per minute limit")
    openai_max_retries: int = Field(default=3, description="Maximum retry attempts")
    openai_timeout: int = Field(default=60, description="Request timeout in seconds")
    
    # System Prompts
    system_prompt_template: str = Field(default="default", description="System prompt template name")
    include_context_instructions: bool = Field(default=True, description="Include context usage instructions")
    response_format: str = Field(default="markdown", description="Preferred response format")
    
    # Conversation Settings
    max_conversation_history: int = Field(default=10, description="Maximum conversation turns to keep")
    include_chat_history: bool = Field(default=True, description="Include previous messages in context")
    conversation_timeout_minutes: int = Field(default=30, description="Conversation timeout in minutes")
    
    @property
    def model_presets(self) -> Dict[str, str]:
        """Predefined model configurations."""
        return {
            "fast": "gpt-4o-mini",
            "quality": "gpt-4o",
            "cheap": "gpt-3.5-turbo",
            "legacy": "gpt-3.5-turbo-instruct"
        }
    
    def get_chat_params(self) -> Dict[str, Any]:
        """Get chat completion parameters as a dictionary."""
        return {
            "model": self.chat_model,
            "temperature": self.chat_temperature,
            "max_tokens": self.chat_max_tokens,
            "top_p": self.chat_top_p,
            "frequency_penalty": self.chat_frequency_penalty,
            "presence_penalty": self.chat_presence_penalty
        }