"""
Pruebas unitarias y de integración de la Base de Datos (Fase 2).
Valida la integridad de modelos, claves foráneas, enums y relaciones ORM.
"""
import pytest
from app.core.database import Base
from app.models import (
    User, Camera, Incident, Alert, Evidence, Notification, AuditLog,
    RolUsuario, EstadoCamara, TipoFuenteCamara, TipoIncidente,
    NivelRiesgo, EstadoIncidente, PrioridadAlerta, EstadoAlerta, TipoEvidencia
)


def test_models_table_creation():
    """Verifica que las 7 tablas requeridas existan en los metadatos."""
    tables = Base.metadata.tables.keys()
    assert "usuarios" in tables
    assert "camaras" in tables
    assert "incidentes" in tables
    assert "alertas" in tables
    assert "evidencias" in tables
    assert "notificaciones" in tables
    assert "auditoria" in tables


def test_create_user_model(db):
    """Verifica la inserción y consulta de un usuario con sus atributos y rol."""
    user = User(
        nombre="Carlos",
        apellido="Mendoza",
        correo="carlos@example.com",
        usuario="cmendoza_db",
        password_hash="hash_seguro_123",
        rol=RolUsuario.SEGURIDAD,
        activo=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    assert user.id is not None
    assert user.usuario == "cmendoza_db"
    assert user.rol == RolUsuario.SEGURIDAD


def test_create_camera_and_incident_relationship(db):
    """Verifica la creación de cámara, incidente vinculado y alerta automática."""
    camera = Camera(
        nombre="Cámara Entrada Principal",
        ubicacion="Pasillo Norte",
        rtsp_url="rtsp://admin:1234@192.168.1.100:554/live",
        tipo_fuente=TipoFuenteCamara.RTSP,
        estado=EstadoCamara.CONECTADA,
        activa=True
    )
    db.add(camera)
    db.commit()
    db.refresh(camera)

    incident = Incident(
        camara_id=camera.id,
        tipo=TipoIncidente.POSIBLE_AGRESION,
        descripcion="Forcejeo detectado entre dos individuos",
        nivel_riesgo=NivelRiesgo.ALTO,
        confianza=0.88,
        estado=EstadoIncidente.PENDIENTE
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    alert = Alert(
        incidente_id=incident.id,
        mensaje="Alerta Crítica: Posible agresión detectada en Pasillo Norte",
        prioridad=PrioridadAlerta.ALTA,
        estado=EstadoAlerta.ACTIVA
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    # Validar navegación por relaciones ORM
    assert incident.camara.nombre == "Cámara Entrada Principal"
    assert len(incident.alertas) == 1
    assert incident.alertas[0].mensaje.startswith("Alerta Crítica")


def test_evidence_and_audit_log(db):
    """Verifica registro de evidencias de incidentes y logs de auditoría."""
    incident = Incident(
        tipo=TipoIncidente.CAIDA,
        descripcion="Caída de persona mayor",
        nivel_riesgo=NivelRiesgo.MEDIO,
        confianza=0.92
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    evidence = Evidence(
        incidente_id=incident.id,
        tipo_archivo=TipoEvidencia.IMAGEN,
        ruta_archivo="storage/images/incidente_1_frame_01.jpg",
        tamano_bytes=204800,
        hash_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    db.add(evidence)

    audit = AuditLog(
        accion="REGISTRO_INCIDENTE",
        entidad="incidentes",
        entidad_id=incident.id,
        detalles="Incidente de caída detectado automáticamente por IA"
    )
    db.add(audit)
    db.commit()

    assert evidence.id is not None
    assert audit.id is not None
    assert len(incident.evidencias) == 1
