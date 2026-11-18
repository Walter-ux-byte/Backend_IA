"""
Punto de Entrada Principal de la Aplicación FastAPI.
Sistema de Detección de Violencia mediante Inteligencia Artificial (IA).
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.routers import health, auth, users, cameras
from app.cameras.camera_manager import camera_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ciclo de vida de la aplicación:
    Se ejecuta al iniciar y al detener el servidor FastAPI.
    Garantiza que las rutas de almacenamiento existan y los recursos se liberen ordenadamente.
    """
    # 1. Asegurar directorios de almacenamiento de evidencias
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    os.makedirs(settings.EVIDENCES_IMAGES_DIR, exist_ok=True)
    os.makedirs(settings.EVIDENCES_VIDEOS_DIR, exist_ok=True)
    print(f"[*] Directorios de almacenamiento verificados: {settings.STORAGE_DIR}")
    print(f"[*] Servidor iniciado en modo: {settings.APP_ENV} | Debug: {settings.DEBUG}")

    yield

    # Limpieza o cierre de conexiones si aplica
    print("[*] Cerrando servidor y liberando recursos...")
    camera_manager.stop_all()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## Backend del Sistema de Detección de Violencia con IA
    
    API REST y servicios en tiempo real diseñados para el monitoreo automatizado de seguridad:
    - **Detección de Personas**: Integración con Ultralytics YOLO.
    - **Estimación de Postura**: Integración con Google MediaPipe.
    - **Detección de Incidentes**: Caídas, inmovilidad prolongada, movimientos bruscos y posibles agresiones.
    - **Alertas y Evidencias**: Emisión de notificaciones por WebSocket y almacenamiento seguro de capturas/clips.
    - **Monitoreo de Cámaras**: Soporte para Webcams, archivos de prueba MP4 y cámaras IP RTSP.
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configuración de Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusión de Enrutadores de la API
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(cameras.router)


@app.get("/", tags=["Información General"], status_code=status.HTTP_200_OK)
def root():
    """
    Endpoint de bienvenida e información del servicio.
    Proporciona enlaces rápidos a la documentación interactiva OpenAPI/Swagger.
    """
    return {
        "sistema": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "entorno": settings.APP_ENV,
        "estado": "operativo",
        "documentacion_swagger": "/docs",
        "documentacion_redoc": "/redoc",
        "salud_servicio": "/health",
        "preparacion_servicio": "/health/ready",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
