"""
Script CLI seguro para cambiar la contraseña del usuario administrador.
Permite actualizar la clave del admin directamente en PostgreSQL
o resetearla en caso de olvido.
"""
import sys
import os
import getpass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.enums import RolUsuario
from app.core.security import get_password_hash
from app.services.audit_service import AuditService


def change_admin_password():
    print("=" * 60)
    print("CAMBIO SEGURO DE CONTRASEÑA DE ADMINISTRADOR")
    print("=" * 60)

    username = input("Ingrese el nombre de usuario del administrador [default: admin]: ").strip() or "admin"

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.usuario == username.lower()).first()
        if not user:
            print(f"[-] Error: Usuario '{username}' no encontrado en la base de datos.")
            return

        if user.rol != RolUsuario.ADMINISTRADOR:
            print(f"[-] Error: El usuario '{username}' no tiene rol de ADMINISTRADOR.")
            return

        print(f"[+] Usuario '{user.usuario}' localizado ({user.nombre} {user.apellido} - {user.correo})")

        new_password = getpass.getpass("Ingrese la nueva contraseña segura (mínimo 6 caracteres): ")
        if len(new_password) < 6:
            print("[-] Error: La contraseña debe tener al menos 6 caracteres.")
            return

        confirm_password = getpass.getpass("Confirme la nueva contraseña: ")
        if new_password != confirm_password:
            print("[-] Error: Las contraseñas no coinciden.")
            return

        # Actualizar hash en base de datos
        user.password_hash = get_password_hash(new_password)
        db.commit()

        AuditService.log_event(
            db=db,
            accion="RESET_PASSWORD_CLI",
            entidad="usuarios",
            entidad_id=user.id,
            usuario_id=user.id,
            detalles="Contraseña de administrador actualizada mediante script CLI seguro."
        )

        print("\n[+] ¡Contraseña de administrador actualizada con éxito en PostgreSQL!")
        print(f"    Ahora puedes iniciar sesión en Swagger (/docs) con:")
        print(f"    Usuario: {user.usuario}")
        print(f"    Contraseña: (la que acabas de configurar)")
    finally:
        db.close()


if __name__ == "__main__":
    change_admin_password()
