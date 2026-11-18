"""
Modelo ORM para la tabla de Incidentes.
RF-11: Información del incidente (fecha, hora, cámara, ubicación, tipo, nivel de riesgo, estado).
RF-15: Clasificación en categorías.
RF-18: Asignación de emergencias a personal de seguridad.
"""
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.enums import TipoIncidente, NivelRiesgo, EstadoIncidente


class Incident(Base):
    __tablename__ = "incidentes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camara_id = Column(Integer, ForeignKey("camaras.id", ondelete="SET NULL"), nullable=True, index=True)
    tipo = Column(SQLEnum(TipoIncidente), nullable=False, index=True)
    descripcion = Column(Text, nullable=True)
    nivel_riesgo = Column(SQLEnum(NivelRiesgo), default=NivelRiesgo.MEDIO, nullable=False)
    confianza = Column(Float, default=0.0, nullable=False)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)
    estado = Column(SQLEnum(EstadoIncidente), default=EstadoIncidente.PENDIENTE, index=True, nullable=False)
    usuario_asignado_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    es_simulado = Column(Boolean, default=False, nullable=False)

    # Relaciones
    camara = relationship("Camera", back_populates="incidentes")
    usuario_asignado = relationship("User", back_populates="incidentes_asignados", foreign_keys=[usuario_asignado_id])
    alertas = relationship("Alert", back_populates="incidente", cascade="all, delete-orphan")
    evidencias = relationship("Evidence", back_populates="incidente", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Incident(id={self.id}, tipo='{self.tipo}', riesgo='{self.nivel_riesgo}', estado='{self.estado}')>"
