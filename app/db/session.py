"""Database Session Management"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Use StaticPool for SQLite to handle concurrent access
# This allows the same connection to be shared across threads
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=settings.DEBUG,
    poolclass=StaticPool,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Get a database session.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error("Database session error: %s", e)
        db.rollback()
        raise
    finally:
        db.close()
