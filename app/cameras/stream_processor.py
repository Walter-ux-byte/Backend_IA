"""
Procesador de Flujos de Video en Segundo Plano con OpenCV.
RF-01: Captura de WEBCAM, MP4 y RTSP.
RF-19: Estados de cámara (Conectada, Desconectada, Error, Reconectando).
RNF-02: Medición de latencia y FPS reales.
RNF-06: Procesamiento aislado por cámara sin bloquear HTTP.
"""
import os
import time
import threading
from typing import Optional, Callable, Any
import cv2
import numpy as np

from app.models.enums import EstadoCamara, TipoFuenteCamara


class StreamProcessor:
    def __init__(
        self,
        camera_id: int,
        source: str,
        source_type: TipoFuenteCamara,
        target_fps: int = 25,
        status_callback: Optional[Callable[[int, EstadoCamara, Optional[str]], None]] = None
    ):
        self.camera_id = camera_id
        self.source = source
        self.source_type = source_type
        self.target_fps = max(1, min(60, target_fps))
        self.frame_delay = 1.0 / self.target_fps
        self.status_callback = status_callback

        # Control de hilos y ejecución
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Telemetría y estadísticas
        self.estado: EstadoCamara = EstadoCamara.DESCONECTADA
        self.fps_actual: float = 0.0
        self.latencia_ms: float = 0.0
        self.frames_procesados: int = 0
        self.reconexiones: int = 0
        self.ultimo_error: Optional[str] = None

        # Buffers de fotogramas
        self._last_raw_frame: Optional[np.ndarray] = None
        self._last_jpeg_bytes: Optional[bytes] = None

        # Callbacks para IA (Fase 5)
        self._ai_callbacks: list[Callable[[np.ndarray, int], Any]] = []

        # Configuración de reconexión
        self.max_retries = 5
        self.retry_delay = 2.0

    def _set_status(self, nuevo_estado: EstadoCamara, error: Optional[str] = None):
        self.estado = nuevo_estado
        self.ultimo_error = error
        if self.status_callback:
            try:
                self.status_callback(self.camera_id, nuevo_estado, error)
            except Exception:
                pass

    def _open_capture(self) -> Optional[cv2.VideoCapture]:
        """Abre la captura de OpenCV según el tipo de fuente."""
        try:
            if self.source_type == TipoFuenteCamara.WEBCAM:
                # Si el source es "0", "1", etc., convertir a entero
                device_index = int(self.source) if self.source.isdigit() else 0
                cap = cv2.VideoCapture(device_index)
            elif self.source_type == TipoFuenteCamara.MP4:
                if not os.path.exists(self.source):
                    self.ultimo_error = f"Archivo de video no encontrado: {self.source}"
                    return None
                cap = cv2.VideoCapture(self.source)
            elif self.source_type == TipoFuenteCamara.RTSP:
                # Parámetros optimizados para bajo retraso en streams RTSP
                cap = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)
            else:
                cap = cv2.VideoCapture(self.source)

            if cap and cap.isOpened():
                return cap
            return None
        except Exception as e:
            self.ultimo_error = f"Error al abrir fuente de video: {str(e)}"
            return None

    def start(self):
        """Inicia el hilo de captura en segundo plano."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._capture_loop,
            name=f"CameraStream-{self.camera_id}",
            daemon=True
        )
        self._thread.start()

    def stop(self):
        """Detiene la captura de video y libera recursos de OpenCV."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._set_status(EstadoCamara.DESCONECTADA)

    def _capture_loop(self):
        """Bucle principal de lectura y procesamiento de fotogramas."""
        retries = 0

        while self._running:
            self._set_status(EstadoCamara.RECONECTANDO if retries > 0 else EstadoCamara.DESCONECTADA)
            cap = self._open_capture()

            if not cap or not cap.isOpened():
                retries += 1
                self.reconexiones += 1
                err_msg = f"No se pudo conectar a la cámara (Intento {retries}/{self.max_retries})"
                self._set_status(EstadoCamara.RECONECTANDO, err_msg)

                if retries >= self.max_retries:
                    self._set_status(EstadoCamara.ERROR, f"Fallo definitivo de conexión tras {self.max_retries} intentos.")
                    break

                time.sleep(self.retry_delay)
                continue

            # Conexión establecida
            self._set_status(EstadoCamara.CONECTADA)
            retries = 0
            last_fps_calc = time.time()
            frames_in_second = 0

            while self._running:
                start_time = time.time()
                ret, frame = cap.read()

                if not ret or frame is None:
                    # En archivos MP4, reiniciar al principio para pruebas continuas
                    if self.source_type == TipoFuenteCamara.MP4:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = cap.read()
                        if not ret or frame is None:
                            break
                    else:
                        break

                # Medir latencia de captura y codificación
                encode_start = time.time()
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                jpeg_bytes = buffer.tobytes()
                latencia = (time.time() - encode_start) * 1000.0

                with self._lock:
                    self._last_raw_frame = frame
                    self._last_jpeg_bytes = jpeg_bytes
                    self.frames_procesados += 1
                    self.latencia_ms = round(latencia, 2)

                # Ejecutar callbacks de IA (YOLO / MediaPipe) si existen
                for cb in self._ai_callbacks:
                    try:
                        cb(frame, self.camera_id)
                    except Exception:
                        pass

                # Cálculo de FPS reales
                frames_in_second += 1
                now = time.time()
                if now - last_fps_calc >= 1.0:
                    self.fps_actual = round(frames_in_second / (now - last_fps_calc), 1)
                    frames_in_second = 0
                    last_fps_calc = now

                # Control de ritmo para no saturar CPU
                elapsed = time.time() - start_time
                sleep_time = self.frame_delay - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

            cap.release()

            if self._running:
                retries += 1
                self.reconexiones += 1
                self._set_status(EstadoCamara.RECONECTANDO, "Señal de video interrumpida. Reconectando...")
                time.sleep(self.retry_delay)

        self._set_status(EstadoCamara.DESCONECTADA)

    def get_last_frame_jpeg(self) -> Optional[bytes]:
        """Devuelve el último fotograma codificado en formato JPEG de manera segura."""
        with self._lock:
            return self._last_jpeg_bytes

    def get_last_raw_frame(self) -> Optional[np.ndarray]:
        """Devuelve el último fotograma OpenCV en formato array BGR."""
        with self._lock:
            return self._last_raw_frame.copy() if self._last_raw_frame is not None else None

    def register_ai_callback(self, callback: Callable[[np.ndarray, int], Any]):
        """Permite registrar funciones de detección de IA para recibir cada fotograma."""
        if callback not in self._ai_callbacks:
            self._ai_callbacks.append(callback)

    def get_telemetry(self) -> dict:
        """Devuelve las métricas en tiempo real de la cámara."""
        return {
            "estado": self.estado,
            "fps_actual": self.fps_actual,
            "latencia_ms": self.latencia_ms,
            "frames_procesados": self.frames_procesados,
            "reconexiones": self.reconexiones,
            "captura_activa": self._running,
            "ultimo_error": self.ultimo_error
        }
