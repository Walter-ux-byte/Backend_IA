"""
Detector Experimental de Posibles Gestos de Solicitud de Auxilio.
RF-07: Detección heurística de brazos en alto, agitación de manos o posturas de socorro.
"""
from typing import Dict, Any, Optional


class HelpGestureDetector:
    def __init__(self):
        pass

    def analyze(self, pose_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analiza los puntos anatómicos de brazos y muñecas para identificar gestos de ayuda.
        Retorna: { 'detected': bool, 'confidence': float, 'details': str }
        """
        if not pose_data or "keypoints" not in pose_data:
            return {"detected": False, "confidence": 0.0, "details": "Sin datos de postura"}

        kp_map = {kp["name"]: kp for kp in pose_data["keypoints"]}

        # Se requieren al menos nariz, hombros y muñecas visibles
        nose = kp_map.get("NOSE")
        l_sh = kp_map.get("LEFT_SHOULDER")
        r_sh = kp_map.get("RIGHT_SHOULDER")
        l_w = kp_map.get("LEFT_WRIST")
        r_w = kp_map.get("RIGHT_WRIST")

        if not (l_sh and r_sh and l_w and r_w):
            return {"detected": False, "confidence": 0.0, "details": "Extremidades no visibles"}

        # En coordenadas de imagen, menor Y = más alto
        # 1. Ambos brazos levantados por encima de los hombros (Gesto de auxilio / rendición)
        both_hands_up = (l_w["y"] < l_sh["y"]) and (r_w["y"] < r_sh["y"])

        # 2. Brazos por encima de la cabeza
        above_head = nose and (l_w["y"] < nose["y"]) and (r_w["y"] < nose["y"])

        if above_head:
            return {
                "detected": True,
                "confidence": 0.78,
                "details": "Posible gesto de auxilio (Experimental): Ambos brazos alzados por encima de la cabeza."
            }

        if both_hands_up:
            return {
                "detected": True,
                "confidence": 0.65,
                "details": "Posible solicitud de ayuda (Experimental): Manos levantadas sobre la altura de los hombros."
            }

        return {"detected": False, "confidence": 0.0, "details": "Sin gestos anormales de auxilio"}
