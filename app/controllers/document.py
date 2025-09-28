from fastapi import Depends, APIRouter, Query

from app.dependencies.auth import get_current_user
from app.schemas.auth import UserResponse
from app.services.document import DocumentService
from app.dependencies.documents import preprocess_uploaded_file, get_document_service, assemble_search_request
from langchain_core.documents import Document
from app.schemas.document import AddDocumentsResult, SearchResponse, SearchRequest, DocumentOperationResult
from typing import List, Union
from app.config.logging import logger


document_controller = APIRouter(
    prefix="/documents",
    tags=["documents", "retrieval"]
)


@document_controller.post('/', response_model=AddDocumentsResult)
async def add_document(
    service: DocumentService = Depends(get_document_service),
    chunks: List[Document] = Depends(preprocess_uploaded_file)
) -> AddDocumentsResult:
    logger.debug("API add_document called", extra={"chunks": len(chunks) if chunks else 0})
    result = await service.add_documents(chunks)
    logger.info("API add_document completed", extra={"success": result.success, "added_count": getattr(result, 'added_count', None)})
    return result

@document_controller.delete('/', response_model=DocumentOperationResult)
async def deleted_document_by_source(
    source_file: str = Query(),
    current_user: UserResponse = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> DocumentOperationResult:
    logger.debug("API delete by source called", extra={"source_file": source_file})
    result = await service.delete_by_source(source_file, current_user.id)
    logger.info("API delete by source completed", extra={"success": result.success, "deleted_count": getattr(result, 'deleted_count', None)})
    return result

@document_controller.get('/similarity-search', response_model=Union[SearchResponse, DocumentOperationResult])
async def similarity_search(
    request: SearchRequest = Depends(assemble_search_request),
    service: DocumentService = Depends(get_document_service)
) -> Union[SearchResponse, DocumentOperationResult]:
    logger.debug("API similarity search called", extra={"k": request.k, "include_scores": request.include_scores})
    result = await service.similarity_search(request)
    if isinstance(result, SearchResponse):
        logger.info("API similarity search completed", extra={"total_found": result.total_found})
    else:
        logger.warning("API similarity search failed", extra={"success": result.success, "message": result.message})
    return result