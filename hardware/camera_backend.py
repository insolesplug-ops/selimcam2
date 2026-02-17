"""
CameraBackend - REAL HARDWARE
8MP IMX219 via PiCamera2 - KEINE STUBS
Pi 3A+ Optimiert
"""
import time
import sys
import logging
import numpy as np
import threading
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _import_picamera2_safely():
    removed_path = None
    removed_module = None

    project_root_str = str(_PROJECT_ROOT)
    if project_root_str in sys.path:
        sys.path.remove(project_root_str)
        removed_path = project_root_str

    existing_libcamera = sys.modules.get("libcamera")
    if existing_libcamera is not None:
        module_file = getattr(existing_libcamera, "__file__", "") or ""
        if module_file.startswith(project_root_str):
            removed_module = existing_libcamera
            del sys.modules["libcamera"]

    try:
        from picamera2 import Picamera2 as _Picamera2
        return _Picamera2, None
    except Exception as exc:
        return None, exc
    finally:
        if removed_path is not None:
            sys.path.insert(0, removed_path)
        if removed_module is not None and "libcamera" not in sys.modules:
            sys.modules["libcamera"] = removed_module


Picamera2, _PICAMERA2_IMPORT_ERROR = _import_picamera2_safely()


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
        self._capture_thread: Optional[threading.Thread] = None
        self._capture_stop = threading.Event()
        self._capture_error_count = 0
        self._Picamera2   = Picamera2

        self.camera = Picamera2()
        self._configure_preview()

        logger.info("CameraBackend ready: %dx%d @ %dfps", preview_size[0], preview_size[1], preview_fps)

    def _configure_preview(self):
        cfg = self.camera.create_preview_configuration(
            main={"size": self.preview_size, "format": "RGB888"},
            lores={"size": self.preview_size, "format": "YUV420"},
            buffer_count=3,
            queue=True,
            controls={"FrameRate": float(self.preview_fps)}
        )
        self.camera.configure(cfg)

    def _capture_loop(self):
        while not self._capture_stop.is_set():
            try:
                request = self.camera.capture_request()
                frame = request.make_array("main")
                request.release()
                if frame is None:
                    continue

                if frame.ndim == 3 and frame.shape[2] >= 3:
                    frame_rgb = frame[:, :, :3]
                else:
                    frame_rgb = frame

                frame_contiguous = np.ascontiguousarray(frame_rgb)

                with self._frame_lock:
                    self._last_frame = frame_contiguous
                self._capture_error_count = 0
            except Exception as exc:
                self._capture_error_count += 1
                if self._capture_error_count <= 5 or self._capture_error_count % 30 == 0:
                    logger.error("Camera request loop error (%d): %s", self._capture_error_count, exc)
                time.sleep(0.01)

    def _configure_capture(self):
        cfg = self.camera.create_still_configuration(
            main={"size": self.capture_size, "format": "RGB888"}
        )
        self.camera.configure(cfg)

    def start_preview(self):
        if self.is_running:
            return
        try:
            self.camera.start(show_preview=False)
            self._capture_stop.clear()
            self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self._capture_thread.start()
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
            self._capture_stop.set()
            if self._capture_thread is not None:
                self._capture_thread.join(timeout=0.5)
                self._capture_thread = None
            self.camera.stop()
        except Exception:
            pass
        self.is_running = False

    def get_preview_frame(self) -> Optional[np.ndarray]:
        if not self.is_running:
            return None
        with self._frame_lock:
            return self._last_frame.copy() if self._last_frame is not None else None

    def capture_array(self) -> Optional[np.ndarray]:
        if not self.is_running:
            return None
        try:
            with self._frame_lock:
                if self._last_frame is not None:
                    return self._last_frame.copy()
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
                self.is_running = False
                self.start_preview()
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