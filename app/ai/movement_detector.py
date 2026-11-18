"""
Detector de Movimientos Bruscos y Desplazamientos Anormales.
RF-03: Análisis temporal de aceleración y velocidad corporal.
"""
import time
from typing import Dict, Any, Optional


class SuddenMovementDetector:
    def __init__(self, velocity_threshold_px_s: float = 350.0, acceleration_threshold: float = 600.0):
        self.velocity_threshold = velocity_threshold_px_s
        self.acceleration_threshold = acceleration_threshold
        # Historial: { person_id: { "last_pos": (x, y), "last_v": float, "last_t": float } }
        self._history: Dict[int, Dict[str, Any]] = {}

    def analyze(self, person_id: int, box: Dict[str, Any], pose_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        now = time.time()
        cx = (box["x1"] + box["x2"]) / 2.0
        cy = (box["y1"] + box["y2"]) / 2.0

        hist = self._history.get(person_id)

        if hist is None:
            self._history[person_id] = {
                "last_x": cx,
                "last_y": cy,
                "last_v": 0.0,
                "last_t": now
            }
            return {"detected": False, "confidence": 0.0, "details": "Inicializando"}

        dt = max(0.01, now - hist["last_t"])
        dist = ((cx - hist["last_x"])**2 + (cy - hist["last_y"])**2) ** 0.5
        velocity = dist / dt  # px/s
        acceleration = abs(velocity - hist["last_v"]) / dt

        # Actualizar historial
        hist["last_x"] = cx
        hist["last_y"] = cy
        hist["last_v"] = velocity
        hist["last_t"] = now

        # Detección de aceleración o velocidad brusca inusual
        if velocity > self.velocity_threshold or acceleration > self.acceleration_threshold:
            confidence = min(0.95, round(velocity / (self.velocity_threshold * 1.5), 2))
            return {
                "detected": True,
                "confidence": max(0.65, confidence),
                "details": f"Movimiento brusco detectado: velocidad {int(velocity)} px/s, aceleración {int(acceleration)} px/s²"
            }

        return {"detected": False, "confidence": 0.0, "details": "Movimiento dentro de parámetros normales"}

    def reset_person(self, person_id: int):
        self._history.pop(person_id, None)
