"""
Enumeraciones estandarizadas del sistema para roles, estados, prioridades y tipos.
"""
from enum import Enum


class RolUsuario(str, Enum):
    """RF-16: Roles de usuario del sistema."""
    ADMINISTRADOR = "ADMINISTRADOR"
    SEGURIDAD = "SEGURIDAD"
    SUPERVISOR = "SUPERVISOR"


class EstadoCamara(str, Enum):
    """RF-19: Estados de conexión de cámaras."""
    CONECTADA = "Conectada"
    DESCONECTADA = "Desconectada"
    ERROR = "Error"
    RECONECTANDO = "Reconectando"


class TipoFuenteCamara(str, Enum):
    """Fuentes de video soportadas."""
    WEBCAM = "WEBCAM"
    MP4 = "MP4"
    RTSP = "RTSP"


class TipoIncidente(str, Enum):
    """RF-15: Clasificación de incidentes detectados."""
    CAIDA = "Caída"
    POSIBLE_AGRESION = "Posible agresión"
    MOVIMIENTO_BRUSCO = "Movimiento brusco"
    PERSONA_INMOVIL = "Persona inmóvil"
    POSIBLE_SOLICITUD_AUXILIO = "Posible solicitud de auxilio"
    OTRO_EVENTO_SOSPECHOSO = "Otro evento sospechoso"


class NivelRiesgo(str, Enum):
    """Niveles de gravedad del incidente."""
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"


class EstadoIncidente(str, Enum):
    """RF-11 / RF-18: Ciclo de atención del incidente."""
    PENDIENTE = "PENDIENTE"
    EN_REVISION = "EN_REVISION"
    CONFIRMADO = "CONFIRMADO"
    DESCARTADO = "DESCARTADO"
    CERRADO = "CERRADO"


class PrioridadAlerta(str, Enum):
    """Prioridad para emisión de alertas."""
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"


class EstadoAlerta(str, Enum):
    """RF-14: Ciclo de vida de una alerta."""
    ACTIVA = "ACTIVA"
    CONFIRMADA = "CONFIRMADA"
    DESCARTADA = "DESCARTADA"
    CERRADA = "CERRADA"


class TipoEvidencia(str, Enum):
    """RF-12: Formato de archivo de evidencias almacenadas."""
    IMAGEN = "IMAGEN"
    VIDEO = "VIDEO"


class CanalNotificacion(str, Enum):
    """RF-09: Canales de emisión de notificaciones."""
    WEBSOCKET = "WEBSOCKET"
    EMAIL = "EMAIL"
