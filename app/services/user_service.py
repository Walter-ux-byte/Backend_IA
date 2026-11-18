"""
Servicio de Lógica de Negocio para la Gestión de Usuarios.
RF-16: Operaciones CRUD con reglas de negocio, validaciones y auditoría.
"""
import math
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.enums import RolUsuario
from app.schemas.user import UserCreate, UserUpdate, UserListResponse, UserResponse
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.core.security import get_password_hash


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)

    def list_users(
        self,
        page: int = 1,
        size: int = 20,
        rol: Optional[RolUsuario] = None,
        activo: Optional[bool] = None
    ) -> UserListResponse:
        page = max(1, page)
        size = max(1, min(100, size))
        skip = (page - 1) * size

        items, total = self.repo.get_paginated(skip=skip, limit=size, rol=rol, activo=activo)
        pages = math.ceil(total / size) if total > 0 else 1

        return UserListResponse(
            items=[UserResponse.model_validate(u) for u in items],
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    def get_by_id(self, user_id: int) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con ID {user_id} no encontrado."
            )
        return user

    def create_user(self, user_in: UserCreate, current_user: User, client_ip: Optional[str] = None) -> User:
        # Validar unicidad de username
        if self.repo.get_by_username(user_in.usuario):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El nombre de usuario '{user_in.usuario}' ya se encuentra registrado."
            )

        # Validar unicidad de correo
        if self.repo.get_by_email(user_in.correo):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El correo electrónico '{user_in.correo}' ya está en uso."
            )

        pwd_hash = get_password_hash(user_in.password)
        new_user = self.repo.create(user_in, pwd_hash)

        # Auditoría
        AuditService.log_event(
            db=self.db,
            accion="CREAR_USUARIO",
            entidad="usuarios",
            entidad_id=new_user.id,
            usuario_id=current_user.id,
            detalles=f"Usuario '{new_user.usuario}' creado con rol '{new_user.rol.value}'.",
            ip_origen=client_ip
        )

        return new_user

    def update_user(
        self,
        user_id: int,
        user_in: UserUpdate,
        current_user: User,
        client_ip: Optional[str] = None
    ) -> User:
        target_user = self.get_by_id(user_id)

        # Si actualiza correo, validar duplicado
        if user_in.correo and user_in.correo.lower() != target_user.correo:
            existing = self.repo.get_by_email(user_in.correo)
            if existing and existing.id != target_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El correo electrónico '{user_in.correo}' ya pertenece a otro usuario."
                )

        new_pwd_hash = None
        if user_in.password:
            new_pwd_hash = get_password_hash(user_in.password)

        updated_user = self.repo.update(target_user, user_in, new_pwd_hash)

        AuditService.log_event(
            db=self.db,
            accion="ACTUALIZAR_USUARIO",
            entidad="usuarios",
            entidad_id=updated_user.id,
            usuario_id=current_user.id,
            detalles=f"Usuario '{updated_user.usuario}' actualizado por '{current_user.usuario}'.",
            ip_origen=client_ip
        )

        return updated_user

    def soft_delete_user(self, user_id: int, current_user: User, client_ip: Optional[str] = None) -> User:
        target_user = self.get_by_id(user_id)

        # Evitar que el administrador se auto-desactive
        if target_user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un administrador no puede desactivar su propia cuenta de acceso."
            )

        deleted_user = self.repo.soft_delete(target_user)

        AuditService.log_event(
            db=self.db,
            accion="DESACTIVAR_USUARIO",
            entidad="usuarios",
            entidad_id=deleted_user.id,
            usuario_id=current_user.id,
            detalles=f"Usuario '{deleted_user.usuario}' desactivado lógicamente por '{current_user.usuario}'.",
            ip_origen=client_ip
        )

        return deleted_user
