from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DocumentSettings(BaseSettings):
    """Document processing and file upload settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env/.storage.env",
        env_prefix="",
        case_sensitive=False,
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # File Upload Settings
    max_file_size_mb: int = Field(default=50, description="Maximum file size in MB")
    allowed_file_types: List[str] = Field(
        default=[".pdf", ".txt", ".docx", ".md"],
        description="Allowed file extensions"
    )
    upload_dir: str = Field(default=str(Path("./storage/uploads")), description="Upload directory path")
    max_files_per_upload: int = Field(default=10, description="Maximum files per upload request")
    
    # Text Chunking Settings
    chunk_size: int = Field(default=1000, description="Default chunk size in characters")
    chunk_overlap: int = Field(default=200, description="Overlap between chunks in characters")
    min_chunk_size: int = Field(default=100, description="Minimum allowed chunk size")
    max_chunk_size: int = Field(default=2000, description="Maximum allowed chunk size")
    
    # Text Processing Settings
    remove_headers_footers: bool = Field(default=True, description="Remove headers and footers from documents")
    normalize_whitespace: bool = Field(default=True, description="Normalize whitespace in text")
    remove_urls: bool = Field(default=False, description="Remove URLs from text")
    remove_emails: bool = Field(default=False, description="Remove email addresses from text")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure upload directory exists
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
    
    @property
    def allowed_extensions_set(self) -> set:
        """Get allowed file extensions as a set for faster lookup."""
        return set(ext.lower() for ext in self.allowed_file_types)
    
    @property
    def max_file_size_bytes(self) -> int:
        """Get maximum file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024