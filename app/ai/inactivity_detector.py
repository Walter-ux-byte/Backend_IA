"""
Detector de Inmovilidad Prolongada en Personas.
RF-06: Identifica cuando una persona permanece inmóvil en el suelo durante un tiempo configurable.
"""
import time
from typing import Dict, Any, Optional
from app.core.config import settings


class InactivityDetector:
    def __init__(self, threshold_seconds: float = None, movement_tolerance_px: float = 20.0):
        self.threshold_seconds = threshold_seconds or settings.INACTIVITY_THRESHOLD_SECONDS
        self.movement_tolerance_px = movement_tolerance_px
        # Historial: { person_id: { "anchor_pos": (x, y), "start_time": float, "last_active_time": float } }
        self._history: Dict[int, Dict[str, Any]] = {}

    def analyze(self, person_id: int, box: Dict[str, Any], pose_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analiza si una persona permanece estática sin movimiento por un periodo prolongado.
        """
        now = time.time()
        center_x = (box["x1"] + box["x2"]) / 2.0
        center_y = (box["y1"] + box["y2"]) / 2.0
        posture = pose_data.get("posture", "UNKNOWN") if pose_data else "UNKNOWN"

        hist = self._history.get(person_id)

        if hist is None:
            self._history[person_id] = {
                "anchor_x": center_x,
                "anchor_y": center_y,
                "still_start_time": now,
                "detected": False
            }
            return {"detected": False, "confidence": 0.0, "details": "Inicializando monitoreo"}

        # Distancia euclídea respecto a la posición ancla
        dx = center_x - hist["anchor_x"]
        dy = center_y - hist["anchor_y"]
        dist = (dx**2 + dy**2) ** 0.5

        if dist < self.movement_tolerance_px:
            # Sigue sin moverse significativamente
            duration = now - hist["still_start_time"]
            if duration >= self.threshold_seconds:
                confidence = 0.82
                if posture in ["HORIZONTAL", "INCLINADO"]:
                    confidence = 0.92  # Mayor gravedad si está en el suelo inmóvil

                return {
                    "detected": True,
                    "confidence": round(confidence, 2),
                    "details": f"Inmovilidad prolongada detectada: {round(duration, 1)}s sin desplazamiento (Postura: {posture})"
                }
        else:
            # Hubo movimiento significativo: reiniciar punto ancla y contador
            hist["anchor_x"] = center_x
            hist["anchor_y"] = center_y
            hist["still_start_time"] = now

        return {"detected": False, "confidence": 0.0, "details": "Movimiento activo"}

    def reset_person(self, person_id: int):
        self._history.pop(person_id, None)
