"""
Endpoints REST de Inteligencia Artificial y Visión Computacional.
RF-02, RF-03, RF-04, RF-05, RF-06, RF-07.
"""
from typing import List, Optional
import os
import shutil
import cv2
import numpy as np
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, Request, status, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_active_user, require_roles
from app.models.user import User
from app.models.enums import RolUsuario
from app.schemas.ai import FrameAnalysisResult, AIStatusResponse, AIModelInfo
from app.ai.pipeline import ai_pipeline
from app.cameras.camera_manager import camera_manager
from app.services.camera_service import CameraService
from app.core.config import settings

router = APIRouter(prefix="/api/ai", tags=["Inteligencia Artificial"])


@router.get(
    "/status",
    response_model=AIStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Estado de los motores de Inteligencia Artificial",
    description="Informa sobre la disponibilidad de Ultralytics YOLO, MediaPipe y las cámaras con análisis en vivo."
)
def get_ai_status(
    current_user: User = Depends(get_current_active_user)
) -> AIStatusResponse:
    return AIStatusResponse(
        sistema="Motor de Análisis de Seguridad con IA",
        device=settings.DEVICE,
        yolo_disponible=ai_pipeline.person_detector.is_available,
        mediapipe_disponible=ai_pipeline.pose_estimator.is_available,
        camaras_con_analisis_activo=list(ai_pipeline.enabled_camera_ids),
        metricas={
            "umbral_confianza": settings.CONFIDENCE_THRESHOLD,
            "tiempo_confirmacion_caida_s": settings.FALL_CONFIRMATION_SECONDS,
            "tiempo_umbral_inmovilidad_s": settings.INACTIVITY_THRESHOLD_SECONDS,
            "tiempo_enfriamiento_alertas_s": settings.ALERT_COOLDOWN_SECONDS
        }
    )


@router.get(
    "/models",
    response_model=List[AIModelInfo],
    status_code=status.HTTP_200_OK,
    summary="Catálogo de modelos y detectores de IA integrados",
    description="Describe los modelos disponibles, su estado operativo y requisitos de hardware."
)
def list_ai_models(
    current_user: User = Depends(get_current_active_user)
) -> List[AIModelInfo]:
    return [
        AIModelInfo(
            nombre="Ultralytics YOLOv8 Nano",
            tarea="Detección y seguimiento temporal de personas",
            tipo_modelo="Red Neuronal Convolucional (CNN)",
            estado="OPERATIVO",
            descripcion="Modelo preentrenado optimizado para detección y tracking en tiempo real de personas.",
            hardware_recomendado="CPU o GPU CUDA"
        ),
        AIModelInfo(
            nombre="Google MediaPipe Pose",
            tarea="Estimación de postura corporal y 33 keypoints",
            tipo_modelo="Red Neuronal para Puntos Anatómicos",
            estado="OPERATIVO",
            descripcion="Extrae la cinemática de torso, hombros, brazos y piernas para detectar caídas y orientación.",
            hardware_recomendado="CPU"
        ),
        AIModelInfo(
            nombre="Detector Cinemático de Caídas",
            tarea="Detección de caídas",
            tipo_modelo="Algoritmo Cinemático-Temporal Multi-Frame",
            estado="OPERATIVO",
            descripcion="Analiza velocidad de descenso del centroide, inversión de relación de aspecto y permanencia horizontal.",
            hardware_recomendado="CPU"
        ),
        AIModelInfo(
            nombre="Detector de Inmovilidad Prolongada",
            tarea="Monitoreo de personas caídas o inmóviles",
            tipo_modelo="Análisis de Dispersión Espacio-Temporal",
            estado="OPERATIVO",
            descripcion="Verifica si una persona en el suelo permanece sin desplazamiento durante un tiempo configurable.",
            hardware_recomendado="CPU"
        ),
        AIModelInfo(
            nombre="Detector de Movimientos Bruscos",
            tarea="Detección de anomalías cinéticas rápidas",
            tipo_modelo="Análisis Temporal de Velocidad y Aceleración",
            estado="OPERATIVO",
            descripcion="Evalúa cambios repentinos de aceleración en centros de masa y extremidades.",
            hardware_recomendado="CPU"
        ),
        AIModelInfo(
            nombre="Detector de Gestos de Auxilio",
            tarea="Reconocimiento de posturas de ayuda",
            tipo_modelo="Heurístico Anatómico Experimental",
            estado="EXPERIMENTAL",
            descripcion="Identifica brazos en alto sobre la cabeza o posturas de socorro. Requiere confirmación humana.",
            hardware_recomendado="CPU"
        ),
        AIModelInfo(
            nombre="Módulo de Reconocimiento de Violencia / Peleas",
            tarea="Identificación de riñas y agresiones físicas",
            tipo_modelo="Interfaz para Video Action Recognition (SlowFast / VideoMAE) + Heurística",
            estado="EXPERIMENTAL_HEURISTICO",
            descripcion="Evalúa solapamiento corporal y movimientos bruscos simultáneos. Dispone de interfaz para conectar modelos neuronales adicionales.",
            hardware_recomendado="GPU CUDA recomendada para modelos neuronales de video 3D"
        )
    ]


