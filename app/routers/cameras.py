"""
Endpoints REST para la Administración y Transmisión de Cámaras.
RF-01: Visualización y streaming en tiempo real (MJPEG).
RF-19: Estados de cámara y reconexión automática.
RNF-04: Protección de rutas según roles.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_active_user, require_roles
from app.models.user import User
from app.models.enums import RolUsuario, EstadoCamara
from app.schemas.camera import (
    CameraCreate,
    CameraUpdate,
    CameraResponse,
    CameraListResponse,
    CameraStatusResponse
)
from app.services.camera_service import CameraService
from app.cameras.camera_manager import camera_manager
from app.core.security import decode_token, is_token_revoked
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/api/cameras", tags=["Gestión de Cámaras"])


@router.get(
    "",
    response_model=CameraListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar cámaras registradas",
    description="Permitido para ADMINISTRADOR, SUPERVISOR y SEGURIDAD. Paginación y filtros por estado y activación."
)
def list_cameras(
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(20, ge=1, le=100, description="Cantidad por página"),
    activa: Optional[bool] = Query(None, description="Filtrar por cámara activa"),
    estado: Optional[EstadoCamara] = Query(None, description="Filtrar por estado de conexión"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> CameraListResponse:
    service = CameraService(db)
    is_admin = current_user.rol == RolUsuario.ADMINISTRADOR
    return service.list_cameras(page=page, size=size, activa=activa, estado=estado, is_admin=is_admin)


@router.post(
    "",
    response_model=CameraResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una nueva cámara",
    description="Exclusivo para ADMINISTRADOR. Registra una fuente WEBCAM, MP4 o RTSP."
)
def create_camera(
    body: CameraCreate,
    request: Request,
    current_user: User = Depends(require_roles([RolUsuario.ADMINISTRADOR])),
    db: Session = Depends(get_db)
) -> CameraResponse:
    service = CameraService(db)
    client_ip = request.client.host if request.client else None
    return service.create_camera(body, current_user=current_user, client_ip=client_ip)


@router.get(
    "/{camera_id}",
    response_model=CameraResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener detalle de una cámara por ID",
    description="Permitido para ADMINISTRADOR, SUPERVISOR y SEGURIDAD."
)
def get_camera_by_id(
    camera_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> CameraResponse:
    service = CameraService(db)
    is_admin = current_user.rol == RolUsuario.ADMINISTRADOR
    return service.get_by_id(camera_id, is_admin=is_admin)


@router.put(
    "/{camera_id}",
    response_model=CameraResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar información de una cámara",
    description="Exclusivo para ADMINISTRADOR. Modifica nombre, ubicación, URL, FPS o resolución."
)
def update_camera(
    camera_id: int,
    body: CameraUpdate,
    request: Request,
    current_user: User = Depends(require_roles([RolUsuario.ADMINISTRADOR])),
    db: Session = Depends(get_db)
) -> CameraResponse:
    service = CameraService(db)
    client_ip = request.client.host if request.client else None
    return service.update_camera(camera_id, body, current_user=current_user, client_ip=client_ip)


@router.delete(
    "/{camera_id}",
    response_model=CameraResponse,
    status_code=status.HTTP_200_OK,
    summary="Desactivar una cámara (Eliminación lógica)",
    description="Exclusivo para ADMINISTRADOR. Detiene la captura si está activa y desactiva la cámara."
)
def delete_camera(
    camera_id: int,
    request: Request,
    current_user: User = Depends(require_roles([RolUsuario.ADMINISTRADOR])),
    db: Session = Depends(get_db)
) -> CameraResponse:
    service = CameraService(db)
    client_ip = request.client.host if request.client else None
    return service.soft_delete_camera(camera_id, current_user=current_user, client_ip=client_ip)


@router.get(
    "/{camera_id}/status",
    response_model=CameraStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar estado y telemetría de la cámara",
    description="Devuelve estado (Conectada, Reconectando, Error, Desconectada), FPS y latencia real."
)
def get_camera_status(
    camera_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> CameraStatusResponse:
    service = CameraService(db)
    return service.get_status(camera_id)


@router.post(
    "/{camera_id}/start",
    response_model=CameraStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Iniciar captura y procesamiento de video",
    description="Exclusivo para ADMINISTRADOR. Arranca el procesador en segundo plano para la cámara."
)
def start_camera(
    camera_id: int,
    request: Request,
    current_user: User = Depends(require_roles([RolUsuario.ADMINISTRADOR])),
    db: Session = Depends(get_db)
) -> CameraStatusResponse:
    service = CameraService(db)
    client_ip = request.client.host if request.client else None
    return service.start_camera(camera_id, current_user=current_user, client_ip=client_ip)


@router.post(
    "/{camera_id}/stop",
    response_model=CameraStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Detener captura de video",
    description="Exclusivo para ADMINISTRADOR. Detiene el hilo de procesamiento de la cámara."
)
def stop_camera(
    camera_id: int,
    request: Request,
    current_user: User = Depends(require_roles([RolUsuario.ADMINISTRADOR])),
    db: Session = Depends(get_db)
) -> CameraStatusResponse:
    service = CameraService(db)
    client_ip = request.client.host if request.client else None
    return service.stop_camera(camera_id, current_user=current_user, client_ip=client_ip)


@router.get(
    "/{camera_id}/stream",
    status_code=status.HTTP_200_OK,
    summary="Transmisión en vivo MJPEG",
    description="Transmite el flujo de video en tiempo real. Admite token Bearer en cabecera o como parámetro ?token=... para tags HTML5 / React."
)
def stream_camera(
    camera_id: int,
    token: Optional[str] = Query(None, description="Token JWT para clientes que no soportan cabeceras en tags de imagen"),
    max_frames: Optional[int] = Query(None, description="Límite opcional de fotogramas a transmitir"),
    db: Session = Depends(get_db)
):
    # Validar que la cámara exista
    service = CameraService(db)
    service.get_by_id(camera_id)

    # Si se pasa token por query param, validar autenticación
    if token:
        try:
            if is_token_revoked(token):
                raise HTTPException(status_code=401, detail="Token revocado")
            payload = decode_token(token)
            user_id = payload.get("user_id")
            user = UserRepository(db).get_by_id(user_id)
            if not user or not user.activo:
                raise HTTPException(status_code=401, detail="Usuario inactivo o no encontrado")
        except Exception:
            raise HTTPException(status_code=401, detail="Token inválido o expirado para streaming")

    return StreamingResponse(
        camera_manager.generate_mjpeg_stream(camera_id, max_frames=max_frames),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
