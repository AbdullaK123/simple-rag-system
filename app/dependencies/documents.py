from fastapi import UploadFile, File, Depends, HTTPException, status
from app.dependencies.config import get_settings
from app.config import Settings
from app.schemas.document import DocumentMetadata
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
from typing import List
from app.schemas.upload import UploadResult
import uuid
from datetime import datetime

async def validate_file(
    settings: Settings = Depends(get_settings),
    file: UploadFile = File(...)
) -> UploadResult:
    
    # check file extension 
    if not file.filename or not file.filename.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file selected"
        )
    
    file_ext = Path(file.filename).suffix.lower()
    if not file_ext or file_ext not in settings.documents.allowed_extensions_set:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or missing file extension. Allowed: {', '.join(settings.documents.allowed_file_types)}"
        )
    
    content = await file.read()
    await file.seek(0)

    # check file size
    if len(content) > settings.documents.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upload is too big. Max is {settings.documents.max_file_size_mb} MB."
        )

    # make file name uuid to ensure uploads are unique
    stored_filename = f"{uuid.uuid4()}{file_ext}"
    try: 
        with open(settings.documents.upload_dir / stored_filename, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {e}"
        )

    # Attempt to decode content as UTF-8 for text processing
    try:
        decoded_content = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be valid UTF-8 text content"
        )

    return UploadResult(
        filename=stored_filename,
        source_file=file.filename,
        content_type=file.content_type or "text/plain",
        content=decoded_content
    )

async def preprocess_uploaded_file(
    settings: Settings = Depends(get_settings),
    upload: UploadResult = Depends(validate_file)
) -> List[Document]:
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.documents.chunk_size,
        chunk_overlap=settings.documents.chunk_overlap,
        length_function=len
    )

    chunks = splitter.split_text(upload.content)

    return [
        Document(
            page_content=chunk,
            metadata=DocumentMetadata(
                uuid=str(uuid.uuid4()),
                source_file=upload.source_file,
                filename=upload.filename,
                chunk_size=len(chunk),
                added_at=datetime.utcnow(),
                content_type=upload.content_type,
                chunk_index=i,
            ).model_dump()
        )
        for i, chunk 
        in enumerate(chunks)
    ]

