"""
Configuración de conexión y sesión a Base de Datos mediante SQLAlchemy.
Soporta PostgreSQL nativo y SQLite para entornos de prueba/fallback.
"""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from app.core.config import settings

# Base declarativa para todos los modelos ORM
Base = declarative_base()

# Configuración del motor SQLAlchemy
# Si se usa SQLite en tests, se añade check_same_thread=False
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,  # Comprueba que la conexión siga viva antes de usarla (RNF-01)
    connect_args=connect_args,
)

# Creador de sesiones
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    Generador de sesión de base de datos para inyección de dependencias en FastAPI.
    Garantiza que la sesión se cierre al finalizar cada petición HTTP.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
