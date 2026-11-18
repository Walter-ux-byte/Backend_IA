"""
Pipeline Central de Inteligencia Artificial y Visión Computacional.
Integra y coordina en tiempo real: YOLO, MediaPipe, Detectores de Caídas,
Inmovilidad, Movimientos Bruscos, Gestos de Auxilio y Violencia.
"""
from datetime import datetime, timezone
import time
import base64
from typing import Dict, Any, List, Optional
import cv2
import numpy as np

from app.schemas.ai import FrameAnalysisResult, PersonDetection, BoundingBox, Keypoint, IncidentSignal
from app.ai.person_detector import PersonDetector
from app.ai.pose_estimator import PoseEstimator
from app.ai.fall_detector import FallDetector
from app.ai.inactivity_detector import InactivityDetector
from app.ai.movement_detector import SuddenMovementDetector
from app.ai.help_gesture_detector import HelpGestureDetector
from app.ai.violence_detector import ViolenceDetector
from app.core.config import settings


class AIPipeline:
    def __init__(self):
        self.person_detector = PersonDetector(
            confidence_threshold=settings.CONFIDENCE_THRESHOLD,
            device=settings.DEVICE
        )
        self.pose_estimator = PoseEstimator()
        self.fall_detector = FallDetector()
        self.inactivity_detector = InactivityDetector()
        self.movement_detector = SuddenMovementDetector()
        self.help_detector = HelpGestureDetector()
        self.violence_detector = ViolenceDetector()

        # Registro de cámaras con análisis de IA activado
        self.enabled_camera_ids: set[int] = set()

    def enable_camera(self, camera_id: int):
        self.enabled_camera_ids.add(camera_id)

    def disable_camera(self, camera_id: int):
        self.enabled_camera_ids.discard(camera_id)

    def is_camera_enabled(self, camera_id: int) -> bool:
        return camera_id in self.enabled_camera_ids

    def process_frame(
        self,
        frame: np.ndarray,
        camera_id: Optional[int] = None,
        include_annotated_image: bool = False
    ) -> FrameAnalysisResult:
        """
        Ejecuta el pipeline completo de visión por computadora sobre el fotograma.
        Retorna personas detectadas, posturas, señales de riesgo y latencia de inferencia.
        """
        start_time = time.time()
        detected_persons = self.person_detector.detect_and_track(frame, persist=True)

        persons_out: List[PersonDetection] = []
        signals_out: List[IncidentSignal] = []
        movement_signals: List[Dict[str, Any]] = []

        for p in detected_persons:
            pid = p["person_id"]
            box_data = p["box"]
            bbox = BoundingBox(**box_data)

            # Estimación de postura con MediaPipe usando ROI de la persona
            crop_box = (int(box_data["x1"]), int(box_data["y1"]), int(box_data["x2"]), int(box_data["y2"]))
            pose_res = self.pose_estimator.estimate_pose(frame, crop_box=crop_box)

            keypoints_list: Optional[List[Keypoint]] = None
            torso_angle = 0.0
            posture = "VERTICAL"

            if pose_res:
                keypoints_list = [Keypoint(**kp) for kp in pose_res.get("keypoints", [])]
                torso_angle = pose_res.get("torso_angle", 0.0)
                posture = pose_res.get("posture", "VERTICAL")

            persons_out.append(PersonDetection(
                person_id=pid,
                box=bbox,
                torso_angle=torso_angle,
                posture=posture,
                keypoints=keypoints_list
            ))

            # 1. Detector de Caídas (RF-04)
            fall_res = self.fall_detector.analyze(pid, box_data, pose_res)
            if fall_res.get("detected"):
                signals_out.append(IncidentSignal(
                    tipo="Caída",
                    detectado=True,
                    confianza=fall_res["confianza"] if "confianza" in fall_res else fall_res.get("confidence", 0.8),
                    detalles=f"Persona #{pid}: {fall_res.get('details', '')}"
                ))

            # 2. Detector de Inmovilidad Prolongada (RF-06)
            inactivity_res = self.inactivity_detector.analyze(pid, box_data, pose_res)
            if inactivity_res.get("detected"):
                signals_out.append(IncidentSignal(
                    tipo="Persona inmóvil",
                    detectado=True,
                    confianza=inactivity_res.get("confidence", 0.85),
                    detalles=f"Persona #{pid}: {inactivity_res.get('details', '')}"
                ))

            # 3. Detector de Movimientos Bruscos (RF-03)
            move_res = self.movement_detector.analyze(pid, box_data, pose_res)
            movement_signals.append(move_res)
            if move_res.get("detected"):
                signals_out.append(IncidentSignal(
                    tipo="Movimiento brusco",
                    detectado=True,
                    confianza=move_res.get("confidence", 0.75),
                    detalles=f"Persona #{pid}: {move_res.get('details', '')}"
                ))

            # 4. Detector de Gestos de Auxilio (RF-07)
            help_res = self.help_detector.analyze(pose_res)
            if help_res.get("detected"):
                signals_out.append(IncidentSignal(
                    tipo="Posible solicitud de auxilio",
                    detectado=True,
                    confianza=help_res.get("confidence", 0.65),
                    detalles=f"Persona #{pid}: {help_res.get('details', '')}",
                    es_heuristico=True
                ))

        # 5. Detector de Posibles Peleas y Agresiones (RF-05)
        violence_res = self.violence_detector.analyze(detected_persons, movement_signals)
        if violence_res.get("detected"):
            signals_out.append(IncidentSignal(
                tipo="Posible agresión",
                detectado=True,
                confianza=violence_res.get("confidence", 0.65),
                detalles=violence_res.get("details", ""),
                es_heuristico=violence_res.get("is_heuristic", True)
            ))

        latency_ms = round((time.time() - start_time) * 1000.0, 2)

        # Generar imagen anotada en base64 si fue solicitada
        image_b64 = None
        if include_annotated_image:
            annotated = self.person_detector.draw_annotations(frame, detected_persons)
            _, buffer = cv2.imencode('.jpg', annotated)
            image_b64 = base64.b64encode(buffer).decode('utf-8')

        return FrameAnalysisResult(
            timestamp=datetime.now(timezone.utc).isoformat(),
            camera_id=camera_id,
            num_personas=len(persons_out),
            personas=persons_out,
            senales_riesgo=signals_out,
            latencia_ms=latency_ms,
            imagen_anotada_b64=image_b64
        )


# Instancia singleton del pipeline de IA
ai_pipeline = AIPipeline()
