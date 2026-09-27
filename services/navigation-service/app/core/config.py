import uuid

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    AUTH_SERVICE_URL: str
    INTERNAL_SERVICE_KEY: str

    RESEND_API_KEY: str
    RESEND_SENDER_EMAIL: str
    FRONTEND_URL: str

    FRONTEND_ORIGINS: str = "http://localhost:5173"


settings = Settings()

# Mismos UUIDs fijos que Auth Service y Role Service.
MENTEE_ROLE_ID = uuid.UUID("123e4567-e89b-12d3-a456-426614174000")
MENTOR_ROLE_ID = uuid.UUID("223e4567-e89b-12d3-a456-426614174000")
ADMIN_ROLE_ID = uuid.UUID("323e4567-e89b-12d3-a456-426614174000")
