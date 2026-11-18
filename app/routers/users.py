"""
Endpoints REST para la Administración y CRUD de Usuarios.
RF-16: Operaciones protegidas por roles (ADMINISTRADOR, SEGURIDAD, SUPERVISOR).
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_active_user, require_roles
from app.models.user import User
from app.models.enums import RolUsuario
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse
)
from app.services.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["Gestión de Usuarios"])


@router.get(
    "",
    response_model=UserListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar usuarios con paginación y filtros",
    description="Permitido para ADMINISTRADOR y SUPERVISOR. Permite filtrar por rol y estado activo."
)
def list_users(
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(20, ge=1, le=100, description="Cantidad de registros por página"),
    rol: Optional[RolUsuario] = Query(None, description="Filtrar por rol"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    current_user: User = Depends(require_roles([RolUsuario.ADMINISTRADOR, RolUsuario.SUPERVISOR])),
    db: Session = Depends(get_db)
) -> UserListResponse:
    user_service = UserService(db)
    return user_service.list_users(page=page, size=size, rol=rol, activo=activo)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo usuario",
    description="Exclusivo para ADMINISTRADOR. Registra el usuario con contraseña cifrada y rol especificado."
)
def create_user(
    body: UserCreate,
    request: Request,
    current_user: User = Depends(require_roles([RolUsuario.ADMINISTRADOR])),
    db: Session = Depends(get_db)
) -> UserResponse:
    user_service = UserService(db)
    client_ip = request.client.host if request.client else None
    new_user = user_service.create_user(body, current_user=current_user, client_ip=client_ip)
    return UserResponse.model_validate(new_user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener detalle de un usuario por ID",
    description="Accesible para ADMINISTRADOR, SUPERVISOR o el propio usuario autenticado."
)
def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    # Si no es admin ni supervisor, solo puede consultar su propio perfil
    if current_user.rol not in [RolUsuario.ADMINISTRADOR, RolUsuario.SUPERVISOR] and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene autorización para consultar los datos de otro usuario."
        )

    user_service = UserService(db)
    user = user_service.get_by_id(user_id)
    return UserResponse.model_validate(user)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar información de un usuario",
    description="Exclusivo para ADMINISTRADOR. Permite modificar nombres, correo, rol, estado activo y contraseña."
)
def update_user(
    user_id: int,
    body: UserUpdate,
    request: Request,
    current_user: User = Depends(require_roles([RolUsuario.ADMINISTRADOR])),
    db: Session = Depends(get_db)
) -> UserResponse:
    user_service = UserService(db)
    client_ip = request.client.host if request.client else None
    updated = user_service.update_user(user_id, body, current_user=current_user, client_ip=client_ip)
    return UserResponse.model_validate(updated)


@router.delete(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Eliminación lógica de un usuario",
    description="Exclusivo para ADMINISTRADOR. Desactiva la cuenta del usuario sin eliminar su historial."
)
def delete_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_roles([RolUsuario.ADMINISTRADOR])),
    db: Session = Depends(get_db)
) -> UserResponse:
    user_service = UserService(db)
    client_ip = request.client.host if request.client else None
    deleted = user_service.soft_delete_user(user_id, current_user=current_user, client_ip=client_ip)
    return UserResponse.model_validate(deleted)
