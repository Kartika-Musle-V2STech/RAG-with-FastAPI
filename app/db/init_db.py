"""Database Initialization"""

from sqlalchemy import inspect
from app.db.base import Base
from app.db.session import engine, SessionLocal

from app.utils.logger import get_logger

logger = get_logger(__name__)


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def create_tables():
    """Create all tables if not exists"""
    try:
        from app.models import User, Conversation, Message, Document, DocumentChunk

        logger.info("Checking and Creating tables if needed")
        Base.metadata.create_all(engine)

        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info("Database ready. Tables Present: %s", ", ".join(tables))
    except Exception as e:
        logger.error("Failed to create tables: %s", e)
        raise


def init_database():
    """Initialize the database"""
    logger.info("Initializing the database")
    # trying by checking the core user table if its exists
    if not table_exists("users"):
        logger.info("Database tables not found, Creating it")
        create_tables()
    else:
        logger.info("Database tables already exists")

    logger.info("Database initialized successfully")


def get_database_info():
    """Get database information"""

    db = SessionLocal()
    try:
        from app.models import User, Conversation, Message, Document, DocumentChunk

        return {
            "users": db.query(User).count(),
            "conversations": db.query(Conversation).count(),
            "messages": db.query(Message).count(),
            "documents": db.query(Document).count(),
            "document_chunks": db.query(DocumentChunk).count(),
        }
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
    info = get_database_info()
    print("Database Information")
    for table, count in info.items():
        print(f"{table}: {count} records")
