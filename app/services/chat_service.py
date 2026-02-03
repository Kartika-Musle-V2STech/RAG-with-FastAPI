"""Chat Service"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Conversation, Message, User
from app.rag.pipeline import RAGPipeline
from app.utils.logger import get_logger
from app.utils.helpers import generate_thread_id

logger = get_logger(__name__)


async def process_chat_query(
    query: str,
    user: User,
    thread_id: Optional[str],
    db: Session,
) -> Dict[str, Any]:
    """Process a chat query through RAG pipeline"""
    try:
        # Get or create conversation
        conversation = None
        if thread_id:
            conversation = (
                db.query(Conversation)
                .filter(
                    Conversation.thread_id == thread_id, Conversation.user_id == user.id
                )
                .first()
            )
            if conversation:
                # update existing conversation
                conversation.updated_at = datetime.utcnow()
            else:
                logger.warning(
                    "Conversation not found for thread_id, creating new one: %s",
                    thread_id,
                )

        # Create new conversation if needed
        if not conversation:
            thread_id = generate_thread_id()
            conversation = Conversation(
                thread_id=thread_id,
                user_id=user.id,
                title=query[:50] + "..." if len(query) > 50 else query,
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            logger.info("Created new conversation: %s", thread_id)

        # save user message
        user_message = Message(
            conversation_id=conversation.id, role="user", content=query, msg_metadata={}
        )
        db.add(user_message)
        db.commit()

        # process query using RAG pipeline
        rag_pipeline = RAGPipeline(db)
        result = rag_pipeline.process_query(
            query=query, user_id=user.id, thread_id=thread_id
        )

        # save assistant message
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=result["answer"],
            msg_metadata={
                "sources": result["sources"],
                "confidence": result["metadata"]["confidence"],
                "retrieval_time_ms": result["metadata"]["retrieval_time_ms"],
                "generation_time_ms": result["metadata"]["generation_time_ms"],
            },
        )
        db.add(assistant_message)
        db.commit()

        logger.info(
            "Chat query processed for user %s in thread %s",
            user.username,
            thread_id,
        )

        # return response with thread_id
        response = result.copy()
        response["thread_id"] = thread_id
        response["query"] = query
        response["created_at"] = datetime.utcnow()

        return response

    except Exception as e:
        logger.error("Error processing chat query: %s", e)
        raise


def get_conversation_history(
    thread_id: str, user_id: int, db: Session
) -> List[Dict[str, Any]]:
    """Get conversation history for a thread"""
    conversation = (
        db.query(Conversation)
        .filter(Conversation.thread_id == thread_id, Conversation.user_id == user_id)
        .first()
    )

    if not conversation:
        return None

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
        .all()
    )

    return {
        "thread_id": thread_id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "messages": messages,
        "message_count": len(messages),
    }


def get_user_threads(
    user_id: int, db: Session, skip: int = 0, limit: int = 50
) -> List[Dict[str, Any]]:
    """Get all conversation threads for a user"""
    conversations = (
        db.query(Conversation)
        .filter(Conversation.updated_at == user_id)
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    threads = []
    for conv in conversations:
        message_count = (
            db.query(Message).filter(Message.conversation_id == conv.id).count()
        )

        # get last message time
        last_message = (
            db.query(Message)
            .filter(Message.conversation_id == conv.id)
            .order_by(Message.created_at.desc())
            .first()
        )

        threads.append(
            {
                "thread_id": conv.thread_id,
                "title": conv.title,
                "created_at": conv.created_at,
                "last_message_at": (
                    last_message.created_at if last_message else conv.created_at
                ),
            }
        )

    return threads


def delete_conversation(thread_id: str, user_id: int, db: Session) -> bool:
    """delete conversation thread"""
    conversation = (
        db.query(Conversation)
        .filter(Conversation.thread_id == thread_id, Conversation.user_id == user_id)
        .first()
    )

    if not conversation:
        return False

    db.delete(conversation)
    db.commit()

    logger.info(
        "Conversation deleted for thread_id: %s for user %s", thread_id, user_id
    )
    return True
