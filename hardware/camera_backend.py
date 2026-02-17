"""CameraBackend - REAL HARDWARE - 8MP IMX219 - KEINE STUBS"""
import time
import numpy as np
import threading
from typing import Optional, Tuple
from picamera2 import Picamera2


class CameraBackend:
    """Real PiCamera2 - 8MP IMX219 - no stubs, no fallbacks"""

    def __init__(
        self,
        preview_size: Tuple[int, int] = (640, 480),
        capture_size: Tuple[int, int] = (3280, 2464),
        preview_fps: int = 24
    ):
        print("[CameraBackend] Init REAL PiCamera2 - 8MP IMX219")
        self.preview_size = preview_size
        self.capture_size = capture_size
        self.preview_fps  = preview_fps
        self.is_running   = False
        self._frame_lock  = threading.Lock()
        self._last_frame: Optional[np.ndarray] = None

        self.camera = Picamera2()
        self._configure_preview()

        print(f"[CameraBackend] ✓ Ready: {preview_size[0]}x{preview_size[1]} @ {preview_fps}fps")

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
        self.camera.start()
        self.is_running = True
        time.sleep(0.15)
        print("[CameraBackend] ✓ Preview started")

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
            print(f"[CameraBackend] capture_array failed: {e}")
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
            print(f"[CameraBackend] ✓ Photo: {filepath}")
            return True
        except Exception as e:
            print(f"[CameraBackend] ✗ Photo failed: {e}")
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
            print("[CameraBackend] Cleanup done")
        except Exception:
            pass