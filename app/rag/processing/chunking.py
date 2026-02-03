"""Text Chunking"""

from typing import List, Dict, Any
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TextChunker:
    """Split text into chunks with overlap"""

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ):
        """Initialize text chunker"""
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    def chunk_text(
        self, text: str, metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Split text into chunks with overlap"""
        if not text or not text.strip():
            logger.warning("Attempted to chunk empty text")
            return []

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size

            # If not at the end, try to break at a sentence or word boundary
            if end < len(text):
                # Look for sentence boundary (period, question mark, exclamation)
                for boundary in [". ", "? ", "! ", "\n\n", "\n"]:
                    boundary_pos = text.rfind(boundary, start, end)
                    if boundary_pos != -1:
                        end = boundary_pos + len(boundary)
                        break
                else:
                    # If no sentence boundary, look for word boundary
                    space_pos = text.rfind(" ", start, end)
                    if space_pos != -1:
                        end = space_pos + 1

            # Ensure end is at least past start
            if end <= start:
                end = min(start + self.chunk_size, len(text))

            # Extract chunk
            chunk_text = text[start:end].strip()

            chunk_metadata = (metadata or {}).copy()
            chunk_metadata.update(
                {"chunk_index": chunk_index, "start_char": start, "end_char": end}
            )

            chunks.append(
                {
                    "content": chunk_text,
                    "metadata": chunk_metadata,
                    "chunk_index": chunk_index,
                }
            )

            chunk_index += 1

            # Calculate next start position (with overlap)
            prev_start = start
            start = end - self.chunk_overlap

            # Ensure we always make forward progress (at least 1 character)
            if start <= prev_start:
                start = prev_start + max(1, self.chunk_size - self.chunk_overlap)

        logger.info(
            "Created %d chunks from text (size=%s, overlap=%s)",
            len(chunks),
            self.chunk_size,
            self.chunk_overlap,
        )
        return chunks

    def chunk_text_by_pages(
        self, page_texts: List[Dict[str, Any]], base_metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Chunk text while preserving page information"""
        all_chunks = []
        global_chunk_index = 0  # Track globally unique index

        for page_info in page_texts:
            page_num = page_info.get("page")
            page_text = page_info.get("text", "")

            if not page_text.strip():
                continue

            # Create metadata for this page
            page_metadata = base_metadata.copy() if base_metadata else {}
            page_metadata["page"] = page_num

            page_chunks = self.chunk_text(page_text, page_metadata)

            # Reassign global chunk indices
            for chunk in page_chunks:
                chunk["chunk_index"] = global_chunk_index
                chunk["metadata"]["chunk_index"] = global_chunk_index
                global_chunk_index += 1

            all_chunks.extend(page_chunks)

        logger.info("Created %d chunks from %d pages", len(all_chunks), len(page_texts))
        return all_chunks
