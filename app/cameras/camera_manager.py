"""
Administrador Centralizado de Flujos de Cámaras (CameraManager).
RF-01: Visualización y streaming en tiempo real.
RF-19: Estados de cámara y reconexión automática.
RNF-06: Aislamiento de fallos entre cámaras.
"""
from typing import Dict, Optional, Generator
import time
import cv2
import numpy as np

from app.models.enums import EstadoCamara, TipoFuenteCamara
from app.cameras.stream_processor import StreamProcessor
from app.core.database import SessionLocal
from app.repositories.camera_repository import CameraRepository


class CameraManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CameraManager, cls).__new__(cls)
            cls._instance._processors: Dict[int, StreamProcessor] = {}
        return cls._instance

    def _update_db_status(self, camera_id: int, estado: EstadoCamara, error: Optional[str] = None):
        """Callback para sincronizar el estado en tiempo real con la base de datos."""
        try:
            with SessionLocal() as db:
                repo = CameraRepository(db)
                repo.update_status(camera_id, estado)
        except Exception:
            pass

    def start_camera(
        self,
        camera_id: int,
        source: str,
        source_type: TipoFuenteCamara,
        target_fps: int = 25
    ) -> StreamProcessor:
        """Inicia o reinicia el procesador de video para una cámara."""
        if camera_id in self._processors:
            processor = self._processors[camera_id]
            if processor._running:
                return processor
            processor.stop()

        processor = StreamProcessor(
            camera_id=camera_id,
            source=source,
            source_type=source_type,
            target_fps=target_fps,
            status_callback=self._update_db_status
        )
        self._processors[camera_id] = processor
        processor.start()
        return processor

    def stop_camera(self, camera_id: int) -> bool:
        """Detiene la captura de una cámara."""
        if camera_id in self._processors:
            self._processors[camera_id].stop()
            self._update_db_status(camera_id, EstadoCamara.DESCONECTADA)
            del self._processors[camera_id]
            return True
        return False

    def stop_all(self):
        """Detiene todas las cámaras activas al apagar el servidor."""
        for camera_id in list(self._processors.keys()):
            self.stop_camera(camera_id)

    def get_processor(self, camera_id: int) -> Optional[StreamProcessor]:
        return self._processors.get(camera_id)

    def get_status(self, camera_id: int) -> dict:
        """Obtiene la telemetría en tiempo real o el estado inactivo."""
        processor = self._processors.get(camera_id)
        if processor:
            return processor.get_telemetry()
        return {
            "estado": EstadoCamara.DESCONECTADA,
            "fps_actual": 0.0,
            "latencia_ms": 0.0,
            "frames_procesados": 0,
            "reconexiones": 0,
            "captura_activa": False,
            "ultimo_error": None
        }

    def generate_placeholder_frame(self, text: str = "SIN SENAL") -> bytes:
        """Genera un fotograma JPEG con fondo negro y mensaje de estado cuando no hay señal."""
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, text, (180, 240), font, 1.2, (0, 0, 255), 3, cv2.LINE_AA)
        cv2.putText(img, time.strftime("%Y-%m-%d %H:%M:%S"), (190, 290), font, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
        _, buffer = cv2.imencode('.jpg', img)
        return buffer.tobytes()

    def generate_mjpeg_stream(self, camera_id: int, max_frames: Optional[int] = None) -> Generator[bytes, None, None]:
        """
        Generador para streaming de video MJPEG continuo (multipart/x-mixed-replace).
        Compatible con navegadores web, tags <img> y aplicaciones React.
        Permite limitar max_frames para pruebas o capturas puntuales.
        """
        frames_sent = 0
        while True:
            if max_frames is not None and frames_sent >= max_frames:
                break

            processor = self._processors.get(camera_id)
            if processor and processor._running:
                frame_bytes = processor.get_last_frame_jpeg()
                if frame_bytes is None:
                    frame_bytes = self.generate_placeholder_frame("CONECTANDO...")
            else:
                frame_bytes = self.generate_placeholder_frame("CAMARA INACTIVA")

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )
            frames_sent += 1
            time.sleep(0.04)  # ~25 FPS máximo para el streaming HTTP


# Instancia singleton accesible globalmente
camera_manager = CameraManager()
