from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Password Manager"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str
    REDIS_URL: str

    SESSION_TTL_SECONDS:int =43200 # 12 hours in seconds
    VAULT_ENCRYPTION_KEY: str

    # Rate limiting (counters are stored in Redis via REDIS_URL)
    RATE_LIMIT_ENABLED: bool = True

    RATE_LIMIT_LOGIN_LIMIT: int = Field(default=5, gt=0)
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = Field(default=60, gt=0)

    RATE_LIMIT_REGISTER_LIMIT: int = Field(default=5, gt=0)
    RATE_LIMIT_REGISTER_WINDOW_SECONDS: int = Field(default=60, gt=0)

    RATE_LIMIT_USER_LIMIT: int = Field(default=60, gt=0)
    RATE_LIMIT_USER_WINDOW_SECONDS: int = Field(default=60, gt=0)

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        # Keep secrets (DB password, encryption key) out of startup errors.
        hide_input_in_errors=True,
    )


settings = Settings()
