from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class VectorSettings(BaseSettings):
    """Vector database configuration settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env/.vectors.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Database Configuration
    vector_db_type: Literal["chroma"] = Field(default="chroma", description="Vector database type")
    chroma_persist_dir: Path = Field(default=Path("./storage/chroma_db"), description="Chroma persistence directory")
    chroma_collection_name: str = Field(default="documents", description="Chroma collection name")
    chroma_distance_metric: Literal["cosine", "l2", "ip"] = Field(default="cosine", description="Distance metric for similarity")
    
    # Search Configuration
    default_search_results: int = Field(default=5, description="Default number of search results")
    max_search_results: int = Field(default=20, description="Maximum number of search results")
    min_similarity_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum similarity threshold")
    rerank_results: bool = Field(default=True, description="Enable result reranking")
    
    # Context Building
    max_context_length: int = Field(default=4000, description="Maximum context length in characters")
    context_overlap: int = Field(default=100, description="Overlap between context chunks")
    include_metadata: bool = Field(default=True, description="Include chunk metadata in results")
    include_source_info: bool = Field(default=True, description="Include source document information")
    
    # Query Processing
    query_expansion: bool = Field(default=False, description="Enable query expansion")
    query_rewriting: bool = Field(default=False, description="Enable query rewriting")
    semantic_search_weight: float = Field(default=0.7, ge=0.0, le=1.0, description="Weight for semantic search")
    keyword_search_weight: float = Field(default=0.3, ge=0.0, le=1.0, description="Weight for keyword search")
    
    @model_validator(mode='after')
    def validate_search_weights(self):
        """Validate that search weights are reasonable."""
        if self.semantic_search_weight + self.keyword_search_weight != 1.0:
            raise ValueError("Semantic search weight and key word search weight must sum to 1.0")
        return self
    
    def model_post_init(self, __context) -> None:
        """Post-initialization setup."""
        # Ensure chroma directory exists
        self.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def chroma_settings(self) -> dict:
        """Get Chroma-specific configuration."""
        return {
            "persist_directory": str(self.chroma_persist_dir),
            "collection_name": self.chroma_collection_name,
            "collection_metadata": {
                "hnsw:space": self.chroma_distance_metric
            }
        }
    
    @property
    def search_config(self) -> dict:
        """Get search configuration summary."""
        return {
            "default_results": self.default_search_results,
            "max_results": self.max_search_results,
            "similarity_threshold": self.min_similarity_threshold,
            "semantic_weight": self.semantic_search_weight,
            "keyword_weight": self.keyword_search_weight,
            "rerank_enabled": self.rerank_results
        }