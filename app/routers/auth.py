"""
Endpoints REST de Autenticación y Gestión de Sesiones JWT.
RF-17: /api/auth/login, /api/auth/refresh, /api/auth/logout, /api/auth/me, /api/auth/change-password.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Request, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_active_user, oauth2_scheme
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    ChangePasswordRequest,
    LogoutResponse,
    UserResponse
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Autenticación y Sesiones"])


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión y obtener tokens JWT",
    description="Permite autenticarse mediante nombre de usuario o correo electrónico. Compatible con Swagger UI y clientes JSON."
)
async def login(
    request: Request,
    db: Session = Depends(get_db)
) -> TokenResponse:
    auth_service = AuthService(db)
    client_ip = request.client.host if request.client else None

    # Detectar si la petición proviene de un formulario OAuth2 (Swagger) o de un JSON
    content_type = request.headers.get("content-type", "")

    if "application/x-www-form-urlencoded" in content_type:
        form_data = await request.form()
        username = form_data.get("username")
        password = form_data.get("password")
        if not username or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campos 'username' y 'password' requeridos."
            )
        identifier = str(username)
        pwd = str(password)
    else:
        try:
            body = await request.json()
            login_data = LoginRequest(**body)
            identifier = login_data.username
            pwd = login_data.password
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato de solicitud JSON inválido: {str(e)}"
            )

    return auth_service.login(
        identifier=identifier,
        password=pwd,
        client_ip=client_ip
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Renovar token de acceso con refresh token",
    description="Emite un nuevo par de access_token y refresh_token, revocando el refresh_token utilizado."
)
def refresh_token(
    body: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> TokenResponse:
    auth_service = AuthService(db)
    client_ip = request.client.host if request.client else None
    return auth_service.refresh_access_token(body.refresh_token, client_ip=client_ip)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Cerrar sesión e invalidar token",
    description="Revoca el token JWT actual y registra la salida en el log de auditoría."
)
def logout(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> LogoutResponse:
    auth_service = AuthService(db)
    client_ip = request.client.host if request.client else None
    if token:
        auth_service.logout(token, current_user, client_ip=client_ip)
    return LogoutResponse()


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener perfil del usuario autenticado",
    description="Devuelve la información y rol del usuario correspondiente al token Bearer provisto."
)
def get_me(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Cambiar contraseña del usuario actual",
    description="Permite actualizar la contraseña actual por una nueva contraseña segura."
)
def change_password(
    body: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    auth_service = AuthService(db)
    client_ip = request.client.host if request.client else None
    auth_service.change_password(
        user=current_user,
        current_password=body.current_password,
        new_password=body.new_password,
        client_ip=client_ip
    )
    return {"message": "Contraseña actualizada exitosamente."}
