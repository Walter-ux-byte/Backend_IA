"""
Pruebas automatizadas de Autenticación y Seguridad (Fase 3).
Cubre: Login exitoso, contraseña incorrecta, token inválido, token expirado,
usuario desactivado, refresh token, revocación y logout.
"""
from datetime import timedelta
import pytest
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.enums import RolUsuario


@pytest.fixture(autouse=True)
def seed_auth_users(db):
    """Siembra los usuarios necesarios para las pruebas de autenticación."""
    # Verificar si ya existen antes de insertar
    if not db.query(User).filter(User.usuario == "admin_auth").first():
        admin = User(
            nombre="Admin",
            apellido="Test",
            correo="admin.auth@example.com",
            usuario="admin_auth",
            password_hash=get_password_hash("Password123*"),
            rol=RolUsuario.ADMINISTRADOR,
            activo=True
        )
        inactive_user = User(
            nombre="Inactivo",
            apellido="User",
            correo="inactivo.auth@example.com",
            usuario="inactivo_auth",
            password_hash=get_password_hash("Password123*"),
            rol=RolUsuario.SEGURIDAD,
            activo=False
        )
        guard_user = User(
            nombre="Guardia",
            apellido="Seguridad",
            correo="guardia.auth@example.com",
            usuario="guardia_auth",
            password_hash=get_password_hash("Guardia123*"),
            rol=RolUsuario.SEGURIDAD,
            activo=True
        )
        db.add_all([admin, inactive_user, guard_user])
        db.commit()


def test_login_successful(client):
    """Valida login exitoso con usuario y contraseña correctos."""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin_auth", "password": "Password123*"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["usuario"] == "admin_auth"
    assert data["user"]["rol"] == "ADMINISTRADOR"


def test_login_with_email_successful(client):
    """Valida login exitoso utilizando el correo electrónico."""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin.auth@example.com", "password": "Password123*"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["correo"] == "admin.auth@example.com"


def test_login_incorrect_password(client):
    """Valida rechazo ante contraseña equivocada (401)."""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin_auth", "password": "ClaveEquivocada123"}
    )
    assert response.status_code == 401
    assert "incorrectas" in response.json()["detail"].lower()


def test_login_user_not_found(client):
    """Valida rechazo si el usuario no existe (401)."""
    response = client.post(
        "/api/auth/login",
        json={"username": "usuario_fantasma", "password": "Password123*"}
    )
    assert response.status_code == 401


def test_login_inactive_user(client):
    """Valida rechazo si la cuenta está desactivada (403)."""
    response = client.post(
        "/api/auth/login",
        json={"username": "inactivo_auth", "password": "Password123*"}
    )
    assert response.status_code == 403
    assert "desactivada" in response.json()["detail"].lower()


def test_get_me_endpoint_with_valid_token(client):
    """Valida obtención de perfil /api/auth/me con token Bearer."""
    login_res = client.post(
        "/api/auth/login",
        json={"username": "admin_auth", "password": "Password123*"}
    )
    token = login_res.json()["access_token"]

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["usuario"] == "admin_auth"


def test_invalid_token(client):
    """Valida rechazo con token con firma o formato inválido (401)."""
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer token_falso_invalido_12345"}
    )
    assert response.status_code == 401


def test_expired_token(client):
    """Valida rechazo de token de acceso expirado (401)."""
    expired_token = create_access_token(
        subject="admin_auth",
        user_id=1,
        rol="ADMINISTRADOR",
        expires_delta=timedelta(seconds=-10)
    )
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401
    assert "expirado" in response.json()["detail"].lower()


def test_refresh_token_flow(client):
    """Valida renovación de sesión con refresh token."""
    login_res = client.post(
        "/api/auth/login",
        json={"username": "guardia_auth", "password": "Guardia123*"}
    )
    refresh_token = login_res.json()["refresh_token"]

    refresh_res = client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert refresh_res.status_code == 200
    data = refresh_res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != refresh_token


def test_logout_revokes_token(client):
    """Valida que /api/auth/logout invalide el token inmediatamente."""
    login_res = client.post(
        "/api/auth/login",
        json={"username": "guardia_auth", "password": "Guardia123*"}
    )
    access_token = login_res.json()["access_token"]

    logout_res = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["revoked"] is True

    retry_res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert retry_res.status_code == 401
    assert "revocado" in retry_res.json()["detail"].lower()


def test_change_password(client):
    """Valida cambio de contraseña de usuario."""
    login_res = client.post(
        "/api/auth/login",
        json={"username": "admin_auth", "password": "Password123*"}
    )
    token = login_res.json()["access_token"]

    change_res = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "current_password": "Password123*",
            "new_password": "NewSecretPassword2026*"
        }
    )
    assert change_res.status_code == 200

    old_login = client.post(
        "/api/auth/login",
        json={"username": "admin_auth", "password": "Password123*"}
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/auth/login",
        json={"username": "admin_auth", "password": "NewSecretPassword2026*"}
    )
    assert new_login.status_code == 200
