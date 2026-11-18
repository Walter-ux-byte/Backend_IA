"""
Esquemas de respuesta para los endpoints de salud del sistema.
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., description="Estado general del servicio", examples=["healthy"])
    environment: str = Field(..., description="Entorno de ejecución", examples=["development"])
    version: str = Field(..., description="Versión del backend", examples=["1.0.0"])
    timestamp: str = Field(..., description="Marca de tiempo ISO-8601")


class ReadinessResponse(BaseModel):
    status: str = Field(..., description="Estado de preparación para recibir tráfico", examples=["ready"])
    database: Dict[str, Any] = Field(..., description="Estado de conectividad con PostgreSQL")
    storage: Dict[str, Any] = Field(..., description="Estado de los directorios de almacenamiento")
    details: Optional[Dict[str, Any]] = None
