from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Password Manager"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str
    REDIS_URL: str

    SESSION_TTL_SECONDS:int =43200 # 12 hours in seconds
    VAULT_ENCRYPTION_KEY: str
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()