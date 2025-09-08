import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import List

from app.services.documents import DocumentService
from app.schemas.document import (
    DocumentMetadata, 
    AddDocumentResult, 
    AddDocumentsResult,
    DeleteDocumentResult,
    DocumentOperationResult,
    SearchRequest,
    SearchResponse,
    SearchResult,
    CollectionStats
)
from langchain_core.documents import Document


class TestDocumentService:
    """Test suite for DocumentService class."""

    @pytest.fixture
    def mock_embeddings(self):
        """Mock OpenAI embeddings."""
        with patch('app.services.documents.OpenAIEmbeddings') as mock:
            mock_instance = Mock()
            mock_instance.model = "text-embedding-ada-002"
            mock.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def mock_chroma(self):
        """Mock Chroma vector store."""
        with patch('app.services.documents.Chroma') as mock:
            mock_instance = Mock()
            mock_instance._collection.name = "test_collection"
            mock.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def document_service(self, mock_embeddings, mock_chroma):
        """Create DocumentService instance with mocked dependencies."""
        service = DocumentService(
            collection_name="test_collection",
            embedding_model="text-embedding-ada-002",
            persist_directory="/tmp/test_chroma"
        )
        return service

    @pytest.fixture
    def sample_metadata(self):
        """Sample document metadata for testing."""
        return DocumentMetadata(
            uuid="test-uuid-123",
            source_file="test_document.pdf",
            file_name="test_document.pdf",
            chunk_index=0,
            chunk_size=1000,
            added_at=datetime.now(),
            content_type="application/pdf"
        )

    @pytest.fixture
    def sample_document(self, sample_metadata):
        """Sample Langchain document for testing."""
        return Document(
            page_content="This is a test document content.",
            metadata=sample_metadata.model_dump()
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_add_document_success(self, document_service, sample_metadata):
        """Test successful document addition."""
        # Mock the async add_documents method
        document_service.store.aadd_documents = AsyncMock(return_value=["doc-id-123"])
        
        result = await document_service.add_document(
            content="Test content",
            metadata=sample_metadata
        )
        
        assert isinstance(result, AddDocumentResult)
        assert result.success is True
        assert result.uuid == "doc-id-123"
        assert "Successfully added document" in result.message
        
        # Verify the mock was called correctly
        document_service.store.aadd_documents.assert_called_once()
        call_args = document_service.store.aadd_documents.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0].page_content == "Test content"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_add_document_failure(self, document_service, sample_metadata):
        """Test document addition failure."""
        # Mock the async add_documents method to raise an exception
        document_service.store.aadd_documents = AsyncMock(side_effect=Exception("Connection error"))
        
        result = await document_service.add_document(
            content="Test content",
            metadata=sample_metadata
        )
        
        assert isinstance(result, AddDocumentResult)
        assert result.success is False
        assert result.uuid is None
        assert "Failed to add document to store" in result.message
        assert "Connection error" in result.message

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_add_documents_success(self, document_service, sample_document):
        """Test successful multiple documents addition."""
        documents = [sample_document, sample_document]
        document_service.store.aadd_documents = AsyncMock(return_value=["doc-1", "doc-2"])
        
        result = await document_service.add_documents(documents)
        
        assert isinstance(result, AddDocumentsResult)
        assert result.success is True
        assert result.added_count == 2
        assert result.uuids == ["doc-1", "doc-2"]
        assert "Successfully added documents" in result.message

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_add_documents_failure(self, document_service, sample_document):
        """Test multiple documents addition failure."""
        documents = [sample_document]
        document_service.store.aadd_documents = AsyncMock(side_effect=Exception("Storage error"))
        
        result = await document_service.add_documents(documents)
        
        assert isinstance(result, AddDocumentsResult)
        assert result.success is False
        assert "Failed to add documents to store" in result.message

    @pytest.mark.unit
    def test_update_document_success(self, document_service, sample_document):
        """Test successful document update."""
        document_service.store.update_document = Mock()
        
        result = document_service.update_document("doc-123", sample_document)
        
        assert isinstance(result, DocumentOperationResult)
        assert result.success is True
        assert "Successfully updated document" in result.message
        document_service.store.update_document.assert_called_once_with("doc-123", sample_document)

    @pytest.mark.unit
    def test_update_document_failure(self, document_service, sample_document):
        """Test document update failure."""
        document_service.store.update_document = Mock(side_effect=Exception("Update error"))
        
        result = document_service.update_document("doc-123", sample_document)
        
        assert isinstance(result, DocumentOperationResult)
        assert result.success is False
        assert "Failed to update document" in result.message

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_document_success(self, document_service):
        """Test successful document deletion."""
        document_service.store.adelete = AsyncMock()
        
        result = await document_service.delete_document("doc-123")
        
        assert isinstance(result, DocumentOperationResult)
        assert result.success is True
        assert "Successfully deleted document" in result.message
        document_service.store.adelete.assert_called_once_with(["doc-123"])

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_document_failure(self, document_service):
        """Test document deletion failure."""
        document_service.store.adelete = AsyncMock(side_effect=Exception("Delete error"))
        
        result = await document_service.delete_document("doc-123")
        
        assert isinstance(result, DocumentOperationResult)
        assert result.success is False
        assert "Failed to delete document" in result.message

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_documents_success(self, document_service):
        """Test successful multiple documents deletion."""
        document_ids = ["doc-1", "doc-2", "doc-3"]
        document_service.store.adelete = AsyncMock()
        
        result = await document_service.delete_documents(document_ids)
        
        assert isinstance(result, DeleteDocumentResult)
        assert result.success is True
        assert result.deleted_count == 3
        assert "Successfully deleted 3 documents" in result.message
        document_service.store.adelete.assert_called_once_with(document_ids)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_documents_failure(self, document_service):
        """Test multiple documents deletion failure."""
        document_ids = ["doc-1", "doc-2"]
        document_service.store.adelete = AsyncMock(side_effect=Exception("Delete error"))
        
        result = await document_service.delete_documents(document_ids)
        
        assert isinstance(result, DeleteDocumentResult)
        assert result.success is False
        assert "Failed to delete documents" in result.message

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_by_source_success(self, document_service):
        """Test successful deletion by source file."""
        # Mock the get method to return documents with the source file
        document_service.store.get = Mock(return_value={
            "ids": ["doc-1", "doc-2"],
            "metadatas": [
                {"source_file": "test.pdf"},
                {"source_file": "test.pdf"}
            ]
        })
        document_service.store.adelete = AsyncMock()
        
        result = await document_service.delete_by_source("test.pdf")
        
        assert isinstance(result, DeleteDocumentResult)
        assert result.success is True
        assert result.deleted_count == 2
        assert "test.pdf" in result.message

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_by_source_no_documents(self, document_service):
        """Test deletion by source file when no documents exist."""
        document_service.store.get = Mock(return_value={"ids": []})
        
        result = await document_service.delete_by_source("nonexistent.pdf")
        
        assert isinstance(result, DeleteDocumentResult)
        assert result.success is True
        assert result.deleted_count == 0

    @pytest.mark.unit
    def test_clear_collection_success(self, document_service):
        """Test successful collection clearing."""
        document_service.store.delete_collection = Mock()
        
        result = document_service.clear_collection()
        
        assert isinstance(result, DocumentOperationResult)
        assert result.success is True
        assert "Successfully deleted collection" in result.message
        document_service.store.delete_collection.assert_called_once()

    @pytest.mark.unit
    def test_clear_collection_failure(self, document_service):
        """Test collection clearing failure."""
        document_service.store.delete_collection = Mock(side_effect=Exception("Clear error"))
        
        result = document_service.clear_collection()
        
        assert isinstance(result, DocumentOperationResult)
        assert result.success is False
        assert "Failed to delete collection" in result.message

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_similarity_search_with_scores(self, document_service, sample_metadata):
        """Test similarity search with relevance scores."""
        mock_docs_with_scores = [
            (Document(page_content="Test content 1", metadata=sample_metadata.model_dump()), 0.9),
            (Document(page_content="Test content 2", metadata=sample_metadata.model_dump()), 0.8)
        ]
        document_service.store.asimilarity_search_with_relevance_scores = AsyncMock(
            return_value=mock_docs_with_scores
        )
        
        request = SearchRequest(
            query="test query",
            k=2,
            include_scores=True
        )
        
        result = await document_service.similarity_search(request)
        
        assert isinstance(result, SearchResponse)
        assert result.query == "test query"
        assert len(result.results) == 2
        assert result.results[0].relevance_score == 0.9
        assert result.results[1].relevance_score == 0.8
        assert result.total_found == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_similarity_search_without_scores(self, document_service, sample_metadata):
        """Test similarity search without relevance scores."""
        mock_docs = [
            Document(page_content="Test content 1", metadata=sample_metadata.model_dump()),
            Document(page_content="Test content 2", metadata=sample_metadata.model_dump())
        ]
        document_service.store.asimilarity_search = AsyncMock(return_value=mock_docs)
        
        request = SearchRequest(
            query="test query",
            k=2,
            include_scores=False
        )
        
        result = await document_service.similarity_search(request)
        
        assert isinstance(result, SearchResponse)
        assert result.query == "test query"
        assert len(result.results) == 2
        assert result.results[0].relevance_score is None
        assert result.total_found == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_similarity_search_failure(self, document_service):
        """Test similarity search failure."""
        document_service.store.asimilarity_search = AsyncMock(side_effect=Exception("Search error"))
        
        request = SearchRequest(query="test query", k=5)
        
        result = await document_service.similarity_search(request)
        
        assert isinstance(result, DocumentOperationResult)
        assert result.success is False
        assert "Failed to search collection" in result.message

    @pytest.mark.unit
    def test_get_document_count(self, document_service):
        """Test getting document count."""
        document_service.store.get = Mock(return_value={
            "ids": ["doc-1", "doc-2", "doc-3"],
            "metadatas": [{}, {}, {}]
        })
        
        count = document_service.get_document_count()
        
        assert count == 3
        document_service.store.get.assert_called_once_with(include=["metadatas"])

    @pytest.mark.unit
    def test_get_document_count_empty(self, document_service):
        """Test getting document count when collection is empty."""
        document_service.store.get = Mock(return_value={"ids": []})
        
        count = document_service.get_document_count()
        
        assert count == 0

    @pytest.mark.unit
    def test_list_sources(self, document_service):
        """Test listing unique source files."""
        document_service.store.get = Mock(return_value={
            "ids": ["doc-1", "doc-2", "doc-3"],
            "metadatas": [
                {"source_file": "file1.pdf"},
                {"source_file": "file2.pdf"},
                {"source_file": "file1.pdf"}  # Duplicate
            ]
        })
        
        sources = document_service.list_sources()
        
        assert len(sources) == 2
        assert "file1.pdf" in sources
        assert "file2.pdf" in sources

    @pytest.mark.unit
    def test_list_sources_empty(self, document_service):
        """Test listing sources when no documents exist."""
        document_service.store.get = Mock(return_value={"metadatas": []})
        
        sources = document_service.list_sources()
        
        assert sources == []

    @pytest.mark.unit
    def test_get_stats_success(self, document_service):
        """Test getting collection statistics."""
        # Mock the methods that get_stats depends on
        document_service.get_document_count = Mock(return_value=5)
        document_service.list_sources = Mock(return_value=["file1.pdf", "file2.pdf"])
        
        stats = document_service.get_stats()
        
        assert isinstance(stats, CollectionStats)
        assert stats.collection_name == "test_collection"
        assert stats.document_count == 5
        assert stats.sources == ["file1.pdf", "file2.pdf"]
        assert stats.distance_metric == "cosine"
        assert stats.embedding_model == "text-embedding-ada-002"
        assert stats.created_at is None

    @pytest.mark.unit
    def test_get_stats_failure(self, document_service):
        """Test getting statistics when an error occurs."""
        document_service.get_document_count = Mock(side_effect=Exception("Stats error"))
        
        stats = document_service.get_stats()
        
        assert isinstance(stats, CollectionStats)
        assert stats.collection_name == "test_collection"
        assert stats.document_count == 0
        assert stats.sources == []
        assert stats.distance_metric == "cosine"


class TestDocumentServiceIntegration:
    """Integration tests for DocumentService (require more setup)."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_full_document_lifecycle(self):
        """Test complete document lifecycle - add, search, update, delete."""
        # This would be an integration test that uses real Chroma instance
        # Would require proper setup and cleanup
        pytest.skip("Integration test - requires real Chroma setup")

    @pytest.mark.integration
    @pytest.mark.slow  
    def test_bulk_operations(self):
        """Test bulk document operations with real vector store."""
        pytest.skip("Integration test - requires real Chroma setup")
