from sqlmodel import SQLModel, Field
from typing import Optional, List
from datetime import datetime

class DocumentOperationResult(SQLModel):
    success: bool 
    message: str

class AddDocumentResult(DocumentOperationResult):
    uuid: Optional[str]

class AddDocumentsResult(DocumentOperationResult):
    added_count: int = 0
    uuids: List[str] = Field(default_factory=list)

class DeleteDocumentResult(DocumentOperationResult):
    deleted_count: int = 0

class DocumentMetadata(SQLModel):
    uuid: str
    source_file: Optional[str] = None
    filename: Optional[str] = None
    chunk_index: Optional[int] = None
    chunk_size: Optional[int] = None 
    added_at: Optional[datetime] = None 
    content_type: Optional[str] = None 

class DocumentChunk(SQLModel):
    content: str
    doc_metadata: DocumentMetadata

class SearchResult(SQLModel):
    content: str 
    doc_metadata: DocumentMetadata
    relevance_score: Optional[float] = None

class CollectionStats(SQLModel):
    collection_name: str
    document_count: int
    sources: List[str]
    distance_metric: str
    embedding_model: str
    created_at: Optional[datetime] = None


class SearchRequest(SQLModel):
    query: str
    k: int = Field(default=5, ge=1, le=50)
    filters: Optional[dict] = None
    include_scores: bool = False


class SearchResponse(SQLModel):
    query: str
    results: List[SearchResult]
    total_found: int
    search_time_ms: Optional[float] = None


