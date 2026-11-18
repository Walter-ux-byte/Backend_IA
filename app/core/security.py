"""
Módulo de Seguridad Criptográfica, Hashing de Contraseñas y Gestión de JWT.
RF-17: Autenticación, JWT con expiración, Refresh Tokens y Revocación.
Utiliza bcrypt nativo directamente para máxima compatibilidad y rendimiento.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Set
import uuid
import bcrypt
import jwt
from app.core.config import settings

# Set en memoria para lista negra de refresh tokens revocados
_revoked_tokens: Set[str] = set()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña en texto plano coincide con el hash almacenado."""
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Genera el hash seguro bcrypt a partir de una contraseña en texto plano."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def create_access_token(subject: str, user_id: int, rol: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT de acceso de corta duración (por defecto 60 minutos).
    Incluye subject (username), user_id, rol y tipo 'access'.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": subject,
        "user_id": user_id,
        "rol": rol,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: str, user_id: int, rol: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT de refresco de mayor duración (por defecto 7 días).
    Incluye identificador único 'jti' para permitir su revocación explícita.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode: Dict[str, Any] = {
        "sub": subject,
        "user_id": user_id,
        "rol": rol,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodifica y valida la firma y expiración de un token JWT.
    Lanza jwt.PyJWTError si el token es inválido o ha expirado.
    """
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    return payload


def revoke_token(token: str) -> bool:
    """Registra el identificador jti o el token en la lista de revocación."""
    try:
        payload = decode_token(token)
        jti = payload.get("jti") or token
        _revoked_tokens.add(jti)
        return True
    except jwt.PyJWTError:
        _revoked_tokens.add(token)
        return True


def is_token_revoked(token: str) -> bool:
    """Verifica si el token o su identificador 'jti' ha sido revocado."""
    if token in _revoked_tokens:
        return True
    try:
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        jti = unverified_payload.get("jti")
        if jti and jti in _revoked_tokens:
            return True
    except Exception:
        pass
    return False
