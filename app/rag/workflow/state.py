"""Langgraph State"""

from typing import List, Dict, Any, Optional, TypedDict
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RAGState(TypedDict):
    """RAG State"""

    query: str
    user_id: int
    thread_id: Optional[str]

    bm25_results: Optional[List[Dict[str, Any]]]
    vector_results: Optional[List[Dict[str, Any]]]
    hybrid_results: Optional[List[Dict[str, Any]]]
    reranked_results: Optional[List[Dict[str, Any]]]

    context_documents: Optional[List[Dict[str, Any]]]
    answer: Optional[str]

    tool_needed: Optional[bool]
    tool_result: Optional[str]

    metadata: Optional[Dict[str, Any]]
    error: Optional[str]


def create_initial_state(
    query: str, user_id: int, thread_id: Optional[str] = None
) -> RAGState:
    """Create initial state"""
    return RAGState(
        query=query,
        user_id=user_id,
        thread_id=thread_id,
        bm25_results=None,
        vector_results=None,
        hybrid_results=None,
        reranked_results=None,
        context_documents=None,
        answer=None,
        tool_needed=None,
        tool_result=None,
        metadata={"steps": [], "retrieval_time_ms": 0, "generation_time_ms": 0},
        error=None,
    )
