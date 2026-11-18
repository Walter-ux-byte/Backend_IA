"""
Módulo de Detección y Seguimiento Temporal de Personas mediante YOLO (Ultralytics).
RF-02: Detección de personas, coordenadas, confianza y seguimiento temporal (tracking).
"""
from typing import List, Dict, Any, Optional
import numpy as np
import cv2
from app.core.config import settings


class PersonDetector:
    _model = None

    def __init__(self, confidence_threshold: float = 0.45, device: str = "cpu"):
        self.confidence_threshold = confidence_threshold
        self.device = device
        self._yolo_available = False
        self._load_model()

    def _load_model(self):
        """Carga perezosa del modelo YOLOv8 Nano para personas."""
        try:
            from ultralytics import YOLO
            if PersonDetector._model is None:
                # yolov8n.pt es el modelo ligero estándar de 3.2M de parámetros optimizado para CPU
                PersonDetector._model = YOLO("yolov8n.pt")
            self.model = PersonDetector._model
            self._yolo_available = True
        except Exception:
            self._yolo_available = False

    @property
    def is_available(self) -> bool:
        return self._yolo_available

    def detect_and_track(self, frame: np.ndarray, persist: bool = True) -> List[Dict[str, Any]]:
        """
        Ejecuta la inferencia de YOLO y seguimiento temporal sobre el fotograma.
        Filtra únicamente la clase 'person' (clase 0 en COCO).
        """
        if not self._yolo_available:
            return []

        try:
            # Ejecutar tracking con BoT-SORT / ByteTrack
            results = self.model.track(
                frame,
                persist=persist,
                classes=[0],  # 0 = person
                conf=self.confidence_threshold,
                device=self.device,
                verbose=False
            )

            detected_persons = []
            if results and len(results) > 0:
                boxes = results[0].boxes
                if boxes is not None:
                    for i, box in enumerate(boxes):
                        xyxy = box.xyxy[0].cpu().numpy()
                        conf = float(box.conf[0].cpu().numpy())
                        cls_id = int(box.cls[0].cpu().numpy())

                        track_id = int(box.id[0].cpu().numpy()) if box.id is not None else i + 1

                        if cls_id == 0:  # Confirmar que sea persona
                            detected_persons.append({
                                "person_id": track_id,
                                "box": {
                                    "x1": round(float(xyxy[0]), 1),
                                    "y1": round(float(xyxy[1]), 1),
                                    "x2": round(float(xyxy[2]), 1),
                                    "y2": round(float(xyxy[3]), 1),
                                    "confidence": round(conf, 3),
                                    "track_id": track_id
                                }
                            })

            return detected_persons
        except Exception:
            return []

    def draw_annotations(self, frame: np.ndarray, persons: List[Dict[str, Any]]) -> np.ndarray:
        """Dibuja bounding boxes y etiquetas sobre el fotograma."""
        annotated = frame.copy()
        for p in persons:
            b = p["box"]
            x1, y1, x2, y2 = int(b["x1"]), int(b["y1"]), int(b["x2"]), int(b["y2"])
            track_id = b.get("track_id", "?")
            conf = b.get("confidence", 0.0)

            # Rectángulo verde de persona
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Etiqueta con ID y confianza
            label = f"Persona #{track_id} ({int(conf * 100)}%)"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - 20), (x1 + tw + 6, y1), (0, 255, 0), -1)
            cv2.putText(annotated, label, (x1 + 3, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

        return annotated
