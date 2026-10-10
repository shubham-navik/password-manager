| Step  | Feature                   | What you'll learn                                |
| ----- | ------------------------- | ------------------------------------------------ |
| ✅ 1   | User registration         | Password hashing with Argon2                     |
| ✅ 2   | Login                     | Credential verification                          |
| ✅ 3   | Session management        | PostgreSQL + Redis                               |
| ✅ 4   | Authentication dependency | Protecting API routes                            |
| **5** | **Logout**                | Session revocation and cookie deletion           |
| 6     | Logout from all devices   | Managing multiple sessions                       |
| 7     | Password vault CRUD       | SQLAlchemy relationships and database operations |
| 8     | Vault encryption          | AES-GCM and encryption key management            |
| 9     | Rate limiting             | Redis, brute-force protection                    |
| 10    | Testing                   | Pytest and integration tests                     |
| 11    | Frontend                  | React + TypeScript                               |
| 12    | Deployment                | Docker, Nginx, HTTPS, production configuration   |


## Configuration

All configuration is read from environment variables (or a `.env` file in the directory you start the app from) by `backend/app/core/config.py`, using pydantic-settings. Copy `.env.example` to `.env` and fill in the values. `.env` is git-ignored.

Values are validated at startup. A missing required variable or an invalid value (for example a non-positive limit or `RATE_LIMIT_ENABLED=maybe`) stops the app with an error naming the variable. The error never prints the values themselves.

### Required

| Variable               | Purpose                                                                                  |
| ---------------------- | ---------------------------------------------------------------------------------------- |
| `DATABASE_URL`         | PostgreSQL connection string. Must use the `postgresql+asyncpg://` driver.               |
| `REDIS_URL`            | Redis connection string, used for sessions **and** rate-limit counters.                  |
| `VAULT_ENCRYPTION_KEY` | AES-256-GCM key for vault items. URL-safe base64 of exactly 32 bytes (see below).        |

Generate an encryption key:

```bash
python -c "import base64,secrets;print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"
```

### Rate limiting

| Variable                             | Default | Applies to                                    |
| ------------------------------------ | ------- | --------------------------------------------- |
| `RATE_LIMIT_ENABLED`                 | `true`  | Turns all rate limiting on or off             |
| `RATE_LIMIT_LOGIN_LIMIT`             | `5`     | `POST /auth/login`, requests per client IP    |
| `RATE_LIMIT_LOGIN_WINDOW_SECONDS`    | `60`    | Window for the login limit                    |
| `RATE_LIMIT_REGISTER_LIMIT`          | `5`     | `POST /auth/register`, requests per client IP |
| `RATE_LIMIT_REGISTER_WINDOW_SECONDS` | `60`    | Window for the register limit                 |
| `RATE_LIMIT_USER_LIMIT`              | `60`    | All `/api/v1/vault` endpoints, per user       |
| `RATE_LIMIT_USER_WINDOW_SECONDS`     | `60`    | Window for the per-user limit                 |

Limits are counted in fixed windows in Redis. A request over the limit gets `429 Too Many Requests` with a `Retry-After` header. If Redis is unreachable, rate-limited endpoints return `503` (they fail closed).

**Locally:** set the values in `.env` and restart the server. Settings are read once at startup. For load testing with Locust (`locustfile.py` registers and logs in many users from one IP), either raise the login and register limits or set `RATE_LIMIT_ENABLED=false`.

**Production:**

- Provide the variables through your deployment's secret store or environment, not a committed file.
- Use an authenticated, TLS-encrypted Redis URL, e.g. `rediss://:<password>@<host>:6379/0`.
- Keep `RATE_LIMIT_ENABLED=true` unless an upstream proxy enforces equivalent limits.
- Point every app instance and worker at the **same** Redis so they share counters.
- If the app runs behind a reverse proxy (e.g. nginx), start uvicorn with `--proxy-headers --forwarded-allow-ips=<proxy IP>`. Otherwise every client is seen as the proxy's IP and they all share one per-IP limit.

## Running

```bash
docker compose up -d                       # Postgres (host port 5434) and Redis
.venv/bin/pip install -r backend/requirements.txt
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --app-dir backend --reload
```

Run commands from the repository root so `.env` is found.

## Tests

The tests mock Redis, so they don't need Postgres or Redis running.

```bash
.venv/bin/python -m pytest backend                                   # everything
.venv/bin/python -m pytest backend/tests/test_rate_limit_config.py   # rate-limit configuration
.venv/bin/python -m pytest backend/tests/test_rate_limiter.py        # limiter core
```
