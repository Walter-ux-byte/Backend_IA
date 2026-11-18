"""
Modelo ORM para la tabla de Usuarios.
RF-16: Gestión de usuarios con roles ADMINISTRADOR, SEGURIDAD y SUPERVISOR.
RF-17: Autenticación con contraseña cifrada y estado activo.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.enums import RolUsuario


class User(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    correo = Column(String(150), unique=True, index=True, nullable=False)
    usuario = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol = Column(SQLEnum(RolUsuario), nullable=False, default=RolUsuario.SEGURIDAD)
    activo = Column(Boolean, default=True, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones
    incidentes_asignados = relationship("Incident", back_populates="usuario_asignado", foreign_keys="Incident.usuario_asignado_id")
    notificaciones = relationship("Notification", back_populates="usuario", cascade="all, delete-orphan")
    auditorias = relationship("AuditLog", back_populates="usuario")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, usuario='{self.usuario}', rol='{self.rol}', activo={self.activo})>"
