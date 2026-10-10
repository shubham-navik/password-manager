from fastapi import Depends, Request

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.rate_limiter import (
    check_rate_limit,
    get_client_identifier,
)
from app.models.user import User


async def limit_login_by_ip(request: Request) -> None:
    client_id = get_client_identifier(request)

    await check_rate_limit(
        key=f"rate_limit:ip:login:{client_id}",
        limit=settings.RATE_LIMIT_LOGIN_LIMIT,
        window_seconds=settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS,
    )


async def limit_register_by_ip(request: Request) -> None:
    client_id = get_client_identifier(request)

    await check_rate_limit(
        key=f"rate_limit:ip:register:{client_id}",
        limit=settings.RATE_LIMIT_REGISTER_LIMIT,
        window_seconds=settings.RATE_LIMIT_REGISTER_WINDOW_SECONDS,
    )


async def limit_by_user(
    current_user: User = Depends(get_current_user),
) -> None:
    await check_rate_limit(
        key=f"rate_limit:user:{current_user.id}",
        limit=settings.RATE_LIMIT_USER_LIMIT,
        window_seconds=settings.RATE_LIMIT_USER_WINDOW_SECONDS,
    )
