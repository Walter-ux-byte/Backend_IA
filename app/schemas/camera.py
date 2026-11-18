"""
Esquemas Pydantic para la gestión y monitoreo de Cámaras.
RF-01: Registro y administración de cámaras.
RF-19: Estados de cámara y telemetría.
"""
from datetime import datetime
from typing import Optional, List
import re
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.models.enums import EstadoCamara, TipoFuenteCamara


def mask_rtsp_credentials(url: str) -> str:
    """Enmascara contraseñas en URLs RTSP para seguridad (ej. rtsp://user:***@host)."""
    if "rtsp://" in url and "@" in url:
        return re.sub(r"://([^:@]+):([^@]+)@", r"://\1:******@", url)
    return url


class CameraBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, examples=["Cámara Pasillo Central"])
    ubicacion: str = Field(..., min_length=2, max_length=150, examples=["Pabellón A - Piso 1"])
    rtsp_url: str = Field(..., min_length=1, max_length=500, description="URL RTSP, ruta de archivo MP4 o índice de Webcam ('0')", examples=["0"])
    tipo_fuente: TipoFuenteCamara = Field(default=TipoFuenteCamara.RTSP, examples=[TipoFuenteCamara.WEBCAM])
    fps: int = Field(default=25, ge=1, le=60, description="Cuadros por segundo objetivo", examples=[25])
    resolucion: Optional[str] = Field(default="1280x720", max_length=20, examples=["1280x720"])
    activa: bool = Field(default=True)


class CameraCreate(CameraBase):
    pass


class CameraUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    ubicacion: Optional[str] = Field(None, min_length=2, max_length=150)
    rtsp_url: Optional[str] = Field(None, min_length=1, max_length=500)
    tipo_fuente: Optional[TipoFuenteCamara] = None
    fps: Optional[int] = Field(None, ge=1, le=60)
    resolucion: Optional[str] = Field(None, max_length=20)
    activa: Optional[bool] = None


class CameraResponse(BaseModel):
    id: int
    nombre: str
    ubicacion: str
    rtsp_url: str
    tipo_fuente: TipoFuenteCamara
    estado: EstadoCamara
    activa: bool
    fps: int
    resolucion: Optional[str] = None
    fecha_registro: datetime
    fecha_actualizacion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CameraStatusResponse(BaseModel):
    id: int
    nombre: str
    estado: EstadoCamara
    activa: bool
    fps_actual: float
    latencia_ms: float
    frames_procesados: int
    reconexiones: int
    captura_activa: bool
    ultimo_error: Optional[str] = None


class CameraListResponse(BaseModel):
    items: List[CameraResponse]
    total: int
    page: int
    size: int
    pages: int
