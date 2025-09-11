from sqlmodel import SQLModel
from fastapi import UploadFile


class UploadResult(SQLModel):
    filename: str
    source_file: str
    content_type: str
    content: str