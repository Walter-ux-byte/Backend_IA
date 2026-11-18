"""
Endpoints de comprobación de salud y monitoreo del sistema (Health Checks).
Permite a balanceadores de carga, servicios de monitoreo o administradores
verificar que el proceso está activo y preparado para atender solicitudes.
"""
from datetime import datetime, timezone
import os
from fastapi import APIRouter, status
from app.core.config import settings
from app.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter(tags=["Salud del Sistema"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Verificar vitalidad del servicio (Liveness)",
    description="Indica si el servidor FastAPI se encuentra en ejecución activa y respondiendo solicitudes HTTP."
)
def get_health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        environment=settings.APP_ENV,
        version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc).isoformat()
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Verificar preparación del servicio (Readiness)",
    description="Verifica los subsistemas críticos (directorios de almacenamiento y conectividad a base de datos)."
)
def get_readiness() -> ReadinessResponse:
    # Verificación de almacenamiento local de evidencias
    storage_ok = (
        os.path.exists(settings.STORAGE_DIR) and
        os.path.exists(settings.EVIDENCES_IMAGES_DIR) and
        os.path.exists(settings.EVIDENCES_VIDEOS_DIR)
    )

    # Estado de la base de datos en tiempo real (Fase 2)
    db_ok = False
    db_error = None
    try:
        from app.core.database import SessionLocal
        from sqlalchemy import text
        with SessionLocal() as session:
            session.execute(text("SELECT 1;"))
            db_ok = True
    except Exception as exc:
        db_error = str(exc)

    db_status = {
        "configured": bool(settings.DATABASE_URL),
        "status": "connected" if db_ok else "disconnected",
        "error": db_error
    }

    storage_status = {
        "status": "ready" if storage_ok else "missing_directories",
        "directories": {
            "root": settings.STORAGE_DIR,
            "images": settings.EVIDENCES_IMAGES_DIR,
            "videos": settings.EVIDENCES_VIDEOS_DIR,
        }
    }

    overall_status = "ready" if (storage_ok and db_ok) else "degraded"

    return ReadinessResponse(
        status=overall_status,
        database=db_status,
        storage=storage_status,
        details={
            "app_name": settings.APP_NAME,
            "debug": settings.DEBUG,
            "device": settings.DEVICE
        }
    )
