from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class VectorSettings(BaseSettings):
    """Vector database configuration settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        env_file_encoding="utf-8"
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
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure chroma directory exists
        self.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate search weights sum to 1.0
        total_weight = self.semantic_search_weight + self.keyword_search_weight
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError("Semantic and keyword search weights must sum to 1.0")
    
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