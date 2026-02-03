"""User Model"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class User(Base):
    """User Account model"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,  # pylint: disable=not-callable
    )

    conversations = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )

    documents = relationship(
        "Document", back_populates="user", cascade="all, delete-orphan"
    )

    # For printing
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
