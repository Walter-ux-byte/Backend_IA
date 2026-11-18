"""
Script de inicialización y verificación de Base de Datos.
1. Valida conectividad a PostgreSQL.
2. Crea la base de datos 'sistema_violencia_db' si no existe.
3. Genera las tablas requeridas mediante SQLAlchemy Base.metadata.
4. Siembra un usuario administrador inicial si la base está vacía.
"""
import sys
import os

# Asegurar path de app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.models import User, RolUsuario
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import bcrypt


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def check_and_create_database():
    """Conecta a la base postgres por defecto y crea sistema_violencia_db si no existe."""
    db_name = settings.DB_NAME
    user = settings.DB_USER
    password = settings.DB_PASSWORD
    host = settings.DB_HOST
    port = settings.DB_PORT

    print(f"[*] Verificando base de datos '{db_name}' en PostgreSQL ({host}:{port})...")
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=user,
            password=password,
            host=host,
            port=port,
            connect_timeout=5
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s;", (db_name,))
        exists = cur.fetchone()
        if not exists:
            print(f"[*] Creando base de datos '{db_name}'...")
            cur.execute(f'CREATE DATABASE "{db_name}" WITH ENCODING "UTF8";')
            print(f"[+] Base de datos '{db_name}' creada exitosamente.")
        else:
            print(f"[+] La base de datos '{db_name}' ya existe.")

        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[-] Error de conexión a PostgreSQL con las credenciales de .env: {e}")
        return False


def create_tables_and_seed():
    """Crea todas las tablas de SQLAlchemy y crea el usuario administrador inicial."""
    print("[*] Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("[+] Tablas creadas / verificadas:")
    for table_name in Base.metadata.tables.keys():
        print(f"    - {table_name}")

    # Sembrar usuario admin si no existe
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.usuario == "admin").first()
        if not admin_user:
            print("[*] Creando usuario administrador inicial por defecto (admin)...")
            new_admin = User(
                nombre="Administrador",
                apellido="Sistema",
                correo="admin@violenciadetector.local",
                usuario="admin",
                password_hash=hash_password("Admin1234*"),
                rol=RolUsuario.ADMINISTRADOR,
                activo=True
            )
            db.add(new_admin)
            db.commit()
            print("[+] Usuario administrador creado:")
            print("    Usuario: admin")
            print("    Password: Admin1234*")
            print("    Rol: ADMINISTRADOR")
        else:
            print(f"[+] Usuario '{admin_user.usuario}' ya existente.")
    finally:
        db.close()


if __name__ == "__main__":
    success = check_and_create_database()
    if success:
        create_tables_and_seed()
    else:
        print("\n" + "=" * 60)
        print("IMPORTANTE: Para conectar tu PostgreSQL local, asegúrate de que")
        print("la contraseña en el archivo .env coincida con la de tu usuario 'postgres'.")
        print("Ejemplo en .env:")
        print("DATABASE_URL=postgresql://postgres:TU_PASSWORD@localhost:5432/sistema_violencia_db")
        print("=" * 60 + "\n")
