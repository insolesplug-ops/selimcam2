"""
CameraBackend - REAL HARDWARE
8MP IMX219 via PiCamera2 - KEINE STUBS
Pi 3A+ Optimiert
"""
import time
import logging
import numpy as np
import threading
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from picamera2 import Picamera2
    _PICAMERA2_IMPORT_ERROR = None
except Exception as exc:
    Picamera2 = None
    _PICAMERA2_IMPORT_ERROR = exc


class CameraBackend:
    """Real PiCamera2 - 8MP IMX219"""

    def __init__(
        self,
        preview_size: Tuple[int, int] = (640, 480),
        capture_size: Tuple[int, int] = (3280, 2464),
        preview_fps: int = 24
    ):
        if Picamera2 is None:
            raise RuntimeError(f"Picamera2 import failed: {_PICAMERA2_IMPORT_ERROR}")

        logger.info("CameraBackend init: real Picamera2 (IMX219)")

        self.preview_size = preview_size
        self.capture_size = capture_size
        self.preview_fps  = preview_fps
        self.is_running   = False
        self._frame_lock  = threading.Lock()
        self._last_frame: Optional[np.ndarray] = None
        self._Picamera2   = Picamera2

        self.camera = Picamera2()
        self._configure_preview()

        logger.info("CameraBackend ready: %dx%d @ %dfps", preview_size[0], preview_size[1], preview_fps)

    def _configure_preview(self):
        cfg = self.camera.create_preview_configuration(
            main={"size": self.preview_size, "format": "RGB888"},
            buffer_count=2,
            queue=False,
            controls={"FrameRate": float(self.preview_fps)}
        )
        self.camera.configure(cfg)

    def _configure_capture(self):
        cfg = self.camera.create_still_configuration(
            main={"size": self.capture_size, "format": "RGB888"}
        )
        self.camera.configure(cfg)

    def start_preview(self):
        if self.is_running:
            return
        try:
            self.camera.start()
            self.is_running = True
            time.sleep(0.15)
            logger.info("Camera preview started")
        except Exception as e:
            logger.error("Camera preview start failed: %s", e)
            raise

    def stop_preview(self):
        if not self.is_running:
            return
        try:
            self.camera.stop()
        except Exception:
            pass
        self.is_running = False

    def get_preview_frame(self) -> Optional[np.ndarray]:
        if not self.is_running:
            return None
        try:
            frame = self.camera.capture_array("main")
            with self._frame_lock:
                self._last_frame = frame
            return frame
        except Exception:
            return None

    def capture_array(self) -> Optional[np.ndarray]:
        if not self.is_running:
            return None
        try:
            return self.camera.capture_array("main").copy()
        except Exception as e:
            logger.error("Camera capture_array failed: %s", e)
            return None

    def capture_photo(self, filepath: str, quality: int = 92) -> bool:
        was_running = self.is_running
        try:
            if was_running:
                self.stop_preview()
            self._configure_capture()
            self.camera.start()
            time.sleep(0.2)
            self.camera.capture_file(filepath)
            self.camera.stop()
            if was_running:
                self._configure_preview()
                self.camera.start()
                self.is_running = True
            logger.info("Camera photo saved: %s", filepath)
            return True
        except Exception as e:
            logger.error("Camera photo capture failed: %s", e)
            if was_running:
                try:
                    self._configure_preview()
                    self.camera.start()
                    self.is_running = True
                except Exception:
                    self.is_running = False
            return False

    def set_controls(self, **controls):
        try:
            self.camera.set_controls(controls)
        except Exception:
            pass

    def cleanup(self):
        try:
            if self.is_running:
                self.camera.stop()
            self.camera.close()
            logger.info("Camera backend cleanup done")
        except Exception:
            pass