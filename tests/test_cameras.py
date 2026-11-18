"""
Pruebas automatizadas de Administración y Monitoreo de Cámaras (Fase 4).
Cubre: CRUD de cámaras, permisos RBAC, inicio y detención de captura,
procesamiento de MP4 real, tolerancia a errores en OpenCV y streaming MJPEG.
"""
import os
import time
import pytest
from app.models.user import User
from app.models.enums import RolUsuario, TipoFuenteCamara, EstadoCamara
from app.core.security import get_password_hash
from app.cameras.camera_manager import camera_manager


@pytest.fixture(autouse=True)
def seed_cameras_users(db):
    """Siembra usuarios dedicados exclusivamente a las pruebas del módulo de cámaras."""
    if not db.query(User).filter(User.usuario == "admin_cameras").first():
        admin = User(
            nombre="Admin",
            apellido="Camaras",
            correo="admin.cameras@example.com",
            usuario="admin_cameras",
            password_hash=get_password_hash("CamPass123*"),
            rol=RolUsuario.ADMINISTRADOR,
            activo=True
        )
        guard = User(
            nombre="Guardia",
            apellido="Camaras",
            correo="guard.cameras@example.com",
            usuario="guard_cameras",
            password_hash=get_password_hash("CamPass123*"),
            rol=RolUsuario.SEGURIDAD,
            activo=True
        )
        db.add_all([admin, guard])
        db.commit()

    yield
    camera_manager.stop_all()


def get_token_for_user(client, username: str, password: str = "CamPass123*") -> str:
    """Helper para autenticarse y obtener access token."""
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_create_camera_as_admin(client):
    """Valida creación exitosa de una cámara por ADMINISTRADOR (201)."""
    token = get_token_for_user(client, "admin_cameras")
    res = client.post(
        "/api/cameras",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "nombre": "Cámara Patio Norte",
            "ubicacion": "Zona Exterior",
            "rtsp_url": "rtsp://admin:Secreto123@192.168.1.50:554/ch0",
            "tipo_fuente": "RTSP",
            "fps": 30,
            "resolucion": "1920x1080",
            "activa": True
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["nombre"] == "Cámara Patio Norte"
    assert data["tipo_fuente"] == "RTSP"
    assert data["estado"] == "Desconectada"


def test_create_camera_as_seguridad_forbidden(client):
    """Valida que un usuario con rol SEGURIDAD no pueda registrar cámaras (403)."""
    token = get_token_for_user(client, "guard_cameras")
    res = client.post(
        "/api/cameras",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "nombre": "Cámara No Autorizada",
            "ubicacion": "Pasillo",
            "rtsp_url": "0",
            "tipo_fuente": "WEBCAM"
        }
    )
    assert res.status_code == 403


