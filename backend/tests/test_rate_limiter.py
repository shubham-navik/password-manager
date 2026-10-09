from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.core.rate_limiter import check_rate_limit


@pytest.mark.asyncio
async def test_request_within_limit_is_allowed():
    with patch(
        "app.core.rate_limiter.redis_client.eval",
        new_callable=AsyncMock,
        return_value=[1, 60],
    ):
        await check_rate_limit(
            key="test:user:1",
            limit=5,
            window_seconds=60,
        )


@pytest.mark.asyncio
async def test_request_over_limit_returns_429():
    with patch(
        "app.core.rate_limiter.redis_client.eval",
        new_callable=AsyncMock,
        return_value=[6, 45],
    ):
        with pytest.raises(HTTPException) as exc_info:
            await check_rate_limit(
                key="test:user:1",
                limit=5,
                window_seconds=60,
            )

        assert exc_info.value.status_code == 429
        assert exc_info.value.headers["Retry-After"] == "45"


@pytest.mark.asyncio
async def test_redis_failure_returns_503():
    with patch(
        "app.core.rate_limiter.redis_client.eval",
        new_callable=AsyncMock,
        side_effect=ConnectionError("Redis unavailable"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await check_rate_limit(
                key="test:user:1",
                limit=5,
                window_seconds=60,
            )

        assert exc_info.value.status_code == 503