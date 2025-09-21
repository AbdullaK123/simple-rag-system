from fastapi import Depends, APIRouter, Query
from app.services.documents import DocumentService
from app.dependencies.documents import preprocess_uploaded_file, get_document_service, assemble_search_request
from langchain_core.documents import Document
from app.schemas.document import AddDocumentsResult, SearchResponse, SearchRequest, DocumentOperationResult
from typing import List, Union


document_controller = APIRouter(
    prefix="/documents",
    tags=["documents", "retrieval"]
)


@document_controller.post('/', response_model=AddDocumentsResult)
async def add_document(
    service: DocumentService = Depends(get_document_service),
    chunks: List[Document] = Depends(preprocess_uploaded_file)
) -> AddDocumentsResult:
    return await service.add_documents(chunks)

@document_controller.delete('/', response_model=DocumentOperationResult)
async def deleted_document_by_source(
    source_file: str = Query(),
    service: DocumentService = Depends(get_document_service),
) -> DocumentOperationResult:
    return await service.delete_by_source(source_file)

@document_controller.get('/similarity-search', response_model=Union[SearchResponse, DocumentOperationResult])
async def similarity_search(
    request: SearchRequest = Depends(assemble_search_request),
    service: DocumentService = Depends(get_document_service)
) -> Union[SearchResponse, DocumentOperationResult]:
    return await service.similarity_search(request)