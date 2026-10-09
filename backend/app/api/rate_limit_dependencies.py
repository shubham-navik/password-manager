from fastapi import Depends, Request

from app.api.dependencies import get_current_user
from app.core.rate_limiter import (
    check_rate_limit,
    get_client_identifier,
)
from app.models.user import User


def rate_limit_by_ip(
    limit: int,
    window_seconds: int = 60,
    scope: str = "global",
):
    async def dependency(request: Request) -> None:
        client_id = get_client_identifier(request)

        await check_rate_limit(
            key=f"rate_limit:ip:{scope}:{client_id}",
            limit=limit,
            window_seconds=window_seconds,
        )

    return dependency


async def limit_by_ip(request: Request) -> None:
    client_id = get_client_identifier(request)

    await check_rate_limit(
        key=f"rate_limit:ip:{client_id}",
        limit=60,
        window_seconds=60,
    )


async def limit_by_user(
    current_user: User = Depends(get_current_user),
) -> None:
    await check_rate_limit(
        key=f"rate_limit:user:{current_user.id}",
        limit=60,
        window_seconds=60,
    )