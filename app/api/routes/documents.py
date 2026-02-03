"""Document Routes"""

import os
import traceback
from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
    status,
    BackgroundTasks,
)
from sqlalchemy.orm import Session
from app.db.session import get_db, SessionLocal
from app.models.user import User
from app.models.document import Document
from app.services.document_service import (
    save_document,
    process_document,
    get_user_documents,
    get_document_by_id,
    delete_document,
    get_document_stats,
)
from app.api.deps import get_current_active_user
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


def process_document_task(document_id: int):
    """Background task entrypoint (SAFE)"""
    logger.info(
        "PROCESS START doc_id=%s pid=%s",
        document_id,
        os.getpid(),
    )

    db = SessionLocal()
    try:
        logger.info("Background task started for document %d", document_id)
        process_document(document_id, db)
        logger.info("Background task finished for document %d", document_id)
    except Exception:
        logger.error("Background task failed for document %d", document_id)
        logger.error(traceback.format_exc())
    finally:
        db.close()

    logger.info(
        "PROCESS END doc_id=%s pid=%s",
        document_id,
        os.getpid(),
    )


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Upload a document file and queue it for processing."""
    filename = file.filename.lower()
    allowed_extensions = [".pdf", ".doc", ".docx", ".txt", ".csv", ".xls", ".xlsx"]

    if not any(filename.endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format",
        )

    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    try:
        document = save_document(file, current_user, db)

        background_tasks.add_task(process_document_task, document.id)

        return {
            "success": True,
            "message": "Document uploaded and queued for processing",
            "data": {
                "document_id": document.id,
                "filename": document.filename,
                "status": "processing",
            },
        }

    except Exception as e:
        logger.error("Upload failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document",
        ) from e


@router.post("/{document_id}/reprocess")
async def reprocess_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Reprocess an existing document by re-queuing it for background processing."""
    document = get_document_by_id(document_id, current_user.id, db)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    document.processed_status = "pending"
    document.chunk_count = 0
    db.commit()

    background_tasks.add_task(process_document_task, document.id)

    return {
        "success": True,
        "message": "Document queued for reprocessing",
        "data": {
            "document_id": document.id,
            "filename": document.filename,
            "status": "processing",
        },
    }


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document_endpoint(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a document and all associated data."""
    success = delete_document(document_id, current_user.id, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    logger.info(
        "Document %d deleted by user %s",
        document_id,
        current_user.username,
    )

    return {
        "success": True,
        "message": "Document deleted successfully",
        "data": {"document_id": document_id},
    }


@router.get("/stats", status_code=status.HTTP_200_OK)
async def document_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return get_document_stats(current_user.id, db)


@router.get("/{document_id}", status_code=status.HTTP_200_OK)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    document = get_document_by_id(document_id, current_user.id, db)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": document.id,
        "filename": document.filename,
        "file_type": document.file_type,
        "file_size": document.file_size,
        "uploaded_at": (
            document.uploaded_at.isoformat() if document.uploaded_at else None
        ),
        "processed_status": document.processed_status,
        "chunk_count": document.chunk_count,
    }


@router.get("/", status_code=status.HTTP_200_OK)
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    documents = get_user_documents(current_user.id, db, skip, limit)

    return {
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "uploaded_at": (
                    doc.uploaded_at.isoformat() if doc.uploaded_at else None
                ),
                "processed_status": doc.processed_status,
                "chunk_count": doc.chunk_count,
            }
            for doc in documents
        ]
    }
