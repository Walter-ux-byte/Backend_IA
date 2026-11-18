"""
Esquemas Pydantic para el módulo de Inteligencia Artificial y Visión Computacional.
RF-02, RF-03, RF-04, RF-05, RF-06, RF-07.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    track_id: Optional[int] = None


class Keypoint(BaseModel):
    id: int
    name: str
    x: float
    y: float
    z: float
    visibility: float


class PersonDetection(BaseModel):
    person_id: int
    box: BoundingBox
    torso_angle: Optional[float] = None
    posture: str = "VERTICAL"
    keypoints: Optional[List[Keypoint]] = None


class IncidentSignal(BaseModel):
    tipo: str
    detectado: bool
    confianza: float
    detalles: Optional[str] = None
    es_heuristico: bool = False


class FrameAnalysisResult(BaseModel):
    timestamp: str
    camera_id: Optional[int] = None
    num_personas: int
    personas: List[PersonDetection]
    senales_riesgo: List[IncidentSignal]
    latencia_ms: float
    imagen_anotada_b64: Optional[str] = None


class AIStatusResponse(BaseModel):
    sistema: str
    device: str
    yolo_disponible: bool
    mediapipe_disponible: bool
    camaras_con_analisis_activo: List[int]
    metricas: Dict[str, Any]


class AIModelInfo(BaseModel):
    nombre: str
    tarea: str
    tipo_modelo: str
    estado: str  # OPERATIVO, EXPERIMENTAL, PENDIENTE_ENTRENAMIENTO
    descripcion: str
    hardware_recomendado: str
