"""Create admin user"""

import sys
from pathlib import Path
import getpass
from sqlalchemy.exc import SQLAlchemyError
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from app.utils.logger import get_logger

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = get_logger(__name__)


def create_admin_user(username: str, email: str, password: str):
    """Create admin user"""
    db = SessionLocal()

    try:
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            logger.error("Admin user already exists")
            return False

        hashed_password = get_password_hash(password)
        admin_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        logger.info("Admin user created successfully")
        print(f"Username: {username}")
        print(f"Email: {email}")
        return True

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Failed to create admin user")
        print(f"Error:{e}")
        return False
    finally:
        db.close()


def main():
    """Main function"""
    print("Create admin user")
    username = input("Enter Username: ").strip()
    if not username:
        print("Username cannot be empty")
        return

    email = input("Enter Email: ").strip()
    if not email or "@" not in email:
        print("Invalid email address")
        return

    password = getpass.getpass("Enter Password: ")
    if len(password) < 6:
        print("Password must be atleast 6 characters")
        return

    password_confirm = getpass.getpass("Confirm Password: ")
    if password != password_confirm:
        print("Passwords do not match")
        return

    success = create_admin_user(username, email, password)
    if success:
        print("\nYou can now login with these credentials at:")
        print("  http://localhost:8000/docs")


if __name__ == "__main__":
    main()
