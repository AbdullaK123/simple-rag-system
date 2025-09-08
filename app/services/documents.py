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
                message=f"Failed to add document to store: {str(e)}"
            )

    async def add_documents(self, documents: List[Document]) -> AddDocumentsResult:
        try:
            result = self.store.aadd_documents(documents)
            return AddDocumentsResult(
                success=True,
                message=f"Successfully added documents to store",
                added_count=len(result),
                uuids=result
            )
        except Exception as e:
            return AddDocumentResult(
                success=False,
                message=f"Failed to add documents to store: {str(e)}"
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
        
    async def delete_documents(self, document_ids: List[str]):
        try:
            await self.store.adelete(document_ids)
            return DeleteDocumentResult(
                success=True,
                message=f"Successfully deleted {len(document_ids)} documents",
                deleted_count=len(document_ids)
            )
        except Exception as e:
            DeleteDocumentResult(
                success=False,
                message=f"Failed to delete documents: {str(e)}"
            )

    async def delete_by_source(self, source_file: str) -> DeleteDocumentResult:
        try:
            results = await self.store.asearch(filter={"source_file": source_file})
            await self.delete_documents([document.id for document in results])
            return DeleteDocumentResult(
                success=True,
                message=f"Successfully deleted {len(results)} documents with source file: {source_file}",
                deleted_count=len(results)
            )
        except Exception as e:
            DeleteDocumentResult(
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

    async def similarity_search(self, request: SearchRequest) -> SearchResponse:
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
                            metadata=document.metadata,
                            relevance_score=score
                        )
                        for document, score 
                        in results
                    ],
                    total_found=len(results),
                    search_time_ms=time.perf_counter()-search_start
                )
            else:
                results = await self.store.asimilarity_search(
                    query=request.query,
                    k=request.k,
                    filter=request.filters
                )
                return SearchResponse(
                    query=request.query,
                    results=[
                        SearchResult(
                            content=document.page_content,
                            metadata=document.metadata,
                        )
                        for document 
                        in results
                    ],
                    total_found=len(results),
                    search_time_ms=time.perf_counter() - search_start
                )
        except Exception as e:
            return DocumentOperationResult(
                success=False,
                message=f"Failed to search collection: {str(e)}"
            )

    def get_document_count(self) -> int:
        return len(self.store.get())

    def list_sources(self) -> List[str]:
        return [
            metadata.get("file_source")
            for metadata
            in self.store.get(include=["metadatas"])
        ]

    def get_stats(self) -> CollectionStats:
        pass