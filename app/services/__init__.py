"""Service layer modules"""

from app.services.auth_service import (
    authenticate_user,
    create_user,
    get_user_by_username,
)
from app.services.document_service import (
    save_document,
    process_document,
    get_user_documents,
    get_document_by_id,
    delete_document,
    get_document_stats,
)

# from .chat_service import process_chat_query, get_conversation_history, get_user_threads
# from .history_service import (
#     get_all_conversations,
#     get_conversation_details,
#     get_system_stats,
# )

__all__ = [
    "authenticate_user",
    "create_user",
    "get_user_by_username",
    "save_document",
    "process_document",
    "get_user_documents",
    "get_document_by_id",
    "delete_document",
    "get_document_stats",
    "delete_document",
    "get_document_stats",
]
