from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    COOKIE_SECURE: bool = False
    FRONTEND_ORIGINS: str = "http://localhost:5173"

    RESEND_API_KEY: str
    RESEND_SENDER_EMAIL: str
    FRONTEND_URL: str

    # Proveedor de correo: "resend" (por defecto, desarrollo local) o "acs" (Azure Communication Services).
    EMAIL_PROVIDER: str = "resend"
    ACS_CONNECTION_STRING: str = ""
    ACS_SENDER_ADDRESS: str = ""

    INTERNAL_SERVICE_KEY: str

    # Límites de frecuencia por IP y por minuto (0 = sin límite).
    RATE_LIMIT_LOGIN_PER_MIN: int = 60
    RATE_LIMIT_REGISTER_PER_MIN: int = 20
    RATE_LIMIT_RESET_PER_MIN: int = 10
    # Retención de tokens vencidos e intentos de login, en días, y cada cuántas horas se depura (0 = no depurar).
    RETENTION_DAYS: int = 30
    PURGE_INTERVAL_HOURS: int = 24

    # Máximo de solicitudes de restablecimiento por cuenta y hora (TC-AUT-18).
    RESET_REQUESTS_PER_HOUR: int = 5


settings = Settings()
import uuid

MENTEE_ROLE_ID = uuid.UUID("123e4567-e89b-12d3-a456-426614174000")
MENTOR_ROLE_ID = uuid.UUID("223e4567-e89b-12d3-a456-426614174000")
ADMIN_ROLE_ID = uuid.UUID("323e4567-e89b-12d3-a456-426614174000")
KNOWN_ROLE_IDS = {MENTEE_ROLE_ID, MENTOR_ROLE_ID, ADMIN_ROLE_ID}