def test_list_cameras_and_credential_masking(client):
    """Valida que los no administradores vean las contraseñas RTSP enmascaradas."""
    admin_token = get_token_for_user(client, "admin_cameras")
    guard_token = get_token_for_user(client, "guard_cameras")

    # Listar como Admin: ve la URL completa
    res_admin = client.get("/api/cameras", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    cam_admin = next(c for c in res_admin.json()["items"] if c["nombre"] == "Cámara Patio Norte")
    assert "Secreto123" in cam_admin["rtsp_url"]

    # Listar como Guardia de Seguridad: la clave RTSP aparece enmascarada con ******
    res_guard = client.get("/api/cameras", headers={"Authorization": f"Bearer {guard_token}"})
    assert res_guard.status_code == 200
    cam_guard = next(c for c in res_guard.json()["items"] if c["nombre"] == "Cámara Patio Norte")
    assert "******" in cam_guard["rtsp_url"]
    assert "Secreto123" not in cam_guard["rtsp_url"]


def test_update_camera_as_admin(client):
    """Valida modificación de parámetros de cámara por ADMINISTRADOR (200)."""
    admin_token = get_token_for_user(client, "admin_cameras")
    list_res = client.get("/api/cameras", headers={"Authorization": f"Bearer {admin_token}"})
    cam_id = list_res.json()["items"][0]["id"]

    update_res = client.put(
        f"/api/cameras/{cam_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"ubicacion": "Zona Exterior - Portón Principal", "fps": 20}
    )
    assert update_res.status_code == 200
    assert update_res.json()["ubicacion"] == "Zona Exterior - Portón Principal"
    assert update_res.json()["fps"] == 20


def test_start_and_stop_mp4_camera(client):
    """Valida inicio y detención de captura de un video MP4 real."""
    admin_token = get_token_for_user(client, "admin_cameras")
    video_path = os.path.abspath("tests/test_video.mp4")

    # 1. Crear cámara asociada al MP4 sintético
    cam_res = client.post(
        "/api/cameras",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "nombre": "Cámara Video Prueba MP4",
            "ubicacion": "Laboratorio IA",
            "rtsp_url": video_path,
            "tipo_fuente": "MP4",
            "fps": 15
        }
    )
    assert cam_res.status_code == 201
    cam_id = cam_res.json()["id"]

    # 2. Iniciar captura
    start_res = client.post(
        f"/api/cameras/{cam_id}/start",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert start_res.status_code == 200
    assert start_res.json()["captura_activa"] is True

    # Dar tiempo al hilo de captura para leer fotogramas
    time.sleep(0.5)

    # 3. Consultar telemetría y estado
    status_res = client.get(
        f"/api/cameras/{cam_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert status_res.status_code == 200
    telemetry = status_res.json()
    assert telemetry["estado"] in ["Conectada", "Reconectando"]
    assert telemetry["frames_procesados"] >= 0

    # 4. Detener captura
    stop_res = client.post(
        f"/api/cameras/{cam_id}/stop",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert stop_res.status_code == 200
    assert stop_res.json()["captura_activa"] is False
    assert stop_res.json()["estado"] == "Desconectada"


def test_invalid_source_error_handling(client):
    """Valida que una fuente de video inexistente no derribe el servidor."""
    admin_token = get_token_for_user(client, "admin_cameras")

    cam_res = client.post(
        "/api/cameras",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "nombre": "Cámara Fuente Rota",
            "ubicacion": "Test Error",
            "rtsp_url": "ruta/inexistente/video_fantasma.mp4",
            "tipo_fuente": "MP4"
        }
    )
    cam_id = cam_res.json()["id"]

    # Iniciar captura con ruta inexistente
    start_res = client.post(
        f"/api/cameras/{cam_id}/start",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert start_res.status_code == 200

    time.sleep(0.3)

    # El procesador debe reportar reconectando o error de forma controlada sin tumbar la app
    status_res = client.get(
        f"/api/cameras/{cam_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert status_res.status_code == 200
    assert status_res.json()["estado"] in ["Reconectando", "Error", "Desconectada"]


def test_stream_endpoint_content_type(client):
    """Valida que el endpoint /stream devuelva el tipo MIME de MJPEG."""
    admin_token = get_token_for_user(client, "admin_cameras")
    list_res = client.get("/api/cameras", headers={"Authorization": f"Bearer {admin_token}"})
    cam_id = list_res.json()["items"][0]["id"]

    # Probar conexión al stream usando max_frames=1 para pruebas deterministas
    res = client.get(f"/api/cameras/{cam_id}/stream?token={admin_token}&max_frames=1")
    assert res.status_code == 200
    assert "multipart/x-mixed-replace" in res.headers["content-type"]
    assert len(res.content) > 0


def test_soft_delete_camera(client):
    """Valida desactivación lógica de cámara (DELETE)."""
    admin_token = get_token_for_user(client, "admin_cameras")
    list_res = client.get("/api/cameras", headers={"Authorization": f"Bearer {admin_token}"})
    cam_id = list_res.json()["items"][0]["id"]

    del_res = client.delete(
        f"/api/cameras/{cam_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert del_res.status_code == 200
    assert del_res.json()["activa"] is False
    assert del_res.json()["estado"] == "Desconectada"
