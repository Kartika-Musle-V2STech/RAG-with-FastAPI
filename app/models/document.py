"""Document Model"""

from sqlalchemy import Column, Integer, Text, ForeignKey, String, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Document(Base):
    """Document Model"""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(100), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    processed_status = Column(String(20), default="pending", nullable=False)
    chunk_count = Column(Integer, nullable=False, default=0)
    uploaded_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,  # pylint: disable=not-callable
    )

    # Document belongs to one user
    user = relationship("User", back_populates="documents")

    # One document → many chunks
    chunks = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(Base):
    """Document Chunk Model"""

    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    chroma_id = Column(String(100), nullable=True)  # Set after embedding generation
    chunk_metadata = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,  # pylint: disable=not-callable
    )

    # chunk and document relationship
    document = relationship("Document", back_populates="chunks")
