"""
Servicio de Lógica de Negocio para Autenticación, JWT y Control de Sesiones.
RF-17: Login seguro, expiración, refresh tokens revocables y auditoría.
"""
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import jwt

from app.models.user import User
from app.schemas.auth import TokenResponse, UserResponse
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    revoke_token,
    is_token_revoked,
)
from app.core.config import settings


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)

    def login(self, identifier: str, password: str, client_ip: Optional[str] = None) -> TokenResponse:
        user = self.repo.get_by_identifier(identifier)

        if not user:
            AuditService.log_event(
                db=self.db,
                accion="LOGIN_FALLIDO",
                entidad="usuarios",
                detalles=f"Intento de acceso fallido: identificador '{identifier}' no existe.",
                ip_origen=client_ip
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales de acceso incorrectas.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.activo:
            AuditService.log_event(
                db=self.db,
                accion="LOGIN_BLOQUEADO",
                entidad="usuarios",
                entidad_id=user.id,
                usuario_id=user.id,
                detalles=f"Acceso denegado: cuenta de usuario '{user.usuario}' está inactiva.",
                ip_origen=client_ip
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Esta cuenta de usuario ha sido desactivada. Contacte al personal administrador.",
            )

        if not verify_password(password, user.password_hash):
            AuditService.log_event(
                db=self.db,
                accion="LOGIN_FALLIDO",
                entidad="usuarios",
                entidad_id=user.id,
                usuario_id=user.id,
                detalles=f"Intento de acceso fallido: contraseña incorrecta para usuario '{user.usuario}'.",
                ip_origen=client_ip
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales de acceso incorrectas.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Generar tokens
        access_token = create_access_token(
            subject=user.usuario,
            user_id=user.id,
            rol=user.rol.value
        )
        refresh_token = create_refresh_token(
            subject=user.usuario,
            user_id=user.id,
            rol=user.rol.value
        )

        AuditService.log_event(
            db=self.db,
            accion="LOGIN_EXITOSO",
            entidad="usuarios",
            entidad_id=user.id,
            usuario_id=user.id,
            detalles=f"Inicio de sesión exitoso para usuario '{user.usuario}' [Rol: {user.rol.value}].",
            ip_origen=client_ip
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user)
        )

    def refresh_access_token(self, refresh_token_str: str, client_ip: Optional[str] = None) -> TokenResponse:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresco inválido o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

        if is_token_revoked(refresh_token_str):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El token de refresco ha sido revocado. Inicie sesión nuevamente.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            payload = decode_token(refresh_token_str)
            if payload.get("type") != "refresh":
                raise credentials_exception
            user_id = payload.get("user_id")
            if not user_id:
                raise credentials_exception
        except jwt.PyJWTError:
            raise credentials_exception

        user = self.repo.get_by_id(user_id)
        if not user or not user.activo:
            raise credentials_exception

        # Rotar y generar nuevo access_token y nuevo refresh_token
        new_access_token = create_access_token(
            subject=user.usuario,
            user_id=user.id,
            rol=user.rol.value
        )
        new_refresh_token = create_refresh_token(
            subject=user.usuario,
            user_id=user.id,
            rol=user.rol.value
        )

        # Revocar el refresh token anterior para prevenir reuso (Token Rotation)
        revoke_token(refresh_token_str)

        AuditService.log_event(
            db=self.db,
            accion="REFRESH_TOKEN",
            entidad="usuarios",
            entidad_id=user.id,
            usuario_id=user.id,
            detalles=f"Token renovado mediante refresh token para '{user.usuario}'.",
            ip_origen=client_ip
        )

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user)
        )

    def logout(self, token_str: str, user: User, client_ip: Optional[str] = None) -> bool:
        revoke_token(token_str)
        AuditService.log_event(
            db=self.db,
            accion="LOGOUT",
            entidad="usuarios",
            entidad_id=user.id,
            usuario_id=user.id,
            detalles=f"Cierre de sesión de usuario '{user.usuario}' y revocación de token.",
            ip_origen=client_ip
        )
        return True

    def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
        client_ip: Optional[str] = None
    ) -> bool:
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña actual proporcionada es incorrecta."
            )

        if current_password == new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La nueva contraseña no puede ser idéntica a la anterior."
            )

        new_hash = get_password_hash(new_password)
        user.password_hash = new_hash
        self.db.commit()
        self.db.refresh(user)

        AuditService.log_event(
            db=self.db,
            accion="CAMBIO_PASSWORD",
            entidad="usuarios",
            entidad_id=user.id,
            usuario_id=user.id,
            detalles=f"Contraseña actualizada exitosamente para '{user.usuario}'.",
            ip_origen=client_ip
        )
        return True
