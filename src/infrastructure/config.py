# Infrastructure Configuration
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de aplicación desde .env

    Thread-safety: Las Settings son inmutables después de carga.
    """

    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
