"""Helper Function"""

import re
import uuid
from typing import List, Dict, Any
from datetime import datetime


def generate_thread_id() -> str:
    """Generate unique thread ID for conversations"""

    return f"thread_{uuid.uuid4().hex[:12]}"


def format_sources(documents: List[Dict[str, Any]]) -> str:
    """Format source documents for display"""

    if not documents:
        return "No sources avaiable"

    sources = []
    for idx, doc in enumerate(documents, 1):
        source = doc.get("metadata", {}).get("source", "Unknown")
        page = doc.get("metadata", {}).get("page", "")
        page_info = f" (Page{page})" if page else ""
        sources.append(f"{idx}. {source}{page_info}")

    return "\n".join(sources)


def calculate_confidence_score(results: List[Dict[str, Any]]) -> float:
    """Calculate confidence score from retrieval results"""

    if not results:
        return 0.0

    scores = [r.get("score", 0.0) for r in results]
    return sum(scores) / len(scores) if scores else 0.0


def truncate_text(text: str, max_length: int = 1000) -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def format_timestamp(dt: datetime) -> str:
    """Format datetime for display"""

    return dt.strftime("%Y-%m-%d %H:%M:%S")


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for storage"""
    filename = re.sub(r'[\\/*?"<>|]', "", filename)
    filename = filename.replace(" ", "_")
    return filename
