from typing import Dict, List
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from app.schemas.document import *
import time
from app.config.logging import logger

class DocumentService:

    def __init__(self, collection_name: str, embedding_model: str, persist_directory: str):
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.store = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_directory
        )
        logger.info("Initialized DocumentService", extra={"collection_name": collection_name, "embedding_model": embedding_model, "persist_directory": persist_directory})

    def get_embeddings(self, ids: List[str]) -> List[List[float]]:
        logger.debug("Fetching embeddings", extra={"count": len(ids)})
        result = self.store._collection.get(ids=ids, include=['embeddings'])
        embeddings = result['embeddings']
        logger.debug("Fetched embeddings", extra={"returned": len(embeddings) if embeddings else 0})
        return embeddings

    async def add_document(self, content: str, metadata: DocumentMetadata) -> AddDocumentResult:
        logger.debug("Adding single document", extra={"source_file": metadata.source_file, "chunk_index": metadata.chunk_index})
        try: 
            result =  await self.store.aadd_documents([Document(page_content=content, metadata=metadata.model_dump())])
            logger.info("Added document", extra={"uuid": result[0], "source_file": metadata.source_file, "chunk_index": metadata.chunk_index})
            return AddDocumentResult(
                success=True,
                message="Successfully added document to store",
                uuid=result[0]
            )
        except Exception as e:
            logger.exception("Failed to add document", extra={"source_file": metadata.source_file, "chunk_index": metadata.chunk_index})
            return AddDocumentResult(
                success=False,
                message=f"Failed to add document to store: {str(e)}",
                uuid=None
            )

    async def add_documents(self, documents: List[Document]) -> AddDocumentsResult:
        if not documents:
            logger.warning("No documents to add")
        logger.debug("Adding documents", extra={"count": len(documents) if documents else 0})
        try:
            start = time.perf_counter()
            result = await self.store.aadd_documents(documents)
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info("Added documents", extra={"added_count": len(result), "duration_ms": round(duration_ms, 2)})
            return AddDocumentsResult(
                success=True,
                message=f"Successfully added documents to store",
                added_count=len(result),
                uuids=result
            )
        except Exception as e:
            logger.exception("Failed to add documents", extra={"count": len(documents) if documents else 0})
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
        logger.debug("Deleting document", extra={"document_id": document_id})
        try:
            await self.store.adelete([document_id])
            logger.info("Deleted document", extra={"document_id": document_id})
            return DocumentOperationResult(
                success=True,
                message="Successfully deleted document"
            )
        except Exception as e:
            logger.exception("Failed to delete document", extra={"document_id": document_id})
            return DocumentOperationResult(
                success=False,
                message=f"Failed to delete document: {str(e)}"
            )
        
    async def delete_documents(self, document_ids: List[str]) -> DeleteDocumentResult:
        logger.debug("Deleting documents", extra={"count": len(document_ids)})
        try:
            await self.store.adelete(document_ids)
            logger.info("Deleted documents", extra={"deleted_count": len(document_ids)})
            return DeleteDocumentResult(
                success=True,
                message=f"Successfully deleted {len(document_ids)} documents",
                deleted_count=len(document_ids)
            )
        except Exception as e:
            logger.exception("Failed to delete documents", extra={"count": len(document_ids)})
            return DeleteDocumentResult(
                success=False,
                message=f"Failed to delete documents: {str(e)}",
                deleted_count=0
            )

    async def delete_by_source(self, source_file: str, owner_id: str) -> DeleteDocumentResult:
        logger.debug("Deleting by source", extra={"source_file": source_file})
        try:
            collection_data = self.store.get(where={"source_file": source_file, "owner_id": owner_id})
            document_ids = collection_data.get("ids", [])
            logger.debug("Found documents to delete", extra={"count": len(document_ids)})
            if document_ids:  # Only delete if there are documents to delete
                await self.delete_documents(document_ids)
            logger.info("Deleted documents by source", extra={"source_file": source_file, "deleted_count": len(document_ids)})
            return DeleteDocumentResult(
                success=True,
                message=f"Successfully deleted {len(document_ids)} documents with source file: {source_file}",
                deleted_count=len(document_ids)
            )
        except Exception as e:
            logger.exception("Failed to delete by source", extra={"source_file": source_file})
            return DeleteDocumentResult(
                success=False,
                message=f"Failed to delete documents with source file {source_file}: {str(e)}",
                deleted_count=0
            )

    def clear_collection(self) -> DocumentOperationResult:
        logger.warning("Clearing entire collection")
        try:
            self.store.delete_collection()
            logger.info("Collection cleared")
            return DocumentOperationResult(
                success=True,
                message=f"Successfully deleted collection"
            )
        except Exception as e:
            logger.exception("Failed to clear collection")
            return DocumentOperationResult(
                success=False,
                message=f"Failed to delete collection: {str(e)}"
            )

    async def similarity_search(self, request: SearchRequest) -> SearchResponse | DocumentOperationResult:
        try:
            logger.debug("Starting similarity search", extra={"k": request.k, "include_scores": request.include_scores, "has_filters": bool(request.filters)})
            search_start = time.perf_counter()
            if request.include_scores:
                results = await self.store.asimilarity_search_with_relevance_scores(
                    query=request.query,
                    k=request.k,
                    filter=request.filters
                )
                duration_ms = (time.perf_counter() - search_start) * 1000
                logger.info("Similarity search completed", extra={"found": len(results), "duration_ms": round(duration_ms, 2)})
                return SearchResponse(
                    query=request.query,
                    results=[
                        SearchResult(
                            content=document.page_content,
                            doc_metadata=DocumentMetadata(
                                uuid=document.metadata.get('uuid', ''),
                                source_file=document.metadata.get('source_file'),
                                filename=document.metadata.get('filename'),
                                chunk_index=document.metadata.get('chunk_index'),
                                chunk_size=document.metadata.get('chunk_size'),
                                added_at=document.metadata.get('added_at'),
                                content_type=document.metadata.get('content_type')
                            ),
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
                duration_ms = (time.perf_counter() - search_start) * 1000
                logger.info("Similarity search completed", extra={"found": len(docs), "duration_ms": round(duration_ms, 2)})
                return SearchResponse(
                    query=request.query,
                    results=[
                        SearchResult(
                            content=document.page_content,
                            doc_metadata=DocumentMetadata(
                                uuid=document.metadata.get('uuid', ''),
                                source_file=document.metadata.get('source_file'),
                                filename=document.metadata.get('filename'),
                                chunk_index=document.metadata.get('chunk_index'),
                                chunk_size=document.metadata.get('chunk_size'),
                                added_at=document.metadata.get('added_at'),
                                content_type=document.metadata.get('content_type')
                            ),
                        )
                        for document
                        in docs
                    ],
                    total_found=len(docs),
                    search_time_ms=time.perf_counter() - search_start
                )
        except Exception as e:
            logger.exception("Similarity search failed")
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
            logger.exception("Failed to get collection stats")
            # Return empty stats in case of error
            return CollectionStats(
                collection_name=getattr(self.store._collection, 'name', 'unknown'),
                document_count=0,
                sources=[],
                distance_metric="cosine",
                embedding_model=getattr(self.embeddings, 'model', 'unknown'),
                created_at=None
            )