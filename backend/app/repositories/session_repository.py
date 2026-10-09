from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session


async def create_session(
    db: AsyncSession,
    user_id: UUID,
    session_identifier: str,
    expires_at: datetime,
) -> Session:
    session = Session(
        user_id=user_id,
        session_identifier=session_identifier,
        expires_at=expires_at,
    )

    db.add(session)

    await db.commit()
    await db.refresh(session)

    return session


async def get_active_session(
    db: AsyncSession,
    session_identifier: str,
) -> Session | None:
    result = await db.execute(
        select(Session).where(
            Session.session_identifier == session_identifier,
            Session.revoked_at.is_(None),
            Session.expires_at > datetime.now(timezone.utc),
        )
    )

    return result.scalar_one_or_none()

async def revoke_session(
    db: AsyncSession,
    session_identifier: str,
) -> bool:
    session = await get_active_session(
        db=db,
        session_identifier=session_identifier,
    )

    if session is None:
        return False

    session.revoked_at = datetime.now(timezone.utc)

    await db.commit()

    return True

async def revoke_all_user_sessions(
    db: AsyncSession,
    user_id: UUID,
) -> list[str]:
    result = await db.execute(
        select(Session).where(
            Session.user_id == user_id,
            Session.revoked_at.is_(None),
        )
    )

    sessions = result.scalars().all()

    session_identifiers = [
        session.session_identifier for session in sessions
    ]

    revoked_at = datetime.now(timezone.utc)

    for session in sessions:
        session.revoked_at = revoked_at

    await db.commit()

    return session_identifiers    