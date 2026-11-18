"""
Módulo centralizado de Modelos ORM de SQLAlchemy.
Exporta todas las entidades para facilitar su importación y configuración de migraciones.
"""
from app.core.database import Base
from app.models.enums import (
    RolUsuario,
    EstadoCamara,
    TipoFuenteCamara,
    TipoIncidente,
    NivelRiesgo,
    EstadoIncidente,
    PrioridadAlerta,
    EstadoAlerta,
    TipoEvidencia,
    CanalNotificacion,
)
from app.models.user import User
from app.models.camera import Camera
from app.models.incident import Incident
from app.models.alert import Alert
from app.models.evidence import Evidence
from app.models.notification import Notification
from app.models.audit import AuditLog

__all__ = [
    "Base",
    "RolUsuario",
    "EstadoCamara",
    "TipoFuenteCamara",
    "TipoIncidente",
    "NivelRiesgo",
    "EstadoIncidente",
    "PrioridadAlerta",
    "EstadoAlerta",
    "TipoEvidencia",
    "CanalNotificacion",
    "User",
    "Camera",
    "Incident",
    "Alert",
    "Evidence",
    "Notification",
    "AuditLog",
]
