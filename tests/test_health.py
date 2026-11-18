"""
Pruebas automatizadas de la Fase 1: Vitalidad y preparación del servicio.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Valida que el endpoint raíz responda correctamente con información del sistema."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["estado"] == "operativo"
    assert "documentacion_swagger" in data
    assert data["documentacion_swagger"] == "/docs"


def test_health_liveness_endpoint():
    """Valida el endpoint de vitalidad /health."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data


def test_health_readiness_endpoint():
    """Valida el endpoint de preparación /health/ready."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ready", "degraded"]
    assert "database" in data
    assert "storage" in data
