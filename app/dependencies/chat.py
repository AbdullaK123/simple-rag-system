from app.dependencies.documents import get_document_service
from app.schemas.document import DocumentOperationResult, SearchRequest, SearchResponse
from app.services.documents import DocumentService
from app.utils.deduping import get_redundant_chunk_ids
from fastapi import Body, Depends, HTTPException, status
from langchain_core.prompts import ChatPromptTemplate
from itertools import groupby

RAG_PROMPT_TEMPLATE = """You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
Question: {question} 
Context: {context} 
Answer:
"""

RAG_PROMPT = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)


async def get_relevant_chunks(
    service: DocumentService = Depends(get_document_service),
    query: SearchRequest = Body(...)
) -> SearchResponse:
    result = await service.similarity_search(query)
    if isinstance(result, DocumentOperationResult):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chunk retrieval failed: {result.message}"
        )
    else:
        return result
    
async def dedupe_chunks(
    service: DocumentService = Depends(get_document_service),
    response: SearchResponse = Depends(get_relevant_chunks),
) -> SearchResponse:
    deduped_response = response.copy()
    redundant_ids = await get_redundant_chunk_ids(deduped_response, service)
    deduped_response.results = [
        result for result in deduped_response.results if result.doc_metadata.uuid not in redundant_ids
    ]
    deduped_response.total_found = len(deduped_response.results)
    return deduped_response

async def rerank_chunks(
    deduped_response: SearchResponse = Depends(dedupe_chunks)
) -> SearchResponse:
    reranked_response = deduped_response.copy()
    reranked_response.results = sorted(
        reranked_response.results,
        key=lambda result: (
            result.relevance_score if result.relevance_score is not None else 0
        ),
        reverse=True  
    )
    return reranked_response

async def assemble_context(
    reranked_response: SearchResponse = Depends(rerank_chunks)
) -> str:
    grouped_chunks = groupby(
        reranked_response.results,
        key = lambda result: result.doc_metadata.source_file
    )

    context_sections = []
    for source_file, chunks_group in grouped_chunks:
        chunks_list = list(chunks_group)
        
        header = f"=== {source_file} ==="
        source_content = [
            f"[Chunk {chunk.doc_metadata.chunk_index}]\n{chunk.content}" 
            for chunk in chunks_list
        ]
        
        source_section = f"{header}\n\n" + "\n\n".join(source_content)
        context_sections.append(source_section)
    
    context = "\n\n" + "="*50 + "\n\n".join(context_sections)
    
    return RAG_PROMPT.format(
        question=reranked_response.query, 
        context=context
    )
