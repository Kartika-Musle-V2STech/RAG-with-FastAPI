"""
Authentication Service
Business logic for user authentication and registration
"""

from datetime import timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
)
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password"""
    user = get_user_by_username(db, username)
    if not user:
        logger.warning("Authentication failed: user not found - %s", username)
        return None

    if not verify_password(password, user.hashed_password):
        logger.warning("Authentication failed: invalid password - %s", username)
        return None

    logger.info("User authenticated successfully: %s", username)
    return user


def create_user(db: Session, user_data: UserCreate) -> User:
    """Create a new user"""
    if get_user_by_username(db, user_data.username):
        logger.warning("Registration failed: username exists - %s", user_data.username)
        raise ValueError("Username already registered")

    if get_user_by_email(db, user_data.email):
        logger.warning("Registration failed: email exists - %s", user_data.email)
        raise ValueError("Email already registered")

    hashed_password = get_password_hash(user_data.password)

    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=False,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    logger.info("User created successfully: %s", user_data.username)
    return db_user


def create_access_token_for_user(user: User) -> str:
    """Create JWT access token for user"""
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_access_token(
        data={"sub": user.username},
        expires_delta=expires,
    )
