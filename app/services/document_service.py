"""Document Processing Service"""

import os
import shutil
import time
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import traceback

from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.models import Document, DocumentChunk, User
from app.config import settings
from app.rag.processing.docling import DocumentProcessor
from app.rag.processing.chunking import TextChunker
from app.rag.retrieval.vector_retriever import VectorRetriever
from app.utils.logger import get_logger
from app.utils.helpers import sanitize_filename

logger = get_logger(__name__)


def save_document(file: UploadFile, user: User, db: Session) -> Document:
    """Save an uploaded file to disk and create a document record."""
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = sanitize_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{user.id}_{timestamp}_{safe_filename}"

    file_path = upload_dir / unique_filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)

    document = Document(
        user_id=user.id,
        filename=file.filename,
        file_path=str(file_path),
        file_type=file.content_type,
        file_size=file_size,
        processed_status="pending",
        chunk_count=0,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    logger.info(
        "Document saved: %s (ID: %d, User: %s)",
        file.filename,
        document.id,
        user.username,
    )
    return document


def process_document(document_id: int, db: Session) -> Document:
    """Process a document: parse, chunk, embed, and store in vector database.

    Args:
        document_id: ID of the document to process.
        db: Database session.

    Returns:
        The updated Document record with status 'completed' or 'failed'.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise ValueError(f"Document {document_id} not found")

    try:
        # Update status to processing
        document.processed_status = "processing"
        db.commit()

        logger.info("=" * 70)
        logger.info("🔄 PROCESSING START")
        logger.info("   Document ID: %s", document.id)
        logger.info("   Filename: %s", document.filename)
        logger.info("   User ID: %s", document.user_id)
        logger.info("=" * 70)

        # STEP 1: Parse document
        logger.info("📄 STEP 1: Starting document parsing with PyPDF")
        processor = DocumentProcessor()
        extracted = processor.process_document(
            file_path=document.file_path,
            file_type=document.file_type,
        )
        logger.info("✓ STEP 1 COMPLETE: Document parsing finished")

        text = extracted.get("text", "")
        metadata = extracted.get("metadata", {})

        logger.info("   → Extracted text length: %d characters", len(text))
        logger.info("   → Pages: %d", metadata.get("pages", 0))
        logger.info("   → Metadata keys: %s", list(metadata.keys()))

        if not text.strip():
            raise RuntimeError("No text extracted from document")

        # STEP 2: Chunk text
        logger.info("✂️  STEP 2: Starting text chunking")
        chunker = TextChunker()

        if "page_texts" in metadata and metadata["page_texts"]:
            logger.info("   → Using page-based chunking")
            chunks = chunker.chunk_text_by_pages(
                page_texts=metadata["page_texts"],
                base_metadata={"document_id": document.id},
            )
        else:
            logger.info("   → Using standard chunking")
            chunks = chunker.chunk_text(
                text=text,
                metadata={"document_id": document.id},
            )

        logger.info("✓ STEP 2 COMPLETE: Chunking finished")
        logger.info("   → Total chunks created: %d", len(chunks))

        if not chunks:
            raise RuntimeError("Chunking produced zero chunks")

        # STEP 3: Insert chunks to database
        logger.info("💾 STEP 3: Inserting %d chunks into database", len(chunks))
        for i, chunk in enumerate(chunks, 1):
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=chunk["chunk_index"],
                    content=chunk["content"],
                    chunk_metadata=chunk["metadata"],
                )
            )
            if i % 10 == 0 or i == len(chunks):
                logger.info("   → Inserted %d/%d chunks", i, len(chunks))

        logger.info("   → Committing chunks to database...")
        db.commit()
        logger.info("✓ STEP 3 COMPLETE: All chunks saved to database")

        # STEP 4: Generate embeddings and store in ChromaDB
        logger.info("🧮 STEP 4: Starting embedding generation + ChromaDB storage")
        if len(chunks) > 50:
            logger.warning(
                "   ⚠️  Large document: %d chunks - this may take several minutes",
                len(chunks),
            )
        else:
            logger.info("   → Processing %d chunks...", len(chunks))

        start_time = time.time()

        vector_retriever = VectorRetriever()
        chroma_ids = vector_retriever.add_documents(
            chunks=chunks,
            document_id=document.id,
            user_id=document.user_id,
        )

        elapsed = time.time() - start_time
        logger.info("✓ STEP 4 COMPLETE: Embeddings generated and stored")
        logger.info(
            "   → Generated %d embeddings in %.1f seconds", len(chroma_ids), elapsed
        )

        # STEP 5: Update chunks with ChromaDB IDs
        logger.info("🔗 STEP 5: Linking chunks with ChromaDB IDs")
        db_chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document.id)
            .order_by(DocumentChunk.chunk_index)
            .all()
        )

        for db_chunk, chroma_id in zip(db_chunks, chroma_ids):
            db_chunk.chroma_id = chroma_id

        # Final update
        document.processed_status = "completed"
        document.chunk_count = len(chunks)
        db.commit()
        db.refresh(document)

        logger.info("✓ STEP 5 COMPLETE: Chunks linked with ChromaDB")
        logger.info("=" * 70)
        logger.info("✅ PROCESSING COMPLETE!")
        logger.info("   Status: %s", document.processed_status)
        logger.info("   Total chunks: %d", document.chunk_count)
        logger.info("   Document ready for querying")
        logger.info("=" * 70)

        return document

    except Exception as e:
        logger.error("=" * 70)
        logger.error("❌ PROCESSING FAILED!")
        logger.error("   Document ID: %s", document_id)
        logger.error("   Error: %s", str(e))
        logger.error("=" * 70)
        logger.error("Full traceback:\n%s", traceback.format_exc())

        # Update status to failed
        try:
            document.processed_status = "failed"
            db.commit()
        except Exception as commit_error:
            logger.error("Failed to update document status: %s", commit_error)

        raise


def get_user_documents(
    user_id: int,
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> List[Document]:
    """Retrieve documents uploaded by a specific user.

    Args:
        user_id: ID of the user whose documents to retrieve.
        db: Database session.
        skip: Number of documents to skip for pagination.
        limit: Maximum number of documents to return.

    Returns:
        List of Document records ordered by upload date (newest first).
    """
    documents = (
        db.query(Document)
        .filter(Document.user_id == user_id)
        .order_by(Document.uploaded_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    logger.info("Retrieved %d documents for user %d", len(documents), user_id)
    return documents


def get_document_by_id(
    document_id: int,
    user_id: int,
    db: Session,
) -> Optional[Document]:
    """Retrieve a specific document by ID, ensuring it belongs to the user.

    Args:
        document_id: ID of the document to retrieve.
        user_id: ID of the user who owns the document.
        db: Database session.

    Returns:
        The Document record if found and owned by the user, else None.
    """
    return (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == user_id)
        .first()
    )


def delete_document(
    document_id: int,
    user_id: int,
    db: Session,
) -> bool:
    """Delete a document and its associated data.

    Removes the document from the database, deletes vector embeddings from
    ChromaDB, and removes the physical file from storage.

    Args:
        document_id: ID of the document to delete.
        user_id: ID of the user who owns the document.
        db: Database session.

    Returns:
        True if document was deleted, False if document was not found.
    """
    document = get_document_by_id(document_id, user_id, db)
    if not document:
        logger.warning("Document %d not found for user %d", document_id, user_id)
        return False

    try:
        # Delete from ChromaDB
        logger.info("Deleting ChromaDB chunks for document %d", document_id)
        vector_retriever = VectorRetriever()
        vector_retriever.delete_document_chunks(document_id, user_id)
    except Exception as e:
        logger.error("Failed to delete ChromaDB chunks: %s", e)

    # Delete physical file
    if os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
            logger.info("Deleted file: %s", document.file_path)
        except OSError as e:
            logger.warning("Failed to delete file %s: %s", document.file_path, e)

    # Delete from database
    db.delete(document)
    db.commit()

    logger.info("Document deleted: %s (ID: %d)", document.filename, document_id)
    return True


def get_document_stats(user_id: int, db: Session) -> dict:
    """Calculate document processing statistics for a specific user.

    Args:
        user_id: ID of the user to get stats for.
        db: Database session.

    Returns:
        A dictionary containing counts for total, completed, processing,
        and failed documents, plus total chunks across all documents.
    """
    total_documents = db.query(Document).filter(Document.user_id == user_id).count()

    completed = (
        db.query(Document)
        .filter(
            Document.user_id == user_id,
            Document.processed_status == "completed",
        )
        .count()
    )

    processing = (
        db.query(Document)
        .filter(
            Document.user_id == user_id,
            Document.processed_status == "processing",
        )
        .count()
    )

    failed = (
        db.query(Document)
        .filter(
            Document.user_id == user_id,
            Document.processed_status == "failed",
        )
        .count()
    )

    total_chunks = (
        db.query(DocumentChunk)
        .join(Document)
        .filter(Document.user_id == user_id)
        .count()
    )

    return {
        "total_documents": total_documents,
        "completed": completed,
        "processing": processing,
        "failed": failed,
        "total_chunks": total_chunks,
    }
