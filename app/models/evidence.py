"""
Modelo ORM para la tabla de Evidencias.
RF-12: Almacenamiento seguro de capturas y clips asociados a incidentes.
RNF-04: Control de acceso, rutas seguras e integridad con hash SHA-256.
"""
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.enums import TipoEvidencia


class Evidence(Base):
    __tablename__ = "evidencias"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    incidente_id = Column(Integer, ForeignKey("incidentes.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo_archivo = Column(SQLEnum(TipoEvidencia), nullable=False)
    ruta_archivo = Column(String(500), nullable=False)
    tamano_bytes = Column(BigInteger, nullable=True)
    hash_sha256 = Column(String(64), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones
    incidente = relationship("Incident", back_populates="evidencias")

    def __repr__(self) -> str:
        return f"<Evidence(id={self.id}, tipo='{self.tipo_archivo}', ruta='{self.ruta_archivo}')>"
