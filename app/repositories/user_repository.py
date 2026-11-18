"""
Repositorio para operaciones de base de datos sobre la entidad Usuario.
Aplica principios de abstracción de datos y consultas optimizadas.
"""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.user import User
from app.models.enums import RolUsuario
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.usuario == username.lower().strip()).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.correo == email.lower().strip()).first()

    def get_by_identifier(self, identifier: str) -> Optional[User]:
        """Busca un usuario por su nombre de usuario o por su correo electrónico."""
        clean = identifier.lower().strip()
        return self.db.query(User).filter(
            or_(User.usuario == clean, User.correo == clean)
        ).first()

    def get_paginated(
        self,
        skip: int = 0,
        limit: int = 20,
        rol: Optional[RolUsuario] = None,
        activo: Optional[bool] = None
    ) -> Tuple[List[User], int]:
        query = self.db.query(User)
        if rol is not None:
            query = query.filter(User.rol == rol)
        if activo is not None:
            query = query.filter(User.activo == activo)

        total = query.count()
        users = query.order_by(User.id.asc()).offset(skip).limit(limit).all()
        return users, total

    def create(self, user_in: UserCreate, password_hash: str) -> User:
        user = User(
            nombre=user_in.nombre.strip(),
            apellido=user_in.apellido.strip(),
            correo=user_in.correo.lower().strip(),
            usuario=user_in.usuario.lower().strip(),
            password_hash=password_hash,
            rol=user_in.rol,
            activo=user_in.activo
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User, user_in: UserUpdate, new_password_hash: Optional[str] = None) -> User:
        if user_in.nombre is not None:
            user.nombre = user_in.nombre.strip()
        if user_in.apellido is not None:
            user.apellido = user_in.apellido.strip()
        if user_in.correo is not None:
            user.correo = user_in.correo.lower().strip()
        if user_in.rol is not None:
            user.rol = user_in.rol
        if user_in.activo is not None:
            user.activo = user_in.activo
        if new_password_hash is not None:
            user.password_hash = new_password_hash

        self.db.commit()
        self.db.refresh(user)
        return user

    def soft_delete(self, user: User) -> User:
        """Eliminación lógica de usuario (establece activo = False)."""
        user.activo = False
        self.db.commit()
        self.db.refresh(user)
        return user
