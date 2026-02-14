"""
Authentication Routes for Grant Alignment Engine.

Handles login, registration, token refresh, and current user info.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from dependencies import get_current_user
from models import User, UserRoleEnum
from schemas import UserRead, TokenResponse
from services.auth_service import (
    hash_password,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class LoginRequest(BaseModel):
    """Login request payload."""
    email: str = Field(description="User email address")
    password: str = Field(description="User password")


class RegisterRequest(BaseModel):
    """Registration request payload."""
    email: str = Field(description="User email address")
    name: str = Field(min_length=1, max_length=255, description="Full name")
    password: str = Field(min_length=8, description="Password (min 8 characters)")
    role: Optional[UserRoleEnum] = Field(default=UserRoleEnum.VIEWER, description="User role")


class RefreshRequest(BaseModel):
    """Token refresh request payload."""
    refresh_token: str = Field(description="JWT refresh token")


# ============================================================================
# AUTH ENDPOINTS
# ============================================================================


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate with email and password, returns JWT tokens.

    Args:
        request: Login credentials.
        db: Database session.

    Returns:
        TokenResponse: Access and refresh tokens.

    Raises:
        HTTPException: If credentials are invalid.
    """
    user = await authenticate_user(db, request.email, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        role=user.role.value,
    )
    refresh_token = create_refresh_token(user_id=str(user.id))

    logger.info(f"User logged in: {user.email}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRATION_HOURS * 3600,
    )


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """
    Register a new user account.

    Args:
        request: Registration data.
        db: Database session.

    Returns:
        UserRead: Created user info.

    Raises:
        HTTPException: If email is already taken.
    """
    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == request.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=request.email.lower(),
        name=request.name,
        hashed_password=hash_password(request.password),
        role=request.role or UserRoleEnum.VIEWER,
        is_active=True,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"New user registered: {user.email} ({user.role.value})")

    return UserRead.model_validate(user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Get a new access token using a refresh token.

    Args:
        request: Refresh token.
        db: Database session.

    Returns:
        TokenResponse: New access and refresh tokens.

    Raises:
        HTTPException: If refresh token is invalid or expired.
    """
    try:
        payload = decode_token(request.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Load user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Issue new tokens
    access_token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        role=user.role.value,
    )
    new_refresh_token = create_refresh_token(user_id=str(user.id))

    logger.info(f"Token refreshed for user: {user.email}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRATION_HOURS * 3600,
    )


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user info",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    """
    Get the currently authenticated user's info.

    Args:
        current_user: Authenticated user from JWT.

    Returns:
        UserRead: Current user info.
    """
    return UserRead.model_validate(current_user)
