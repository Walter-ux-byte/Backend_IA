"""
Módulo de Estimación de Posturas Corporales mediante Google MediaPipe.
RF-04, RF-07: Extracción de puntos clave corporales y clasificación de orientación.
"""
import math
from typing import Optional, Dict, Any, List, Tuple
import numpy as np

# Nombres de los puntos clave anatómicos relevantes de MediaPipe Pose
POSE_LANDMARK_NAMES = {
    0: "NOSE",
    11: "LEFT_SHOULDER", 12: "RIGHT_SHOULDER",
    13: "LEFT_ELBOW", 14: "RIGHT_ELBOW",
    15: "LEFT_WRIST", 16: "RIGHT_WRIST",
    23: "LEFT_HIP", 24: "RIGHT_HIP",
    25: "LEFT_KNEE", 26: "RIGHT_KNEE",
    27: "LEFT_ANKLE", 28: "RIGHT_ANKLE"
}


class PoseEstimator:
    def __init__(self, min_detection_confidence: float = 0.5, min_tracking_confidence: float = 0.5):
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self._pose = None
        self._mp_available = False
        self._init_mediapipe()

    def _init_mediapipe(self):
        try:
            import mediapipe as mp
            self.mp_pose = mp.solutions.pose
            self._pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence
            )
            self._mp_available = True
        except Exception:
            self._mp_available = False

    @property
    def is_available(self) -> bool:
        return self._mp_available

    def estimate_pose(self, frame: np.ndarray, crop_box: Optional[Tuple[int, int, int, int]] = None) -> Optional[Dict[str, Any]]:
        """
        Analiza el fotograma (o una región recortada de una persona).
        Retorna los puntos corporales, ángulo del torso y orientación.
        """
        if not self._mp_available or self._pose is None:
            return None

        h, w = frame.shape[:2]
        offset_x, offset_y = 0, 0

        # Si se pasa crop_box [x1, y1, x2, y2], recortar la persona para mayor precisión
        if crop_box:
            x1, y1, x2, y2 = [max(0, int(v)) for v in crop_box]
            x2 = min(w, x2)
            y2 = min(h, y2)
            if x2 > x1 and y2 > y1:
                frame_roi = frame[y1:y2, x1:x2]
                offset_x, offset_y = x1, y1
                h, w = frame_roi.shape[:2]
            else:
                frame_roi = frame
        else:
            frame_roi = frame

        try:
            import cv2
            rgb = cv2.cvtColor(frame_roi, cv2.COLOR_BGR2RGB)
            results = self._pose.process(rgb)

            if not results.pose_landmarks:
                return None

            landmarks = results.pose_landmarks.landmark
            keypoints_data = []

            for idx, lm in enumerate(landmarks):
                if idx in POSE_LANDMARK_NAMES:
                    # Coordenadas globales absolutas
                    abs_x = int(lm.x * w) + offset_x
                    abs_y = int(lm.y * h) + offset_y
                    keypoints_data.append({
                        "id": idx,
                        "name": POSE_LANDMARK_NAMES[idx],
                        "x": abs_x,
                        "y": abs_y,
                        "z": lm.z,
                        "visibility": round(lm.visibility, 3)
                    })

            # Calcular centro de hombros y centro de caderas para determinar inclinación del torso
            torso_angle, posture = self._calculate_torso_angle(landmarks, w, h)

            return {
                "keypoints": keypoints_data,
                "torso_angle": torso_angle,
                "posture": posture,
                "raw_landmarks": landmarks
            }
        except Exception:
            return None

    def _calculate_torso_angle(self, landmarks, w: int, h: int) -> Tuple[float, str]:
        """Calcula el ángulo de inclinación del torso con respecto a la vertical (grados)."""
        try:
            l_sh = landmarks[11]
            r_sh = landmarks[12]
            l_hip = landmarks[23]
            r_hip = landmarks[24]

            # Punto medio de hombros
            mid_sh_x = (l_sh.x + r_sh.x) / 2.0 * w
            mid_sh_y = (l_sh.y + r_sh.y) / 2.0 * h

            # Punto medio de caderas
            mid_hip_x = (l_hip.x + r_hip.x) / 2.0 * w
            mid_hip_y = (l_hip.y + r_hip.y) / 2.0 * h

            dx = mid_sh_x - mid_hip_x
            dy = mid_sh_y - mid_hip_y  # En imagen, Y crece hacia abajo

            # Ángulo con respecto a la vertical
            angle_rad = abs(math.atan2(dx, dy))
            angle_deg = round(math.degrees(angle_rad), 1)

            if angle_deg < 35.0:
                posture = "VERTICAL"
            elif angle_deg < 65.0:
                posture = "INCLINADO"
            else:
                posture = "HORIZONTAL"

            return angle_deg, posture
        except Exception:
            return 0.0, "VERTICAL"
