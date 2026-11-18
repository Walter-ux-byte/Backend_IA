"""
Esquemas Pydantic para el módulo de Autenticación y Tokens JWT.
RF-17: Inicio de sesión, tokens de acceso y refresco, cambio de contraseña.
"""
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """Permite autenticarse mediante nombre de usuario O correo electrónico."""
    username: str = Field(..., description="Nombre de usuario o correo electrónico", examples=["admin"])
    password: str = Field(..., description="Contraseña en texto plano", examples=["Admin1234*"])


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Tiempo de expiración en segundos")
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Token de refresco válido para emitir un nuevo access_token")


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=6, description="Contraseña actual")
    new_password: str = Field(..., min_length=6, max_length=100, description="Nueva contraseña segura")


class LogoutResponse(BaseModel):
    message: str = "Sesión cerrada exitosamente"
    revoked: bool = True
