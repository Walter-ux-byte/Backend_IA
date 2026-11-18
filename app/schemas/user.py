"""
Esquemas Pydantic para la gestión de Usuarios.
RF-16: CRUD de usuarios con validaciones de tipo, longitud y formato.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from app.models.enums import RolUsuario


class UserBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, examples=["Juan"])
    apellido: str = Field(..., min_length=2, max_length=100, examples=["Pérez"])
    correo: EmailStr = Field(..., examples=["juan.perez@seguridad.local"])
    usuario: str = Field(..., min_length=3, max_length=50, examples=["jperez"])
    rol: RolUsuario = Field(default=RolUsuario.SEGURIDAD, examples=[RolUsuario.SEGURIDAD])
    activo: bool = Field(default=True)

    @field_validator("usuario")
    @classmethod
    def validate_username(cls, v: str) -> str:
        clean = v.strip().lower()
        if not clean.isalnum() and "_" not in clean and "-" not in clean:
            raise ValueError("El nombre de usuario solo puede contener letras, números, guiones y guiones bajos.")
        return clean


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100, examples=["Seguridad2026*"])


class UserUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    apellido: Optional[str] = Field(None, min_length=2, max_length=100)
    correo: Optional[EmailStr] = None
    rol: Optional[RolUsuario] = None
    activo: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6, max_length=100)


class UserResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    correo: str
    usuario: str
    rol: RolUsuario
    activo: bool
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int
