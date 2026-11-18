"""
Módulo centralizado de Inteligencia Artificial y Visión Computacional.
Exporta el pipeline de IA y los detectores individuales.
"""
from app.ai.person_detector import PersonDetector
from app.ai.pose_estimator import PoseEstimator
from app.ai.fall_detector import FallDetector
from app.ai.inactivity_detector import InactivityDetector
from app.ai.movement_detector import SuddenMovementDetector
from app.ai.help_gesture_detector import HelpGestureDetector
from app.ai.violence_detector import ViolenceDetector, IViolenceActionModel
from app.ai.pipeline import ai_pipeline, AIPipeline

__all__ = [
    "PersonDetector",
    "PoseEstimator",
    "FallDetector",
    "InactivityDetector",
    "SuddenMovementDetector",
    "HelpGestureDetector",
    "ViolenceDetector",
    "IViolenceActionModel",
    "ai_pipeline",
    "AIPipeline",
]
