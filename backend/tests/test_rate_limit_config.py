import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.rate_limit_dependencies import limit_by_user
from app.core.config import Settings, settings
from app.core.rate_limiter import check_rate_limit
from app.main import app


REQUIRED_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/test",
    "REDIS_URL": "redis://localhost:6379/0",
    "VAULT_ENCRYPTION_KEY": "test-key",
}

LOGIN_PAYLOAD = {
    "email": "user@example.com",
    "password": "Secret123!",
}


@pytest.fixture
def base_env(monkeypatch):
    for name in list(Settings.model_fields):
        monkeypatch.delenv(name, raising=False)

    for name, value in REQUIRED_ENV.items():
        monkeypatch.setenv(name, value)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_eval():
    with patch(
        "app.core.rate_limiter.redis_client.eval",
        new_callable=AsyncMock,
    ) as mocked:
        yield mocked


@pytest.fixture
def mock_login_user():
    user = SimpleNamespace(
        id=uuid.uuid4(),
        email=LOGIN_PAYLOAD["email"],
        is_active=True,
    )

    with patch(
        "app.api.routes.auth.login_user",
        new_callable=AsyncMock,
        return_value=(user, "session-token"),
    ) as mocked:
        yield mocked


# --- Settings loading and validation ---


def test_defaults_match_previous_hardcoded_limits(base_env):
    loaded = Settings(_env_file=None)

    assert loaded.RATE_LIMIT_ENABLED is True
    assert loaded.RATE_LIMIT_LOGIN_LIMIT == 5
    assert loaded.RATE_LIMIT_LOGIN_WINDOW_SECONDS == 60
    assert loaded.RATE_LIMIT_REGISTER_LIMIT == 5
    assert loaded.RATE_LIMIT_REGISTER_WINDOW_SECONDS == 60
    assert loaded.RATE_LIMIT_USER_LIMIT == 60
    assert loaded.RATE_LIMIT_USER_WINDOW_SECONDS == 60


def test_limits_are_loaded_from_environment(base_env, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_LIMIT", "10")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_WINDOW_SECONDS", "300")
    monkeypatch.setenv("RATE_LIMIT_REGISTER_LIMIT", "3")
    monkeypatch.setenv("RATE_LIMIT_REGISTER_WINDOW_SECONDS", "3600")
    monkeypatch.setenv("RATE_LIMIT_USER_LIMIT", "120")
    monkeypatch.setenv("RATE_LIMIT_USER_WINDOW_SECONDS", "30")

    loaded = Settings(_env_file=None)

    assert loaded.RATE_LIMIT_ENABLED is False
    assert loaded.RATE_LIMIT_LOGIN_LIMIT == 10
    assert loaded.RATE_LIMIT_LOGIN_WINDOW_SECONDS == 300
    assert loaded.RATE_LIMIT_REGISTER_LIMIT == 3
    assert loaded.RATE_LIMIT_REGISTER_WINDOW_SECONDS == 3600
    assert loaded.RATE_LIMIT_USER_LIMIT == 120
    assert loaded.RATE_LIMIT_USER_WINDOW_SECONDS == 30


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("RATE_LIMIT_LOGIN_LIMIT", "0"),
        ("RATE_LIMIT_LOGIN_LIMIT", "-1"),
        ("RATE_LIMIT_LOGIN_LIMIT", "five"),
        ("RATE_LIMIT_REGISTER_WINDOW_SECONDS", "0"),
        ("RATE_LIMIT_USER_LIMIT", "1.5"),
        ("RATE_LIMIT_USER_WINDOW_SECONDS", ""),
        ("RATE_LIMIT_ENABLED", "maybe"),
    ],
)
def test_invalid_rate_limit_values_are_rejected(base_env, monkeypatch, name, value):
    monkeypatch.setenv(name, value)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    assert name in str(exc_info.value)


def test_missing_redis_url_is_rejected(base_env, monkeypatch):
    monkeypatch.delenv("REDIS_URL")

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    assert "REDIS_URL" in str(exc_info.value)


