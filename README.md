# Sistema de Detección de Violencia mediante Inteligencia Artificial (IA) — Backend

Backend modular, escalable y robusto desarrollado con **FastAPI**, **PostgreSQL**, **SQLAlchemy**, **OpenCV**, **YOLO** y **MediaPipe**.

---

## Arquitectura del Proyecto

```text
BACKEND-IA/
│
├── app/                        # Núcleo de la aplicación
│   ├── main.py                 # Instancia principal de FastAPI, middleware y lifespan
│   ├── core/                   # Configuraciones globales, seguridad y BD
│   │   ├── config.py           # Variables de entorno con Pydantic Settings
│   │   ├── security.py         # Hashing de contraseñas y JWT (Fase 3)
│   │   └── database.py         # Motor SQLAlchemy y sesiones (Fase 2)
│   │
│   ├── models/                 # Modelos ORM de SQLAlchemy
│   ├── schemas/                # Esquemas y DTOs de Pydantic
│   │   └── health.py           # Esquemas para endpoints de salud
│   │
│   ├── routers/                # Controladores y endpoints REST
│   │   └── health.py           # Endpoints /health y /health/ready
│   │
│   ├── services/               # Lógica de negocio
│   ├── repositories/           # Capa de abstracción de datos
│   ├── dependencies/           # Inyección de dependencias (Auth, DB)
│   │
│   ├── ai/                     # Detección con IA (YOLO, MediaPipe, etc.)
│   ├── cameras/                # Gestión de flujos de video (Webcam, MP4, RTSP)
│   ├── notifications/          # Notificaciones por email y eventos
│   ├── websockets/             # Servidor de WebSockets para tiempo real
│   └── workers/                # Procesamiento asíncrono
│
├── storage/                    # Almacenamiento local de evidencias
│   ├── images/                 # Capturas de incidentes
│   └── videos/                 # Fragmentos de video de incidentes
│
├── tests/                      # Suite de pruebas automatizadas con Pytest
│   └── test_health.py          # Pruebas de vitalidad y preparación
│
├── .env.example                # Plantilla de variables de entorno
├── .env                        # Configuración activa del entorno
├── requirements.txt            # Dependencias del proyecto
├── pytest.ini                  # Configuración de pruebas
└── README.md                   # Documentación técnica
```

---

## Guía de Instalación y Ejecución en Windows (VS Code)

### 1. Requisitos Previos
- **Python 3.10** o superior instalado en el sistema.
- **Visual Studio Code** con la extensión oficial de Python de Microsoft.
- **PowerShell** en Windows.

### 2. Creación y Activación del Entorno Virtual
Abre una terminal de PowerShell en la raíz del proyecto (`BACKEND-IA`):

```powershell
# Crear el entorno virtual
python -m venv venv

# Activar el entorno virtual
.\venv\Scripts\Activate.ps1
```

> **Nota si recibes error de políticas de script en PowerShell:**
> Ejecuta en PowerShell: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### 3. Instalación de Dependencias
Con el entorno virtual activado (`(venv)` al inicio de la línea de comandos):

```powershell
pip install -r requirements.txt
```

### 4. Configuración de Variables de Entorno
Copia el archivo `.env.example` a `.env` (si aún no existe):

```powershell
Copy-Item .env.example .env
```

### 5. Iniciar el Servidor de Desarrollo

Puedes iniciar el servidor directamente mediante **npm** desde la terminal de VS Code:

```powershell
# Iniciar con recarga automática (desarrollo):
npm run start:dev

# Iniciar en modo estándar (producción):
npm run start

# Ejecutar pruebas automatizadas:
npm run test
```

También puedes ejecutarlo directamente con Python o Uvicorn si lo prefieres:
```powershell
.\venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

---

## Comprobación de Endpoints y Documentación Interactiva

Una vez iniciado el servidor, abre tu navegador web o cliente HTTP (Postman, Thunder Client) en:

| Recurso | URL | Descripción |
|---|---|---|
| **Página de Inicio** | `http://localhost:8000/` | Metadatos y estado del servicio |
| **Documentación Swagger** | `http://localhost:8000/docs` | Interfaz interactiva OpenAPI con botón **Authorize (JWT Bearer)** |
| **Documentación ReDoc** | `http://localhost:8000/redoc` | Documentación estructurada de referencia |
| **Liveness Check** | `http://localhost:8000/health` | Verifica que el servidor está activo |
| **Readiness Check** | `http://localhost:8000/health/ready` | Verifica almacenamiento y conexión PostgreSQL |

