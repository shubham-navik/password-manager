from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import (
    create_user,
    get_user_by_email,
)
from app.security.password import hash_password,verify_password
from app.services.session_service import create_user_session
from app.models.user import User

async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
):
    existing_user = await get_user_by_email(
        db,
        email,
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    password_hash = hash_password(password)

    user = await create_user(
        db=db,
        email=email,
        password_hash=password_hash,
    )

    return user
async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> tuple[User, str]:
    user = await get_user_by_email(
        db,
        email,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(
        password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    token = await create_user_session(
        db=db,
        user_id=user.id,
    )

    return user, token