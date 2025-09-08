from typing import Dict, Any, List, Tuple
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from app.schemas.document import *
import time

class DocumentService:

    def __init__(self, collection_name: str, embedding_model: str, persist_directory: str):
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.store = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_directory
        )

    async def add_document(self, content: str, metadata: DocumentMetadata) -> AddDocumentResult:
        try: 
            result =  await self.store.aadd_documents([Document(page_content=content, metadata=metadata.model_dump())])
            return AddDocumentResult(
                success=True,
                message="Successfully added document to store",
                uuid=result[0]
            )
        except Exception as e:
            return AddDocumentResult(
                success=False,
                message=f"Failed to add document to store: {str(e)}",
                uuid=None
            )

    async def add_documents(self, documents: List[Document]) -> AddDocumentsResult:
        try:
            result = await self.store.aadd_documents(documents)
            return AddDocumentsResult(
                success=True,
                message=f"Successfully added documents to store",
                added_count=len(result),
                uuids=result
            )
        except Exception as e:
            return AddDocumentsResult(
                success=False,
                message=f"Failed to add documents to store: {str(e)}",
                added_count=0,
                uuids=[]
            )
        
    def update_document(self, document_id: str, updated_document: Document) -> DocumentOperationResult:
        try:
            self.store.update_document(document_id, updated_document)
            return DocumentOperationResult(
                success=True,
                message="Successfully updated document"
            )
        except Exception as e:
            return DocumentOperationResult(
                success=False,
                message=f"Failed to update document: {str(e)}"
            )

    async def delete_document(self, document_id: str) -> DocumentOperationResult:
        try:
            await self.store.adelete([document_id])
            return DocumentOperationResult(
                success=True,
                message="Successfully deleted document"
            )
        except Exception as e:
            return DocumentOperationResult(
                success=False,
                message=f"Failed to delete document: {str(e)}"
            )
        
    async def delete_documents(self, document_ids: List[str]) -> DeleteDocumentResult:
        try:
            await self.store.adelete(document_ids)
            return DeleteDocumentResult(
                success=True,
                message=f"Successfully deleted {len(document_ids)} documents",
                deleted_count=len(document_ids)
            )
        except Exception as e:
            return DeleteDocumentResult(
                success=False,
                message=f"Failed to delete documents: {str(e)}"
            )

    async def delete_by_source(self, source_file: str) -> DeleteDocumentResult:
        try:
            collection_data = self.store.get(where={"source_file": source_file})
            document_ids = collection_data.get("ids", [])
            if document_ids:  # Only delete if there are documents to delete
                await self.delete_documents(document_ids)
            return DeleteDocumentResult(
                success=True,
                message=f"Successfully deleted {len(document_ids)} documents with source file: {source_file}",
                deleted_count=len(document_ids)
            )
        except Exception as e:
            return DeleteDocumentResult(
                success=False,
                message=f"Failed to delete documents with source file {source_file}: {str(e)}"
            )

    def clear_collection(self) -> DocumentOperationResult:
        try:
            self.store.delete_collection()
            return DocumentOperationResult(
                success=True,
                message=f"Successfully deleted collection"
            )
        except Exception as e:
            return DocumentOperationResult(
                success=False,
                message=f"Failed to delete collection: {str(e)}"
            )

    async def similarity_search(self, request: SearchRequest) -> SearchResponse | DocumentOperationResult:
        try:
            search_start = time.perf_counter()
            if request.include_scores:
                results = await self.store.asimilarity_search_with_relevance_scores(
                    query=request.query,
                    k=request.k,
                    filter=request.filters
                )
                return SearchResponse(
                    query=request.query,
                    results=[
                        SearchResult(
                            content=document.page_content,
                            metadata=DocumentMetadata(**document.metadata),
                            relevance_score=score
                        )
                        for document, score 
                        in results
                    ],
                    total_found=len(results),
                    search_time_ms=time.perf_counter()-search_start
                )
            else:
                docs = await self.store.asimilarity_search(
                    query=request.query,
                    k=request.k,
                    filter=request.filters
                )
                return SearchResponse(
                    query=request.query,
                    results=[
                        SearchResult(
                            content=document.page_content,
                            metadata=DocumentMetadata(**document.metadata),
                        )
                        for document
                        in docs
                    ],
                    total_found=len(docs),
                    search_time_ms=time.perf_counter() - search_start
                )
        except Exception as e:
            return DocumentOperationResult(
                success=False,
                message=f"Failed to search collection: {str(e)}"
            )

    def get_document_count(self) -> int:
        collection_data = self.store.get(include=["metadatas"])
        return len(collection_data["ids"]) if collection_data.get("ids") else 0

    def list_sources(self) -> List[str]:
        collection_data = self.store.get(include=["metadatas"])
        return list(set([
            metadata.get("source_file", "unknown")
            for metadata in collection_data.get("metadatas", [])
            if metadata.get("source_file")
        ]))

    def get_stats(self) -> CollectionStats:
        try:
            document_count = self.get_document_count()

            sources = self.list_sources()

            # Get collection info
            collection_name = self.store._collection.name
            
            # Get embedding model from the embeddings instance
            embedding_model = getattr(self.embeddings, 'model', 'unknown')
            
            # Chroma typically uses cosine distance as default
            distance_metric = "cosine"
            
            return CollectionStats(
                collection_name=collection_name,
                document_count=document_count,
                sources=sources,
                distance_metric=distance_metric,
                embedding_model=embedding_model,
                created_at=None  # Chroma doesn't store collection creation time by default
            )
        except Exception as e:
            # Return empty stats in case of error
            return CollectionStats(
                collection_name=getattr(self.store._collection, 'name', 'unknown'),
                document_count=0,
                sources=[],
                distance_metric="cosine",
                embedding_model=getattr(self.embeddings, 'model', 'unknown'),
                created_at=None
            )