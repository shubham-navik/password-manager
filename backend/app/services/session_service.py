from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import redis_client
from app.repositories.session_repository import create_session , revoke_session, revoke_all_user_sessions
from app.security.session import (
    generate_session_token,
    hash_session_token,
)


async def create_user_session(
    db: AsyncSession,
    user_id: UUID,
) -> str:
    token = generate_session_token()
    session_identifier = hash_session_token(token)

    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=settings.SESSION_TTL_SECONDS
    )

    session = await create_session(
        db=db,
        user_id=user_id,
        session_identifier=session_identifier,
        expires_at=expires_at,
    )

    redis_key = f"session:{session.session_identifier}"

    try:
        await redis_client.set(
            redis_key,
            str(user_id),
            ex=settings.SESSION_TTL_SECONDS,
        )
    except Exception:
        session.revoked_at = datetime.now(timezone.utc)
        await db.commit()
        raise

    return token

async def logout_user(
    db: AsyncSession,
    token: str,
) -> None:
    session_identifier = hash_session_token(token)

    await revoke_session(
        db=db,
        session_identifier=session_identifier,
    )

    redis_key = f"session:{session_identifier}"

    await redis_client.delete(redis_key)


async def logout_all_user_sessions(
    db: AsyncSession,
    user_id: UUID,
) -> None:
    session_identifiers = await revoke_all_user_sessions(
        db=db,
        user_id=user_id,
    )

    if not session_identifiers:
        return

    redis_keys = [
        f"session:{identifier}"
        for identifier in session_identifiers
    ]

    await redis_client.delete(*redis_keys)