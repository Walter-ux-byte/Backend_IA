"""
Script para verificar la conexión a PostgreSQL con las variables de .env.
Muestra el diagnóstico y ayuda si la contraseña necesita ser ajustada.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from sqlalchemy import text
from app.core.database import SessionLocal, engine

print("=" * 60)
print("DIAGNÓSTICO DE CONEXIÓN A POSTGRESQL")
print("=" * 60)
print(f"Host:       {settings.DB_HOST}")
print(f"Puerto:     {settings.DB_PORT}")
print(f"Usuario:    {settings.DB_USER}")
print(f"Base Datos: {settings.DB_NAME}")
print(f"URL:        {settings.DATABASE_URL.replace(settings.DB_PASSWORD, '********')}")
print("-" * 60)

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();")).scalar()
        print("[+] ¡CONEXIÓN EXITOSA A POSTGRESQL!")
        print(f"[+] Versión del Servidor: {result}")
        print("\nPara ejecutar las migraciones pendientes:")
        print("  .\\venv\\Scripts\\alembic.exe upgrade head")
        print("O para inicializar tablas y sembrar usuario admin:")
        print("  .\\venv\\Scripts\\python.exe scripts\\init_db.py")
except Exception as e:
    print("[-] ERROR AL CONECTAR A POSTGRESQL:")
    print(f"    {e}")
    print("\n[?] ¿CÓMO RESOLVERLO?:")
    print("1. Abre el archivo '.env' en la raíz de BACKEND-IA.")
    print("2. Modifica 'DB_PASSWORD' y 'DATABASE_URL' con la contraseña real que")
    print("   definiste al instalar PostgreSQL en tu equipo.")
    print("   Ejemplo: DATABASE_URL=postgresql://postgres:MiPasswordReal@localhost:5432/sistema_violencia_db")
    print("3. Vuelve a ejecutar este script:")
    print("   .\\venv\\Scripts\\python.exe scripts\\test_db_connection.py")
print("=" * 60)
