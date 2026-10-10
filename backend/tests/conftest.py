import pytest

from app.core.config import settings


@pytest.fixture(autouse=True)
def rate_limiting_enabled(monkeypatch):
    # Keep tests independent of a local .env that disables rate limiting.
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
