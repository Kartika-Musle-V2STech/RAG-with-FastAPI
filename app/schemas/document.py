"""
Document Schemas
Pydantic models for document-related requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DocumentUpload(BaseModel):
    """Schema for document upload (metadata only, file handled separately)"""
    pass


class DocumentResponse(BaseModel):
    """Schema for document information response"""
    id: int
    filename: str
    file_type: Optional[str]
    file_size: Optional[int]
    processed_status: str
    chunk_count: int
    uploaded_at: datetime
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [{
                "id": 1,
                "filename": "research_paper.pdf",
                "file_type": "application/pdf",
                "file_size": 2048576,
                "processed_status": "completed",
                "chunk_count": 45,
                "uploaded_at": "2024-01-24T10:30:00"
            }]
        }
    }


class DocumentList(BaseModel):
    """Schema for list of documents"""
    documents: List[DocumentResponse]
    total: int


class DocumentStats(BaseModel):
    """Schema for document statistics"""
    total_documents: int
    total_chunks: int
    by_status: dict
    by_type: dict