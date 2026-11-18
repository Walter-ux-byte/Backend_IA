"""
Modelo ORM para la tabla de Cámaras.
RF-01: Visualización y administración de cámaras.
RF-19: Estados de cámara (Conectada, Desconectada, Error, Reconectando).
RNF-07: Configuración dinámica de cámaras sin modificar código fuente.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.enums import EstadoCamara, TipoFuenteCamara


class Camera(Base):
    __tablename__ = "camaras"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    ubicacion = Column(String(150), nullable=False)
    rtsp_url = Column(String(500), nullable=False)
    tipo_fuente = Column(SQLEnum(TipoFuenteCamara), default=TipoFuenteCamara.RTSP, nullable=False)
    estado = Column(SQLEnum(EstadoCamara), default=EstadoCamara.DESCONECTADA, nullable=False)
    activa = Column(Boolean, default=True, nullable=False)
    fps = Column(Integer, default=25, nullable=False)
    resolucion = Column(String(20), nullable=True, default="1280x720")
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relaciones
    incidentes = relationship("Incident", back_populates="camara", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Camera(id={self.id}, nombre='{self.nombre}', estado='{self.estado}', activa={self.activa})>"
