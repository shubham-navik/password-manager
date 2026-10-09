import redis.asyncio as redis

from app.core.config import settings


redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


async def close_redis() -> None:
    await redis_client.aclose()