---

## Endpoints de Autenticación y Gestión de Usuarios (Fase 3)

### Autenticación (`/api/auth`)
- `POST /api/auth/login`: Autenticación por usuario o correo electrónico. Retorna `access_token` (60 min) y `refresh_token` (7 días).
- `POST /api/auth/refresh`: Renovación de `access_token` mediante rotación segura de `refresh_token`.
- `POST /api/auth/logout`: Revocación del token actual y registro en auditoría.
- `GET /api/auth/me`: Perfil del usuario autenticado actual.
- `POST /api/auth/change-password`: Actualización de contraseña del usuario autenticado.

### Usuarios (`/api/users`)
- `GET /api/users`: Listado paginado con filtros de `rol` y `activo` (*Roles: ADMINISTRADOR, SUPERVISOR*).
- `POST /api/users`: Creación de nuevos usuarios con contraseña segura (*Exclusivo: ADMINISTRADOR*).
- `GET /api/users/{id}`: Detalle de usuario (*ADMINISTRADOR, SUPERVISOR o el propio usuario*).
- `PUT /api/users/{id}`: Actualización completa de datos, rol y contraseña (*Exclusivo: ADMINISTRADOR*).
- `DELETE /api/users/{id}`: Eliminación lógica desactivando la cuenta (`activo = False`) (*Exclusivo: ADMINISTRADOR*).

### Cómo autenticarse en Swagger UI (`/docs`):
1. Entra a `http://localhost:8000/docs`.
2. Haz clic en el botón verde **Authorize** (arriba a la derecha).
3. Ingresa tu usuario (`admin`) y contraseña en los campos de login OAuth2 o ingresa el Bearer token en el campo `Value`.
4. Haz clic en **Authorize** y prueba cualquiera de los endpoints protegidos directamente desde Swagger.

### Cambiar contraseña de administrador mediante script:
```powershell
npm run admin:passwd
```

---

## 📹 Endpoints de Administración y Monitoreo de Cámaras (Fase 4)

### Cámaras (`/api/cameras`)
- `GET /api/cameras`: Listado paginado de cámaras con filtros por estado y activación (*ADMINISTRADOR, SUPERVISOR, SEGURIDAD*).
- `POST /api/cameras`: Registro de nuevas cámaras con soporte para `WEBCAM`, `MP4` y `RTSP` (*Exclusivo: ADMINISTRADOR*).
- `GET /api/cameras/{id}`: Detalle de una cámara con enmascaramiento de credenciales RTSP para no administradores.
- `PUT /api/cameras/{id}`: Actualización de configuración de cámara (*Exclusivo: ADMINISTRADOR*).
- `DELETE /api/cameras/{id}`: Desactivación lógica de la cámara y detención del hilo de captura (*Exclusivo: ADMINISTRADOR*).
- `GET /api/cameras/{id}/status`: Consulta de telemetría en tiempo real: estado (`Conectada`, `Reconectando`, `Error`, `Desconectada`), FPS reales, latencia en ms, frames procesados y reconexiones.
- `POST /api/cameras/{id}/start`: Inicia la captura y procesamiento de video en segundo plano mediante un hilo dedicado (*Exclusivo: ADMINISTRADOR*).
- `POST /api/cameras/{id}/stop`: Detiene la captura y libera los recursos de OpenCV (*Exclusivo: ADMINISTRADOR*).
- `GET /api/cameras/{id}/stream`: Transmisión en vivo en formato **MJPEG** (`multipart/x-mixed-replace; boundary=frame`), compatible con tags HTML5 `<img src="...">` y frontend React. Soporta autenticación mediante Bearer token en cabecera o como query param `?token=...`.

---

## Ejecución de Pruebas Automatizadas

Para validar que todo el sistema funciona correctamente:

```powershell
.\venv\Scripts\pytest -v
```
