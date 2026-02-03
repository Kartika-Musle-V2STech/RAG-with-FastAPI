"""
History Service for viewing conversation history and system statistics (Admin)
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import User, Conversation, Message, Document, DocumentChunk
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_all_conversations(
    db: Session, skip: int = 0, limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get all conversations (admin only)
    """
    conversations = (
        db.query(Conversation)
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for conv in conversations:
        # Get user
        user = db.query(User).filter(User.id == conv.user_id).first()

        # Get message count
        message_count = (
            db.query(Message).filter(Message.conversation_id == conv.id).count()
        )

        # Get last message
        last_message = (
            db.query(Message)
            .filter(Message.conversation_id == conv.id)
            .order_by(Message.created_at.desc())
            .first()
        )

        result.append(
            {
                "conversation_id": conv.id,
                "thread_id": conv.thread_id,
                "user_id": conv.user_id,
                "username": user.username if user else "Unknown",
                "title": conv.title,
                "message_count": message_count,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
                "last_message": last_message.content[:100] if last_message else None,
            }
        )

    return result


def get_conversation_details(thread_id: str, db: Session) -> Dict[str, Any]:
    """
    Get detailed conversation information (admin only)
    """
    conversation = (
        db.query(Conversation).filter(Conversation.thread_id == thread_id).first()
    )

    if not conversation:
        return None

    # Get user
    user = db.query(User).filter(User.id == conversation.user_id).first()

    # Get all messages
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
        .all()
    )

    return {
        "thread_id": conversation.thread_id,
        "user": (
            {"id": user.id, "username": user.username, "email": user.email}
            if user
            else None
        ),
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "metadata": msg.metadata,
                "created_at": msg.created_at,
            }
            for msg in messages
        ],
    }


def get_system_stats(db: Session) -> Dict[str, Any]:
    """
    Get system-wide statistics (admin only)
    """
    # User statistics
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active).count()
    admin_users = db.query(User).filter(User.is_admin).count()

    # Conversation statistics
    total_conversations = db.query(Conversation).count()
    total_messages = db.query(Message).count()

    # Document statistics
    total_documents = db.query(Document).count()
    completed_documents = (
        db.query(Document).filter(Document.processed_status == "completed").count()
    )
    total_chunks = db.query(DocumentChunk).count()

    # Get most active users
    most_active = (
        db.query(
            User.username,
            func.count(Conversation.id).label(
                "conversation_count"
            ),  # pylint: disable=not-callable # type: ignore
        )
        .join(Conversation, User.id == Conversation.user_id)
        .group_by(User.id)
        .order_by(
            func.count(
                Conversation.id
            ).desc()  # pylint: disable=not-callable # type: ignore
        )
        .limit(5)
        .all()
    )

    # Document statistics by type
    doc_types = (
        db.query(
            Document.file_type,
            func.count(Document.id).label(
                "count"
            ),  # pylint: disable=not-callable # type: ignore
        )
        .group_by(Document.file_type)
        .all()
    )

    # Average messages per conversation
    avg_messages = (
        db.query(
            func.avg(  # pylint: disable=not-callable # type: ignore
                db.query(
                    func.count(Message.id)
                )  # pylint: disable=not-callable # type: ignore
                .filter(Message.conversation_id == Conversation.id)
                .scalar_subquery()
            )
        ).scalar()
        or 0
    )

    return {
        "users": {"total": total_users, "active": active_users, "admin": admin_users},
        "conversations": {
            "total": total_conversations,
            "total_messages": total_messages,
            "avg_messages_per_conversation": round(float(avg_messages), 2),
        },
        "documents": {
            "total": total_documents,
            "completed": completed_documents,
            "total_chunks": total_chunks,
            "by_type": {doc_type: count for doc_type, count in doc_types},
        },
        "most_active_users": [
            {"username": username, "conversations": count}
            for username, count in most_active
        ],
    }


def search_conversations(
    query: str, db: Session, limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Search conversations by content (admin only)
    """
    # Search in message content
    matching_messages = (
        db.query(Message).filter(Message.content.like(f"%{query}%")).limit(limit).all()
    )

    # Get unique conversations
    conversation_ids = set(msg.conversation_id for msg in matching_messages)

    results = []
    for conv_id in conversation_ids:
        conversation = db.query(Conversation).filter(Conversation.id == conv_id).first()

        if conversation:
            user = db.query(User).filter(User.id == conversation.user_id).first()

            # Get matching messages for this conversation
            conv_messages = [
                msg for msg in matching_messages if msg.conversation_id == conv_id
            ]

            results.append(
                {
                    "thread_id": conversation.thread_id,
                    "username": user.username if user else "Unknown",
                    "title": conversation.title,
                    "matching_messages": len(conv_messages),
                    "preview": (
                        conv_messages[0].content[:200] if conv_messages else None
                    ),
                    "created_at": conversation.created_at,
                }
            )

    return results
