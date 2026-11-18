"""
Modelo ORM para la tabla de Auditoría.
RNF-04: Registro inmutable de acciones administrativas y de seguridad.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    accion = Column(String(50), nullable=False, index=True)
    entidad = Column(String(50), nullable=False, index=True)
    entidad_id = Column(Integer, nullable=True)
    detalles = Column(Text, nullable=True)
    ip_origen = Column(String(45), nullable=True)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)

    # Relaciones
    usuario = relationship("User", back_populates="auditorias")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, accion='{self.accion}', entidad='{self.entidad}', fecha='{self.fecha_hora}')>"
