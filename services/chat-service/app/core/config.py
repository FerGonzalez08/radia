from pydantic_settings import BaseSettings, SettingsConfigDict
import uuid

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    AUTH_SERVICE_URL: str
    NAVIGATION_SERVICE_URL: str
    INTERNAL_SERVICE_KEY: str
    FRONTEND_ORIGINS: str = "http://localhost:5173"
    # Máximo de mensajes por usuaria y minuto (ASR-25); 0 desactiva el límite.
    MESSAGES_PER_MINUTE: int = 40
    # Longitud máxima de un mensaje (coincide con la columna String(2000)).
    MAX_MESSAGE_LENGTH: int = 2000

MENTEE_ROLE_ID = uuid.UUID("123e4567-e89b-12d3-a456-426614174000")
MENTOR_ROLE_ID = uuid.UUID("223e4567-e89b-12d3-a456-426614174000")

settings = Settings()
