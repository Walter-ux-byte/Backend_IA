"""
Detector de Caídas basado en Análisis Postural y Dinámica Temporal.
RF-04: Detección de posibles caídas evaluando relación de aspecto,
inclinación del torso y permanencia temporal en el suelo.
"""
import time
from typing import Dict, Any, Optional
from app.core.config import settings


class FallDetector:
    def __init__(self, confirmation_seconds: float = None):
        self.confirmation_seconds = confirmation_seconds or settings.FALL_CONFIRMATION_SECONDS
        # Historial de estados por persona: { person_id: { "start_time": float, "last_y": float, "last_t": float, "state": str } }
        self._tracking_history: Dict[int, Dict[str, Any]] = {}

    def analyze(self, person_id: int, box: Dict[str, Any], pose_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analiza si una persona ha sufrido una caída potencialmente peligrosa.
        Retorna: { 'detected': bool, 'confidence': float, 'details': str }
        """
        now = time.time()
        w = max(1.0, box["x2"] - box["x1"])
        h = max(1.0, box["y2"] - box["y1"])
        center_y = (box["y1"] + box["y2"]) / 2.0
        aspect_ratio = w / h  # Si aspect_ratio > 1.1, la persona está más ancha que alta (horizontal)

        # 1. Comprobación postural
        posture = pose_data.get("posture", "VERTICAL") if pose_data else "UNKNOWN"
        torso_angle = pose_data.get("torso_angle", 0.0) if pose_data else 0.0

        is_horizontal = (aspect_ratio >= 1.15) or (posture == "HORIZONTAL") or (torso_angle >= 60.0)

        hist = self._tracking_history.get(person_id)

        if hist is None:
            self._tracking_history[person_id] = {
                "start_horizontal_time": now if is_horizontal else None,
                "last_center_y": center_y,
                "last_time": now,
                "detected": False
            }
            return {"detected": False, "confidence": 0.0, "details": "Inicializando seguimiento"}

        # Calcular velocidad descendente (si cayó rápidamente)
        dt = max(0.01, now - hist["last_time"])
        velocity_y = (center_y - hist["last_center_y"]) / dt  # positivo = hacia abajo
        hist["last_center_y"] = center_y
        hist["last_time"] = now

        if is_horizontal:
            if hist["start_horizontal_time"] is None:
                hist["start_horizontal_time"] = now

            duration_in_ground = now - hist["start_horizontal_time"]

            # Confirmar si ha permanecido en el suelo el tiempo mínimo estipulado
            if duration_in_ground >= self.confirmation_seconds:
                confidence = 0.85
                if posture == "HORIZONTAL":
                    confidence += 0.10
                if velocity_y > 80:  # Caída con impacto rápido previo
                    confidence = min(0.98, confidence + 0.04)

                hist["detected"] = True
                return {
                    "detected": True,
                    "confidence": round(confidence, 2),
                    "details": f"Posible caída confirmada: postura horizontal durante {round(duration_in_ground, 1)}s (Torso: {torso_angle}°)"
                }
        else:
            # Si se levanta, reiniciar contador
            hist["start_horizontal_time"] = None
            hist["detected"] = False

        return {"detected": False, "confidence": 0.0, "details": f"Postura: {posture}"}

    def reset_person(self, person_id: int):
        self._tracking_history.pop(person_id, None)
