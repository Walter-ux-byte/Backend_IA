"""
Módulo de Detección de Posibles Peleas, Agresiones y Forcejeos.
RF-05: Interfaz para modelos de reconocimiento de acciones en video (SlowFast, VideoMAE)
y detector heurístico experimental claramente identificado.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np


class IViolenceActionModel(ABC):
    """Interfaz estándar para conectar modelos entrenados de reconocimiento de violencia."""

    @abstractmethod
    def predict(self, frame_sequence: List[np.ndarray]) -> Dict[str, Any]:
        """
        Recibe una secuencia temporal de fotogramas y devuelve la probabilidad de violencia.
        Retorna: { 'detected': bool, 'confidence': float, 'action_label': str }
        """
        pass


class ViolenceDetector:
    def __init__(self):
        self._custom_model: Optional[IViolenceActionModel] = None

    def register_custom_action_model(self, model: IViolenceActionModel):
        """Permite conectar un modelo de Deep Learning entrenado para detección de violencia."""
        self._custom_model = model

    def analyze(
        self,
        persons: List[Dict[str, Any]],
        movement_signals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analiza si existe un posible forcejeo o pelea entre 2 o más personas presentes.
        Si no hay un modelo neuronal acoplado, utiliza el detector heurístico experimental.
        """
        # Si existe un modelo entrenado registrado, usarlo
        if self._custom_model is not None:
            return self._custom_model.predict([])

        # Detector Heurístico Experimental
        if len(persons) < 2:
            return {
                "detected": False,
                "confidence": 0.0,
                "is_heuristic": True,
                "details": "Menos de 2 personas en escena; no aplica forcejeo interpersonal."
            }

        # Evaluar proximidad física y solapamiento de bounding boxes
        close_interactions = 0
        for i in range(len(persons)):
            for j in range(i + 1, len(persons)):
                b1 = persons[i]["box"]
                b2 = persons[j]["box"]

                iou = self._calculate_iou(b1, b2)
                # Si hay solapamiento significativo de cuerpos (forcejeo/contacto directo)
                if iou > 0.12:
                    close_interactions += 1

        # Evaluar si coincide con movimientos bruscos activos
        has_abrupt_movement = any(m.get("detectado", False) for m in movement_signals)

        if close_interactions >= 1 and has_abrupt_movement:
            return {
                "detected": True,
                "confidence": 0.65,
                "is_heuristic": True,
                "details": "Posible agresión / forcejeo detectado mediante análisis heurístico experimental (Contacto físico estrecho y movimiento brusco simultáneo)."
            }

        return {
            "detected": False,
            "confidence": 0.0,
            "is_heuristic": True,
            "details": "Distanciamiento normal o ausencia de movimientos agresivos."
        }

    def _calculate_iou(self, b1: Dict[str, Any], b2: Dict[str, Any]) -> float:
        """Calcula Intersection over Union (IoU) entre dos bounding boxes."""
        xA = max(b1["x1"], b2["x1"])
        yA = max(b1["y1"], b2["y1"])
        xB = min(b1["x2"], b2["x2"])
        yB = min(b1["y2"], b2["y2"])

        interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
        boxAArea = max(1.0, (b1["x2"] - b1["x1"]) * (b1["y2"] - b1["y1"]))
        boxBArea = max(1.0, (b2["x2"] - b2["x1"]) * (b2["y2"] - b2["y1"]))

        iou = interArea / float(boxAArea + boxBArea - interArea)
        return round(iou, 3)
