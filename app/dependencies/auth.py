"""
Dependencias de Autenticación, Verificación de Tokens y Autorización Basada en Roles (RBAC).
RF-16: Control de acceso según roles ADMINISTRADOR, SEGURIDAD y SUPERVISOR.
RF-17: Protección de rutas con JWT.
"""
from typing import List, Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token, is_token_revoked
from app.models.user import User
from app.models.enums import RolUsuario
from app.repositories.user_repository import UserRepository

# Esquema OAuth2 configurado para Swagger UI (apunta a /api/auth/login)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    auto_error=False
)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Extrae, valida y decodifica el token JWT Bearer.
    Recupera el usuario correspondiente desde la base de datos.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales de acceso.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación no proporcionado. Inicie sesión para continuar.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token de acceso ha sido revocado. Inicie sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(token)
        token_type = payload.get("type")
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tipo de token inválido. Se requiere un token de acceso.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id: Optional[int] = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token de acceso ha expirado. Utilice el refresh token o inicie sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception

    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verifica que el usuario autenticado no haya sido desactivado (eliminación lógica).
    """
    if not current_user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta de usuario se encuentra desactivada. Contacte al administrador.",
        )
    return current_user


def require_roles(allowed_roles: List[RolUsuario]):
    """
    Fábrica de dependencias para Autorización Basada en Roles (RBAC).
    Verifica si el rol del usuario actual está dentro de los roles autorizados.
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.rol not in allowed_roles:
            roles_permitidos_str = ", ".join([r.value for r in allowed_roles])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permisos insuficientes. Se requiere rol: [{roles_permitidos_str}]. Su rol actual es: '{current_user.rol.value}'."
            )
        return current_user

    return role_checker