def test_config_errors_do_not_expose_secret_values(base_env, monkeypatch):
    monkeypatch.setenv("VAULT_ENCRYPTION_KEY", "super-secret-key-value")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_LIMIT", "0")
    monkeypatch.delenv("REDIS_URL")

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    message = str(exc_info.value)

    assert "REDIS_URL" in message
    assert "RATE_LIMIT_LOGIN_LIMIT" in message
    assert "super-secret-key-value" not in message
    assert "user:pass" not in message


# --- Enable / disable ---


@pytest.mark.asyncio
async def test_disabled_rate_limiting_skips_redis(monkeypatch, mock_eval):
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", False)

    await check_rate_limit(key="test:key", limit=1, window_seconds=60)

    mock_eval.assert_not_awaited()


@pytest.mark.asyncio
async def test_disabled_rate_limiting_does_not_fail_when_redis_is_down(
    monkeypatch,
    mock_eval,
):
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", False)
    mock_eval.side_effect = ConnectionError("Redis unavailable")

    await check_rate_limit(key="test:key", limit=1, window_seconds=60)


# --- Routes use the configured limits ---


def test_login_uses_configured_limit_and_window(
    client,
    monkeypatch,
    mock_eval,
    mock_login_user,
):
    monkeypatch.setattr(settings, "RATE_LIMIT_LOGIN_LIMIT", 10)
    monkeypatch.setattr(settings, "RATE_LIMIT_LOGIN_WINDOW_SECONDS", 300)
    mock_eval.return_value = [10, 299]

    response = client.post("/auth/login", json=LOGIN_PAYLOAD)

    assert response.status_code == 200
    assert response.json()["email"] == LOGIN_PAYLOAD["email"]
    assert "pm_session" in response.cookies
    mock_eval.assert_awaited_once()
    assert mock_eval.await_args.args[1:] == (
        1,
        "rate_limit:ip:login:testclient",
        300,
    )


def test_login_over_configured_limit_returns_429(
    client,
    monkeypatch,
    mock_eval,
    mock_login_user,
):
    monkeypatch.setattr(settings, "RATE_LIMIT_LOGIN_LIMIT", 10)
    mock_eval.return_value = [11, 42]

    response = client.post("/auth/login", json=LOGIN_PAYLOAD)

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "42"
    assert response.json() == {
        "detail": "Too many requests. Please try again later.",
    }
    mock_login_user.assert_not_awaited()


def test_login_succeeds_past_limit_when_disabled(
    client,
    monkeypatch,
    mock_eval,
    mock_login_user,
):
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", False)
    mock_eval.return_value = [1000, 30]

    response = client.post("/auth/login", json=LOGIN_PAYLOAD)

    assert response.status_code == 200
    mock_eval.assert_not_awaited()


def test_register_over_configured_limit_returns_429(
    client,
    monkeypatch,
    mock_eval,
):
    monkeypatch.setattr(settings, "RATE_LIMIT_REGISTER_LIMIT", 2)
    monkeypatch.setattr(settings, "RATE_LIMIT_REGISTER_WINDOW_SECONDS", 120)
    mock_eval.return_value = [3, 100]

    response = client.post("/auth/register", json=LOGIN_PAYLOAD)

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "100"
    assert mock_eval.await_args.args[1:] == (
        1,
        "rate_limit:ip:register:testclient",
        120,
    )


@pytest.mark.asyncio
async def test_user_limit_uses_configured_values(monkeypatch, mock_eval):
    monkeypatch.setattr(settings, "RATE_LIMIT_USER_LIMIT", 3)
    monkeypatch.setattr(settings, "RATE_LIMIT_USER_WINDOW_SECONDS", 15)
    user = SimpleNamespace(id=uuid.uuid4())

    mock_eval.return_value = [3, 10]
    await limit_by_user(current_user=user)

    assert mock_eval.await_args.args[1:] == (
        1,
        f"rate_limit:user:{user.id}",
        15,
    )

    mock_eval.return_value = [4, 10]
    with pytest.raises(HTTPException) as exc_info:
        await limit_by_user(current_user=user)

    assert exc_info.value.status_code == 429


def test_vault_still_requires_auth_when_rate_limiting_disabled(
    client,
    monkeypatch,
):
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", False)

    response = client.get("/api/v1/vault")

    assert response.status_code == 401
