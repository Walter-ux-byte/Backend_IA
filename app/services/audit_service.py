"""
Servicio centralizado de Auditoría para trazabilidad de eventos de seguridad.
RNF-04: Registro inmutable de acciones administrativas y de seguridad.
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.audit import AuditLog


class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        accion: str,
        entidad: str,
        entidad_id: Optional[int] = None,
        usuario_id: Optional[int] = None,
        detalles: Optional[str] = None,
        ip_origen: Optional[str] = None
    ) -> AuditLog:
        """Crea y persiste un registro de auditoría en la base de datos."""
        log_entry = AuditLog(
            usuario_id=usuario_id,
            accion=accion,
            entidad=entidad,
            entidad_id=entidad_id,
            detalles=detalles,
            ip_origen=ip_origen
        )
        db.add(log_entry)
        try:
            db.commit()
            db.refresh(log_entry)
        except Exception:
            db.rollback()
        return log_entry
