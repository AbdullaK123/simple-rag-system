from pathlib import Path
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingSettings(BaseSettings):
    """Loguru logging configuration settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        case_sensitive=False,
        env_file_encoding="utf-8"
    )
    
    # Basic Logging
    level: Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO", description="Log level")
    format: Literal["json", "text", "detailed"] = Field(default="json", description="Log format")
    
    # Console Logging
    console_enabled: bool = Field(default=True, description="Enable console logging")
    console_colorize: bool = Field(default=True, description="Colorize console output")
    
    # File Logging
    file_enabled: bool = Field(default=True, description="Enable file logging")
    file_path: Path = Field(default=Path("./storage/logs/app.log"), description="Log file path")
    rotation_size: str = Field(default="10 MB", description="Log rotation size (e.g., '10 MB', '100 KB')")
    retention_time: str = Field(default="30 days", description="Log retention time (e.g., '30 days', '1 week')")
    compression: str = Field(default="gz", description="Log file compression format")
    
    # Error Logging
    error_file_enabled: bool = Field(default=True, description="Separate error log file")
    error_file_path: Path = Field(default=Path("./storage/logs/error.log"), description="Error log file path")
    
    # Feature-Specific Logging
    enable_query_logging: bool = Field(default=True, description="Log user queries")
    enable_embedding_logging: bool = Field(default=False, description="Log embedding operations")
    enable_response_logging: bool = Field(default=True, description="Log LLM responses")
    enable_performance_logging: bool = Field(default=True, description="Log performance metrics")
    save_failed_queries: bool = Field(default=True, description="Save failed queries for debugging")
    
    # Query Logging
    query_log_file: Optional[Path] = Field(default=Path("./storage/logs/queries.log"), description="Dedicated query log file")
    query_log_format: str = Field(default="json", description="Query log format")
    
    # Performance Logging
    track_response_times: bool = Field(default=True, description="Track response times")
    response_time_threshold_ms: int = Field(default=5000, description="Slow response threshold in ms")
    embedding_time_threshold_ms: int = Field(default=2000, description="Slow embedding threshold in ms")
    search_time_threshold_ms: int = Field(default=1000, description="Slow search threshold in ms")
    
    # Structured Logging
    include_request_id: bool = Field(default=True, description="Include request ID in logs")
    include_user_context: bool = Field(default=True, description="Include user context")
    serialize_json: bool = Field(default=True, description="Serialize JSON fields in logs")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure log directories exist
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if self.error_file_enabled:
            self.error_file_path.parent.mkdir(parents=True, exist_ok=True)
        if self.query_log_file:
            self.query_log_file.parent.mkdir(parents=True, exist_ok=True)
    
    @property
    def loguru_format_templates(self) -> dict:
        """Get Loguru format templates."""
        return {
            "text": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            "detailed": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <magenta>{extra[request_id]}</magenta> - <level>{message}</level>",
            "json": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message} | {extra}"
        }
    
    @property
    def console_format(self) -> str:
        """Get console log format."""
        if self.format == "json":
            return '{"time": "{time:YYYY-MM-DD HH:mm:ss.SSS}", "level": "{level}", "module": "{name}", "function": "{function}", "line": {line}, "message": "{message}", "extra": {extra}}'
        return self.loguru_format_templates[self.format]
    
    @property
    def file_format(self) -> str:
        """Get file log format."""
        if self.format == "json":
            return '{"time": "{time:YYYY-MM-DD HH:mm:ss.SSS}", "level": "{level}", "module": "{name}", "function": "{function}", "line": {line}, "message": "{message}", "extra": {extra}}'
        return self.loguru_format_templates.get(self.format, self.loguru_format_templates["text"])
    
    def get_loguru_config(self) -> list:
        """Get Loguru configuration as a list of handlers."""
        handlers = []
        
        # Console handler
        if self.console_enabled:
            handlers.append({
                "sink": "sys.stdout",
                "format": self.console_format,
                "level": self.level,
                "colorize": self.console_colorize,
                "serialize": self.format == "json"
            })
        
        # Main file handler
        if self.file_enabled:
            handlers.append({
                "sink": str(self.file_path),
                "format": self.file_format,
                "level": self.level,
                "rotation": self.rotation_size,
                "retention": self.retention_time,
                "compression": self.compression,
                "serialize": self.format == "json"
            })
        
        # Error file handler
        if self.error_file_enabled:
            handlers.append({
                "sink": str(self.error_file_path),
                "format": self.file_format,
                "level": "ERROR",
                "rotation": self.rotation_size,
                "retention": self.retention_time,
                "compression": self.compression,
                "serialize": self.format == "json"
            })
        
        # Query log handler
        if self.enable_query_logging and self.query_log_file:
            handlers.append({
                "sink": str(self.query_log_file),
                "format": '{"time": "{time:YYYY-MM-DD HH:mm:ss.SSS}", "query": "{extra[query]}", "user": "{extra[user]}", "response_time": "{extra[response_time]}", "results": "{extra[results]}"}',
                "level": "INFO",
                "rotation": self.rotation_size,
                "retention": self.retention_time,
                "compression": self.compression,
                "serialize": True,
                "filter": lambda record: "query" in record["extra"]
            })
        
        return handlers