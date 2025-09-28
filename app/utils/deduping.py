from app.schemas.document import SearchResponse
from app.services.document import DocumentService
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Set
import asyncio
from fastapi import HTTPException, status
from app.config.logging import logger


def _sync_get_redundant_chunk_ids(
    response: SearchResponse, 
    service: DocumentService,
    threshold: float = 0.8
) -> List[str]:
    redundant_ids: Set[str] = set()
    doc_ids = [result.doc_metadata.uuid for result in response.results]
    logger.debug("Computing similarity matrix for deduping", extra={"doc_count": len(doc_ids), "threshold": threshold})
    embeddings = np.array(service.get_embeddings(doc_ids))
    similarity_matrix = cosine_similarity(embeddings)
    
    for i in range(len(similarity_matrix)):
        for j in range(i + 1, len(similarity_matrix)):  # Skip diagonal and duplicates
            if similarity_matrix[i][j] > threshold:
                redundant_ids.add(doc_ids[j])  # Remove the later one, keep the first
    logger.info("Deduping completed", extra={"redundant_count": len(redundant_ids)})
    
    return list(redundant_ids)

async def get_redundant_chunk_ids(
    response: SearchResponse, 
    service: DocumentService,
    threshold: float = 0.8
) -> List[str]:
    if not response.results:
        logger.debug("No results to dedupe")
        return []
    
    try:
        result = await asyncio.to_thread(
            _sync_get_redundant_chunk_ids,
            response,
            service,
            threshold
        )
        return result
    except Exception as e:
        logger.exception("Failed during deduping")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to dedupe chunks: {e}"
        )