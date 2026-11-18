"""
Servicio de Lógica de Negocio para la Administración y Monitoreo de Cámaras.
RF-01, RF-19, RNF-04, RNF-06, RNF-07.
"""
import math
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.camera import Camera
from app.models.user import User
from app.models.enums import EstadoCamara, TipoFuenteCamara
from app.schemas.camera import (
    CameraCreate,
    CameraUpdate,
    CameraResponse,
    CameraListResponse,
    CameraStatusResponse,
    mask_rtsp_credentials
)
from app.repositories.camera_repository import CameraRepository
from app.services.audit_service import AuditService
from app.cameras.camera_manager import camera_manager


class CameraService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CameraRepository(db)

    def list_cameras(
        self,
        page: int = 1,
        size: int = 20,
        activa: Optional[bool] = None,
        estado: Optional[EstadoCamara] = None,
        is_admin: bool = False
    ) -> CameraListResponse:
        page = max(1, page)
        size = max(1, min(100, size))
        skip = (page - 1) * size

        items, total = self.repo.get_paginated(skip=skip, limit=size, activa=activa, estado=estado)
        pages = math.ceil(total / size) if total > 0 else 1

        formatted = []
        for cam in items:
            cam_dict = CameraResponse.model_validate(cam)
            if not is_admin:
                cam_dict.rtsp_url = mask_rtsp_credentials(cam_dict.rtsp_url)
            formatted.append(cam_dict)

        return CameraListResponse(
            items=formatted,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    def get_by_id(self, camera_id: int, is_admin: bool = False) -> CameraResponse:
        camera = self.repo.get_by_id(camera_id)
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cámara con ID {camera_id} no encontrada."
            )
        cam_res = CameraResponse.model_validate(camera)
        if not is_admin:
            cam_res.rtsp_url = mask_rtsp_credentials(cam_res.rtsp_url)
        return cam_res

    def create_camera(self, camera_in: CameraCreate, current_user: User, client_ip: Optional[str] = None) -> CameraResponse:
        existing = self.repo.get_by_name(camera_in.nombre)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una cámara registrada con el nombre '{camera_in.nombre}'."
            )

        new_cam = self.repo.create(camera_in)

        AuditService.log_event(
            db=self.db,
            accion="CREAR_CAMARA",
            entidad="camaras",
            entidad_id=new_cam.id,
            usuario_id=current_user.id,
            detalles=f"Cámara '{new_cam.nombre}' registrada en '{new_cam.ubicacion}' ({new_cam.tipo_fuente.value}).",
            ip_origen=client_ip
        )

        return CameraResponse.model_validate(new_cam)

    def update_camera(
        self,
        camera_id: int,
        camera_in: CameraUpdate,
        current_user: User,
        client_ip: Optional[str] = None
    ) -> CameraResponse:
        camera = self.repo.get_by_id(camera_id)
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cámara con ID {camera_id} no encontrada."
            )

        if camera_in.nombre and camera_in.nombre != camera.nombre:
            existing = self.repo.get_by_name(camera_in.nombre)
            if existing and existing.id != camera.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya existe otra cámara con el nombre '{camera_in.nombre}'."
                )

        updated_cam = self.repo.update(camera, camera_in)

        AuditService.log_event(
            db=self.db,
            accion="ACTUALIZAR_CAMARA",
            entidad="camaras",
            entidad_id=updated_cam.id,
            usuario_id=current_user.id,
            detalles=f"Cámara '{updated_cam.nombre}' actualizada.",
            ip_origen=client_ip
        )

        return CameraResponse.model_validate(updated_cam)

    def soft_delete_camera(
        self,
        camera_id: int,
        current_user: User,
        client_ip: Optional[str] = None
    ) -> CameraResponse:
        camera = self.repo.get_by_id(camera_id)
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cámara con ID {camera_id} no encontrada."
            )

        # Detener la captura activa si existe
        camera_manager.stop_camera(camera_id)

        deleted_cam = self.repo.soft_delete(camera)

        AuditService.log_event(
            db=self.db,
            accion="DESACTIVAR_CAMARA",
            entidad="camaras",
            entidad_id=deleted_cam.id,
            usuario_id=current_user.id,
            detalles=f"Cámara '{deleted_cam.nombre}' desactivada.",
            ip_origen=client_ip
        )

        return CameraResponse.model_validate(deleted_cam)

    def start_camera(
        self,
        camera_id: int,
        current_user: User,
        client_ip: Optional[str] = None
    ) -> CameraStatusResponse:
        camera = self.repo.get_by_id(camera_id)
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cámara con ID {camera_id} no encontrada."
            )

        if not camera.activa:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La cámara '{camera.nombre}' está desactivada. Actívela antes de iniciar captura."
            )

        camera_manager.start_camera(
            camera_id=camera.id,
            source=camera.rtsp_url,
            source_type=camera.tipo_fuente,
            target_fps=camera.fps
        )

        AuditService.log_event(
            db=self.db,
            accion="INICIAR_CAPTURA_CAMARA",
            entidad="camaras",
            entidad_id=camera.id,
            usuario_id=current_user.id,
            detalles=f"Captura de video iniciada para cámara '{camera.nombre}'.",
            ip_origen=client_ip
        )

        return self.get_status(camera_id)

    def stop_camera(
        self,
        camera_id: int,
        current_user: User,
        client_ip: Optional[str] = None
    ) -> CameraStatusResponse:
        camera = self.repo.get_by_id(camera_id)
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cámara con ID {camera_id} no encontrada."
            )

        camera_manager.stop_camera(camera_id)

        AuditService.log_event(
            db=self.db,
            accion="DETENER_CAPTURA_CAMARA",
            entidad="camaras",
            entidad_id=camera.id,
            usuario_id=current_user.id,
            detalles=f"Captura de video detenida para cámara '{camera.nombre}'.",
            ip_origen=client_ip
        )

        return self.get_status(camera_id)

    def get_status(self, camera_id: int) -> CameraStatusResponse:
        camera = self.repo.get_by_id(camera_id)
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cámara con ID {camera_id} no encontrada."
            )

        telemetry = camera_manager.get_status(camera_id)

        return CameraStatusResponse(
            id=camera.id,
            nombre=camera.nombre,
            estado=telemetry["estado"],
            activa=camera.activa,
            fps_actual=telemetry["fps_actual"],
            latencia_ms=telemetry["latencia_ms"],
            frames_procesados=telemetry["frames_procesados"],
            reconexiones=telemetry["reconexiones"],
            captura_activa=telemetry["captura_activa"],
            ultimo_error=telemetry["ultimo_error"]
        )
