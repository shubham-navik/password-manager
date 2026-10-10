# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

A learning-oriented password manager built step by step (see the roadmap table in README.md). Only the FastAPI backend exists so far. `frontend/` is empty, and `backend/Dockerfile`, `docker-compose.prod.yml`, `nginx/nginx.conf` and `docker/postgres/init.sql` are empty placeholders for later roadmap steps (React frontend, deployment).

## Commands

Run everything from the **repo root**. `Settings` loads `.env` from the current working directory, and `alembic.ini` lives at the root. The virtualenv is `.venv/` at the root.

```bash
# Start Postgres (host port 5434, not 5432) and Redis (6379)
docker compose up -d

# Install deps
.venv/bin/pip install -r backend/requirements.txt

# Apply migrations (alembic.ini points at backend/alembic; env.py adds backend/ to sys.path)
.venv/bin/alembic upgrade head
.venv/bin/alembic revision --autogenerate -m "describe change"

# Run the API (the `app` package lives under backend/)
.venv/bin/uvicorn app.main:app --app-dir backend --reload

# Tests
.venv/bin/python -m pytest backend
.venv/bin/python -m pytest backend/tests/test_rate_limiter.py
.venv/bin/python -m pytest backend/tests/test_rate_limiter.py::test_request_over_limit_returns_429
```

There is no pytest config or conftest. Pytest's rootdir-based sys.path insertion makes `import app` work. Tests mock Redis (`patch("app.core.rate_limiter.redis_client.eval", ...)`) or only exercise unauthenticated and crypto paths, so the current suite doesn't need live Postgres or Redis. It still needs a valid `.env`, because `app.core.config.settings` is built at import time. `backend/test_encryption.py` is a stray test outside `backend/tests/`.

Required env vars: `DATABASE_URL` (must use `postgresql+asyncpg://`), `REDIS_URL` and `VAULT_ENCRYPTION_KEY`. `.env.example` doesn't include `VAULT_ENCRYPTION_KEY` yet. It must be URL-safe base64 that decodes to exactly 32 bytes:
`python -c "import base64,secrets;print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"`

## Architecture

The app is fully async and layered: `api/routes` → `services` → `repositories` → `models`. Pydantic request and response models are in `schemas/`, and crypto primitives are in `security/`. Services raise `HTTPException` directly. Repositories call `db.commit()` themselves, so each repository write is its own transaction (no unit-of-work spanning calls). Auth and session code uses module-level functions, while the vault uses classes with `@staticmethod`s (`VaultService`, `VaultRepository`). 

**Sessions (dual store: Postgres + Redis).** Login generates an opaque token (`secrets.token_urlsafe`) and sends it to the client in the `pm_session` httpOnly cookie. Only its SHA-256 hash (`session_identifier`) is stored: as a row in the `sessions` table, and as the Redis key `session:<hash>` → `user_id` with TTL `SESSION_TTL_SECONDS`. `api/dependencies.get_current_user` requires **both**: an active DB row (not revoked, not expired) *and* a matching Redis value. If Redis is down, authentication returns 503 rather than falling back to the DB. Logout and logout-all set `revoked_at` in the DB and delete the Redis keys. If the Redis write fails during login, the new DB session is revoked.

**Vault encryption.** `security/encryption.py` uses AES-256-GCM with one server-wide key (`VAULT_ENCRYPTION_KEY`). The stored format is `nonce(12 bytes) || ciphertext+tag`, kept in `LargeBinary` columns (`encrypted_password`, `encrypted_notes`). Encryption and decryption happen only in `VaultService`. `_to_detail` decrypts for single-item responses, and list responses (`VaultItemSummary`) never decrypt. PATCH uses `model_dump(exclude_unset=True)`, maps `password`/`notes` onto the encrypted columns, and rejects an explicit `null` for `title` or `password`. Every vault query is scoped by `user_id` as well as `item_id`.

**Rate limiting.** `core/rate_limiter.check_rate_limit` runs an atomic Lua INCR+EXPIRE fixed-window script in Redis. It returns 429 with `Retry-After`, or 503 if Redis is unreachable. `api/rate_limit_dependencies.py` provides `rate_limit_by_ip(limit, window, scope)` (a dependency factory used on `/auth/register` and `/auth/login` at 5/min) and `limit_by_user`, which is attached at router level to the whole vault router at 60/min and depends on `get_current_user`.

**Routes.** `/auth/*` (register, login, me, logout, logout-all) and `/api/v1/vault` (CRUD). `main.py` also exposes `/health` and `/health/db`.

**Migrations.** When you add a model, import it in `app/models/__init__.py` so Alembic autogenerate sees it (`alembic/env.py` imports `User`, `Session`, `VaultItem` from there). The `sqlalchemy.url` value in `alembic.ini` is blank on purpose. It's set from `settings.DATABASE_URL`.

**Dev-only settings to revisit for production.** Cookies are set with `secure=False`, and the cookie `max_age=43200` is hardcoded in `routes/auth.py` instead of reading `SESSION_TTL_SECONDS`. The engine runs with `echo=True`. Redis is created at import time in `core/redis.py`, and `close_redis()` isn't wired to app shutdown.
