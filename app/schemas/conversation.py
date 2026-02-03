"""
Conversation Schemas
Pydantic models for chat and conversation-related requests and responses
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Schema for chat query request"""

    query: str = Field(
        ..., min_length=1, max_length=2000, description="User question or query"
    )
    thread_id: Optional[str] = Field(
        None, description="Optional thread ID for continuing conversation"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "What are the main findings in the uploaded research paper?",
                    "thread_id": "thread_abc123def456",
                }
            ]
        }
    }


class SourceDocument(BaseModel):
    """Schema for source document reference"""

    document_id: int
    filename: str
    chunk_index: int
    content: str
    relevance_score: float
    page: Optional[int] = None


class ChatResponse(BaseModel):
    """Schema for chat response"""

    thread_id: str
    query: str
    answer: str
    sources: List[SourceDocument]
    metadata: Dict[str, Any]  # confidence, tokens, retrieval_time, etc.
    created_at: datetime

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "thread_id": "thread_abc123def456",
                    "query": "What are the main findings?",
                    "answer": "Based on your documents, the main findings are...",
                    "sources": [
                        {
                            "document_id": 1,
                            "filename": "research_paper.pdf",
                            "chunk_index": 5,
                            "content": "The study found that...",
                            "relevance_score": 0.92,
                            "page": 3,
                        }
                    ],
                    "metadata": {
                        "confidence": 0.87,
                        "tokens_used": 456,
                        "retrieval_time_ms": 234,
                    },
                    "created_at": "2024-01-24T10:35:00",
                }
            ]
        }
    }


class MessageResponse(BaseModel):
    """Schema for individual message"""

    id: int
    role: str  # 'user' or 'assistant'
    content: str
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationHistory(BaseModel):
    """Schema for conversation history"""

    thread_id: str
    title: Optional[str]
    messages: List[MessageResponse]
    created_at: datetime
    updated_at: datetime
    message_count: int


class ThreadSummary(BaseModel):
    """Schema for thread summary"""

    thread_id: str
    title: Optional[str]
    message_count: int
    last_message_at: datetime
    created_at: datetime


class ThreadList(BaseModel):
    """Schema for list of threads"""

    threads: List[ThreadSummary]
    total: int
