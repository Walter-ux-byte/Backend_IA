"""
Modelo ORM para la tabla de Notificaciones.
RF-09: Notificaciones mediante WebSockets y correo electrónico.
"""
from sqlalchemy import Column, Integer, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.enums import CanalNotificacion


class Notification(Base):
    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    alerta_id = Column(Integer, ForeignKey("alertas.id", ondelete="CASCADE"), nullable=True, index=True)
    mensaje = Column(Text, nullable=False)
    canal = Column(SQLEnum(CanalNotificacion), default=CanalNotificacion.WEBSOCKET, nullable=False)
    leida = Column(Boolean, default=False, nullable=False)
    fecha_envio = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones
    usuario = relationship("User", back_populates="notificaciones")
    alerta = relationship("Alert", back_populates="notificaciones")

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, usuario_id={self.usuario_id}, leida={self.leida})>"
