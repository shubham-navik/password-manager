from fastapi import HTTPException, Request, status

from app.core.config import settings
from app.core.redis import redis_client


RATE_LIMIT_SCRIPT = """
local current = redis.call("INCR", KEYS[1])

if current == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end

local ttl = redis.call("TTL", KEYS[1])

return {current, ttl}
"""


async def check_rate_limit(
    key: str,
    limit: int,
    window_seconds: int,
) -> None:
    if not settings.RATE_LIMIT_ENABLED:
        return

    try:
        result = await redis_client.eval(
            RATE_LIMIT_SCRIPT,
            1,
            key,
            window_seconds,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiting service is unavailable",
        ) from exc

    request_count = int(result[0])

    if request_count > limit:
        retry_after = max(int(result[1]), 1)

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )


def get_client_identifier(request: Request) -> str:
    client = request.client

    if client is None:
        return "unknown"

    return client.host