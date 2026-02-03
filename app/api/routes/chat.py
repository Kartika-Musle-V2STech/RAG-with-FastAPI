"""Chat routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User, Conversation
from app.services.chat_service import (
    process_chat_query,
    get_conversation_history,
    get_user_threads,
    delete_conversation,
)
from app.api.deps import get_current_active_user
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/")
async def chat(
    query: str,
    thread_id: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Ask a question based on your uploaded documents"""
    try:
        result = await process_chat_query(
            query=query, user=current_user, thread_id=thread_id, db=db
        )

        # return plan dict instead of pydantic model
        return {
            "thread_id": result["thread_id"],
            "query": result["query"],
            "answer": result["answer"],
        }
    except Exception as e:
        logger.error("Error processing chat request: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat required",
        ) from e


@router.get("/history/{thread_id}")
async def get_history(
    thread_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get full conversation history for a specific thread"""
    conversation = get_conversation_history(thread_id, current_user.id, db)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )

    # manually format messages as plain dicts
    messages = [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
            "metadata": msg.msg_metadata or {},
        }
        for msg in conversation["messages"]
    ]

    return {
        "thread_id": conversation["thread_id"],
        "title": conversation["title"],
        "created_at": (
            conversation["created_at"].isoformat()
            if conversation["created_at"]
            else None
        ),
        "updated_at": (
            conversation["updated_at"].isoformat()
            if conversation["updated_at"]
            else None
        ),
        "messages": messages,
        "message_count": conversation["message_count"],
    }


@router.get("/threads")
async def list_threads(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List summary of all conversation threads for the current user"""
    threads = get_user_threads(current_user.id, db, skip, limit)

    # count total threads

    total = (
        db.query(Conversation).filter(Conversation.user_id == current_user.id).count()
    )

    # format as plain dicts
    thread_list = [
        {
            "thread_id": thread["thread_id"],
            "title": thread["title"],
            "message_count": thread["message_count"],
            "last_message_at": (
                thread["last_message_at"].isoformat()
                if thread["last_message_at"]
                else None
            ),
            "created_at": (
                thread["created_at"].isoformat() if thread["created_at"] else None
            ),
        }
        for thread in threads
    ]

    return {"threads": thread_list, "total": total, "skip": skip, "limit": limit}


@router.delete("/{thread_id}")
async def delete_thread(
    thread_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a conversation thread and all its messages"""
    success = delete_conversation(thread_id, current_user.id, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    logger.info("Thread %s deleted by %s", thread_id, current_user.username)

    return {
        "success": True,
        "message": "Conversation deleted successfully",
        "thread_id": thread_id,
    }
