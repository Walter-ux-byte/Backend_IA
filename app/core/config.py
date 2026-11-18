"""
Configuración centralizada de la aplicación mediante Pydantic Settings.
Lee las variables del archivo .env y variables del entorno del sistema.
"""
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Metadata del Sistema
    APP_NAME: str = "Sistema de Detección de Violencia con IA"
    APP_ENV: str = "development"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_STR: str = "/api"

    # Red y Servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Seguridad y Criptografía
    SECRET_KEY: str = "clave-secreta-temporal-debe-cambiarse-en-produccion"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    # Base de Datos PostgreSQL
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "password"
    DB_NAME: str = "sistema_violencia_db"
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/sistema_violencia_db"

    # Almacenamiento
    STORAGE_DIR: str = "storage"
    EVIDENCES_IMAGES_DIR: str = "storage/images"
    EVIDENCES_VIDEOS_DIR: str = "storage/videos"
    MAX_UPLOAD_SIZE_MB: int = 50

    # Parámetros de IA
    CONFIDENCE_THRESHOLD: float = 0.50
    DEVICE: str = "cpu"
    FALL_CONFIRMATION_SECONDS: float = 1.5
    INACTIVITY_THRESHOLD_SECONDS: float = 5.0
    ALERT_COOLDOWN_SECONDS: float = 10.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


# Instancia singleton para ser importada en toda la aplicación
settings = Settings()
