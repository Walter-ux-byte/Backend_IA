"""
Pruebas automatizadas de Administración de Usuarios y Roles RBAC (Fase 3).
Cubre: Creación, lectura, actualización, eliminación lógica y restricción de permisos.
"""
import pytest
from app.core.security import get_password_hash
from app.models.user import User
from app.models.enums import RolUsuario


@pytest.fixture(autouse=True)
def seed_users_data(db):
    """Siembra los usuarios base con diferentes roles."""
    if not db.query(User).filter(User.usuario == "super_admin").first():
        admin = User(
            nombre="Super",
            apellido="Admin",
            correo="superadmin@example.com",
            usuario="super_admin",
            password_hash=get_password_hash("AdminPass123*"),
            rol=RolUsuario.ADMINISTRADOR,
            activo=True
        )
        supervisor = User(
            nombre="Laura",
            apellido="Supervisor",
            correo="laura@example.com",
            usuario="laura_sup",
            password_hash=get_password_hash("SupPass123*"),
            rol=RolUsuario.SUPERVISOR,
            activo=True
        )
        seguridad = User(
            nombre="Pedro",
            apellido="Guardia",
            correo="pedro@example.com",
            usuario="pedro_guardia",
            password_hash=get_password_hash("GuardiaPass123*"),
            rol=RolUsuario.SEGURIDAD,
            activo=True
        )
        db.add_all([admin, supervisor, seguridad])
        db.commit()


def get_token_for(client, username: str, password: str) -> str:
    """Helper para obtener token de autenticación."""
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_list_users_as_admin(client):
    """Valida que ADMINISTRADOR pueda listar usuarios."""
    token = get_token_for(client, "super_admin", "AdminPass123*")
    res = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert data["total"] >= 3


def test_list_users_as_supervisor(client):
    """Valida que SUPERVISOR pueda listar usuarios."""
    token = get_token_for(client, "laura_sup", "SupPass123*")
    res = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200


def test_list_users_as_seguridad_forbidden(client):
    """Valida que SEGURIDAD NO pueda listar usuarios (403 Forbidden)."""
    token = get_token_for(client, "pedro_guardia", "GuardiaPass123*")
    res = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403
    assert "permisos insuficientes" in res.json()["detail"].lower()


def test_create_user_as_admin(client):
    """Valida creación de usuario por ADMINISTRADOR (201)."""
    token = get_token_for(client, "super_admin", "AdminPass123*")
    new_user_data = {
        "nombre": "Ana",
        "apellido": "Gómez",
        "correo": "ana.gomez@example.com",
        "usuario": "anagomez",
        "password": "PasswordSeguro2026*",
        "rol": "SEGURIDAD",
        "activo": True
    }
    res = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {token}"},
        json=new_user_data
    )
    assert res.status_code == 201
    created = res.json()
    assert created["usuario"] == "anagomez"
    assert created["rol"] == "SEGURIDAD"


def test_create_user_duplicate_username_fails(client):
    """Valida que no se permitan usernames repetidos (400)."""
    token = get_token_for(client, "super_admin", "AdminPass123*")
    res = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "nombre": "Duplicado",
            "apellido": "Test",
            "correo": "otrocorreo@example.com",
            "usuario": "anagomez",  # Ya existe
            "password": "PasswordSeguro2026*",
            "rol": "SEGURIDAD"
        }
    )
    assert res.status_code == 400
    assert "ya se encuentra registrado" in res.json()["detail"].lower()


def test_create_user_as_supervisor_forbidden(client):
    """Valida que SUPERVISOR no tenga permiso de crear usuarios (403)."""
    token = get_token_for(client, "laura_sup", "SupPass123*")
    res = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "nombre": "Test",
            "apellido": "User",
            "correo": "testuser@example.com",
            "usuario": "testuser",
            "password": "PasswordSeguro2026*",
            "rol": "SEGURIDAD"
        }
    )
    assert res.status_code == 403


def test_update_user_as_admin(client):
    """Valida modificación de usuario por ADMINISTRADOR."""
    token = get_token_for(client, "super_admin", "AdminPass123*")
    list_res = client.get("/api/users?rol=SEGURIDAD", headers={"Authorization": f"Bearer {token}"})
    ana = next(u for u in list_res.json()["items"] if u["usuario"] == "anagomez")

    update_res = client.put(
        f"/api/users/{ana['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"nombre": "Ana María", "apellido": "Gómez Silva"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["nombre"] == "Ana María"
    assert update_res.json()["apellido"] == "Gómez Silva"


def test_delete_user_soft_delete(client):
    """Valida eliminación lógica (activo = False) por ADMINISTRADOR."""
    token = get_token_for(client, "super_admin", "AdminPass123*")
    list_res = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    ana = next(u for u in list_res.json()["items"] if u["usuario"] == "anagomez")

    del_res = client.delete(f"/api/users/{ana['id']}", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 200
    assert del_res.json()["activo"] is False

    # Verificar que el usuario desactivado ya no puede iniciar sesión (403)
    login_try = client.post("/api/auth/login", json={"username": "anagomez", "password": "PasswordSeguro2026*"})
    assert login_try.status_code == 403


def test_admin_cannot_delete_himself(client):
    """Valida que un administrador no pueda desactivarse a sí mismo (400)."""
    token = get_token_for(client, "super_admin", "AdminPass123*")
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    my_id = me_res.json()["id"]

    del_try = client.delete(f"/api/users/{my_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_try.status_code == 400
    assert "no puede desactivar su propia cuenta" in del_try.json()["detail"].lower()
