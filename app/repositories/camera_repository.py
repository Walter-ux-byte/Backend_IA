"""
Repositorio para operaciones de base de datos sobre la entidad Cámara.
"""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models.camera import Camera
from app.models.enums import EstadoCamara
from app.schemas.camera import CameraCreate, CameraUpdate


class CameraRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, camera_id: int) -> Optional[Camera]:
        return self.db.query(Camera).filter(Camera.id == camera_id).first()

    def get_by_name(self, name: str) -> Optional[Camera]:
        return self.db.query(Camera).filter(Camera.nombre == name.strip()).first()

    def get_paginated(
        self,
        skip: int = 0,
        limit: int = 20,
        activa: Optional[bool] = None,
        estado: Optional[EstadoCamara] = None
    ) -> Tuple[List[Camera], int]:
        query = self.db.query(Camera)
        if activa is not None:
            query = query.filter(Camera.activa == activa)
        if estado is not None:
            query = query.filter(Camera.estado == estado)

        total = query.count()
        cameras = query.order_by(Camera.id.asc()).offset(skip).limit(limit).all()
        return cameras, total

    def create(self, camera_in: CameraCreate) -> Camera:
        camera = Camera(
            nombre=camera_in.nombre.strip(),
            ubicacion=camera_in.ubicacion.strip(),
            rtsp_url=camera_in.rtsp_url.strip(),
            tipo_fuente=camera_in.tipo_fuente,
            estado=EstadoCamara.DESCONECTADA,
            activa=camera_in.activa,
            fps=camera_in.fps,
            resolucion=camera_in.resolucion
        )
        self.db.add(camera)
        self.db.commit()
        self.db.refresh(camera)
        return camera

    def update(self, camera: Camera, camera_in: CameraUpdate) -> Camera:
        if camera_in.nombre is not None:
            camera.nombre = camera_in.nombre.strip()
        if camera_in.ubicacion is not None:
            camera.ubicacion = camera_in.ubicacion.strip()
        if camera_in.rtsp_url is not None:
            camera.rtsp_url = camera_in.rtsp_url.strip()
        if camera_in.tipo_fuente is not None:
            camera.tipo_fuente = camera_in.tipo_fuente
        if camera_in.fps is not None:
            camera.fps = camera_in.fps
        if camera_in.resolucion is not None:
            camera.resolucion = camera_in.resolucion
        if camera_in.activa is not None:
            camera.activa = camera_in.activa

        self.db.commit()
        self.db.refresh(camera)
        return camera

    def update_status(self, camera_id: int, estado: EstadoCamara) -> Optional[Camera]:
        camera = self.get_by_id(camera_id)
        if camera:
            camera.estado = estado
            self.db.commit()
            self.db.refresh(camera)
        return camera

    def soft_delete(self, camera: Camera) -> Camera:
        """Desactiva la cámara y marca su estado como Desconectada."""
        camera.activa = False
        camera.estado = EstadoCamara.DESCONECTADA
        self.db.commit()
        self.db.refresh(camera)
        return camera

    def delete(self, camera: Camera) -> None:
        """Eliminación física de la cámara."""
        self.db.delete(camera)
        self.db.commit()
