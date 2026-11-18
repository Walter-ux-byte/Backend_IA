"""
Modelo ORM para la tabla de Alertas.
RF-08: Alertas automáticas ante situaciones potencialmente peligrosas.
RF-10: Activación y desactivación de alarmas.
RF-14: Gestión de alertas (revisar, confirmar, descartar, cerrar y registrar usuario gestor).
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.enums import PrioridadAlerta, EstadoAlerta


class Alert(Base):
    __tablename__ = "alertas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    incidente_id = Column(Integer, ForeignKey("incidentes.id", ondelete="CASCADE"), nullable=False, index=True)
    mensaje = Column(Text, nullable=False)
    prioridad = Column(SQLEnum(PrioridadAlerta), default=PrioridadAlerta.MEDIA, nullable=False)
    estado = Column(SQLEnum(EstadoAlerta), default=EstadoAlerta.ACTIVA, index=True, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)
    fecha_confirmacion = Column(DateTime(timezone=True), nullable=True)
    fecha_cierre = Column(DateTime(timezone=True), nullable=True)
    usuario_gestion_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)

    # Relaciones
    incidente = relationship("Incident", back_populates="alertas")
    usuario_gestion = relationship("User", foreign_keys=[usuario_gestion_id])
    notificaciones = relationship("Notification", back_populates="alerta", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, prioridad='{self.prioridad}', estado='{self.estado}')>"
