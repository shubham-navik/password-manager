from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import redis_client
from app.repositories.session_repository import get_active_session
from app.repositories.user_repository import get_user_by_id
from app.security.session import hash_session_token


async def get_current_user(
    session_token: Annotated[
        str | None,
        Cookie(alias="pm_session"),
    ] = None,
    db: AsyncSession = Depends(get_db),
):
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Cookie"},
    )

    if not session_token:
        raise credentials_error

    session_identifier = hash_session_token(session_token)

    session = await get_active_session(
        db=db,
        session_identifier=session_identifier,
    )

    if session is None:
        raise credentials_error

    redis_key = f"session:{session_identifier}"

    try:
        cached_user_id = await redis_client.get(redis_key)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session service temporarily unavailable",
        )

    if cached_user_id != str(session.user_id):
        raise credentials_error

    user = await get_user_by_id(
        db=db,
        user_id=session.user_id,
    )

    if user is None or not user.is_active:
        raise credentials_error

    return user