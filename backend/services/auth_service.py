"""
Authentication Service for FOAM Grant Alignment Engine.

Handles password hashing, JWT token creation/validation, and user authentication.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import bcrypt
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import User

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt directly."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using bcrypt directly."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def create_access_token(user_id: str, email: str, role: str) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: User UUID as string.
        email: User email.
        role: User role.

    Returns:
        Encoded JWT token string.
    """
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """
    Create a JWT refresh token.

    Args:
        user_id: User UUID as string.

    Returns:
        Encoded JWT refresh token string.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_EXPIRATION_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string.

    Returns:
        Decoded token payload.

    Raises:
        JWTError: If token is invalid or expired.
    """
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password.

    Args:
        db: Database session.
        email: User email.
        password: Plain text password.

    Returns:
        User object if authentication succeeds, None otherwise.
    """
    result = await db.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"Login attempt for non-existent user: {email}")
        return None

    if not verify_password(password, user.hashed_password):
        logger.warning(f"Invalid password for user: {email}")
        return None

    if not user.is_active:
        logger.warning(f"Login attempt for inactive user: {email}")
        return None

    return user