@router.post(
    "/analyze-image",
    response_model=FrameAnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Analizar imagen estática con IA",
    description="Sube una imagen (JPG/PNG). Detecta personas, posturas y genera señales de riesgo."
)
async def analyze_image(
    file: UploadFile = File(..., description="Archivo de imagen a analizar"),
    include_annotated: bool = Query(True, description="Incluir imagen resultante con cajas dibujadas en base64"),
    current_user: User = Depends(get_current_active_user)
) -> FrameAnalysisResult:
    # Validar extensión
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de archivo no compatible. Suba una imagen válida (.jpg, .png, etc.)."
        )

    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo decodificar la imagen enviada."
        )

    result = ai_pipeline.process_frame(frame, include_annotated_image=include_annotated)
    return result


@router.post(
    "/analyze-video",
    status_code=status.HTTP_200_OK,
    summary="Analizar archivo de video local o subido con IA",
    description="Procesa fotogramas de un video, detecta personas y reporta incidentes potenciales."
)
async def analyze_video(
    file: Optional[UploadFile] = File(None, description="Archivo MP4 a subir"),
    video_path: Optional[str] = Form(None, description="O ruta a un video ya existente en el servidor"),
    sample_rate: int = Form(5, description="Procesar 1 de cada N fotogramas para rendimiento"),
    current_user: User = Depends(get_current_active_user)
):
    target_path = None
    temp_file = False

    if file:
        temp_dir = os.path.join(settings.STORAGE_DIR, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        target_path = os.path.join(temp_dir, f"upload_{int(time.time())}_{file.filename}")
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        temp_file = True
    elif video_path:
        target_path = video_path
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe proporcionar un archivo de video o una ruta válida."
        )

    if not os.path.exists(target_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Archivo de video no encontrado en '{target_path}'."
        )

    cap = cv2.VideoCapture(target_path)
    if not cap.isOpened():
        if temp_file and os.path.exists(target_path):
            os.remove(target_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OpenCV no pudo abrir el archivo de video especificado."
        )

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

    frame_idx = 0
    frames_processed = 0
    all_signals = []
    max_persons = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            if frame_idx % max(1, sample_rate) == 0:
                res = ai_pipeline.process_frame(frame)
                frames_processed += 1
                max_persons = max(max_persons, res.num_personas)
                for sig in res.senales_riesgo:
                    all_signals.append({
                        "frame": frame_idx,
                        "segundo": round(frame_idx / fps, 2),
                        "tipo": sig.tipo,
                        "confianza": sig.confianza,
                        "detalles": sig.detalles
                    })

            frame_idx += 1
            if frames_processed >= 100:  # Limitar muestra para no bloquear la petición
                break
    finally:
        cap.release()
        if temp_file and os.path.exists(target_path):
            try:
                os.remove(target_path)
            except Exception:
                pass

    return {
        "archivo": os.path.basename(target_path),
        "total_fotogramas_video": total_frames,
        "fotogramas_analizados": frames_processed,
        "max_personas_detectadas": max_persons,
        "incidentes_identificados": all_signals,
        "resumen": f"Se procesaron {frames_processed} fotogramas. Se detectaron {len(all_signals)} eventos potenciales."
    }


@router.post(
    "/cameras/{camera_id}/enable",
    status_code=status.HTTP_200_OK,
    summary="Activar análisis de IA en tiempo real para una cámara",
    description="Conecta el pipeline de inferencia con el stream continuo de la cámara."
)
def enable_camera_ai(
    camera_id: int,
    current_user: User = Depends(require_roles([RolUsuario.ADMINISTRADOR, RolUsuario.SEGURIDAD])),
    db: Session = Depends(get_db)
):
    CameraService(db).get_by_id(camera_id)
    ai_pipeline.enable_camera(camera_id)

    # Registrar el callback en el procesador de stream si está corriendo
    processor = camera_manager.get_processor(camera_id)
    if processor:
        processor.register_ai_callback(
            lambda frame, cid: ai_pipeline.process_frame(frame, camera_id=cid)
        )

    return {"message": f"Análisis de Inteligencia Artificial activado para cámara {camera_id}."}


@router.post(
    "/cameras/{camera_id}/disable",
    status_code=status.HTTP_200_OK,
    summary="Desactivar análisis de IA para una cámara",
    description="Detiene la ejecución del pipeline de inferencia para ahorrar recursos de cómputo."
)
def disable_camera_ai(
    camera_id: int,
    current_user: User = Depends(require_roles([RolUsuario.ADMINISTRADOR, RolUsuario.SEGURIDAD])),
    db: Session = Depends(get_db)
):
    CameraService(db).get_by_id(camera_id)
    ai_pipeline.disable_camera(camera_id)
    return {"message": f"Análisis de Inteligencia Artificial desactivado para cámara {camera_id}."}
