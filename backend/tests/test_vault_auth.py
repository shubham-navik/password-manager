import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.parametrize(
    ("method", "url", "payload"),
    [
        (
            "GET",
            "/api/v1/vault",
            None,
        ),
        (
            "POST",
            "/api/v1/vault",
            {
                "title": "Test Account",
                "website_url": "https://example.com",
                "username": "test@example.com",
                "password": "Secret123!",
                "notes": "Test notes",
            },
        ),
        (
            "GET",
            "/api/v1/vault/00000000-0000-0000-0000-000000000001",
            None,
        ),
        (
            "PATCH",
            "/api/v1/vault/00000000-0000-0000-0000-000000000001",
            {
                "title": "Updated Account",
            },
        ),
        (
            "DELETE",
            "/api/v1/vault/00000000-0000-0000-0000-000000000001",
            None,
        ),
    ],
)
def test_vault_endpoints_require_authentication(
    client,
    method,
    url,
    payload,
):
    response = client.request(
        method=method,
        url=url,
        json=payload,
    )

    assert response.status_code in (401, 403)