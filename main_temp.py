"""
SelimCam v2.0 - PRODUCTION BUILD
Pi 3A+ | 8MP Camera | Waveshare 4.3" DSI
FIXES: KMS Hardware Rotation 180deg, Touch Mapping, Debug Logging
import sys
import pygame
import time
import signal
import threading
import traceback
import json
from pathlib import Path
from typing import Optional
from collections import deque

try:
    import psutil
except ImportError:
    psutil = None

APP_ROOT = Path(__file__).resolve().parent
os.chdir(APP_ROOT)
HEALTH_FILE = Path("/home/pi/camera_app_data/selimcam_health.json")

if not os.environ.get("XDG_RUNTIME_DIR"):
    fallback_runtime = f"/run/user/{os.getuid()}"
    os.environ["XDG_RUNTIME_DIR"] = fallback_runtime if os.path.isdir(fallback_runtime) else "/tmp"

# ============================================================
# PLATFORM - HARDCODED PI MODE
# ============================================================

# FORCE PI MODE - Pi 3A+ hardcoded
IS_RASPBERRY_PI = True
print("[Platform] Raspberry Pi 3A+ - FORCE MODE")

# ============================================================
# DISPLAY ROTATION CONSTANTS
# ============================================================
# KMS Hardware rotation: SDL_VIDEO_KMSDRM_ROTATION="2" (180 degrees)
# - Logical app space: portrait (480x800), no software rotation
# - Physical framebuffer: landscape (800x480), rotated 180 degrees by KMS
# - Touch mapping: (480-x_raw, 800-y_raw) for 180 degree HW rotation

LOGICAL_W  = 480
LOGICAL_H  = 800
PHYSICAL_W = 800
PHYSICAL_H = 480

# ============================================================
# CORE IMPORTS
# ============================================================

from core.config_manager import ConfigManager
from core.state_machine import StateMachine, AppState, AppEvent
from core.resource_manager import ResourceManager
from core.photo_manager import PhotoManager
from core.logger import logger

# ============================================================
# HITBOX SYSTEM
# ============================================================

HITBOXES_FILE = APP_ROOT / "hitboxes_ui.json"


class Hitbox:
    def __init__(self, id: str, x: int, y: int, w: int, h: int, action: str):
        self.id = id
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.action = action

    def contains(self, mx: int, my: int) -> bool:
        return self.x <= mx < self.x + self.w and self.y <= my < self.y + self.h


class HitboxEngine:
    def __init__(self, data: dict):
        self.hitboxes = {}
        for scene_name, scene_data in data.items():
            self.hitboxes[scene_name] = [
                Hitbox(hb["id"], hb["x"], hb["y"], hb["w"], hb["h"], hb["action"])
                for hb in scene_data.get("hitboxes", [])
            ]

    def hit_test(self, scene: str, mx: int, my: int) -> Optional[tuple]:
        for hb in self.hitboxes.get(scene, []):
            if hb.contains(mx, my):
                return (hb.id, hb.action)
        return None

    def get_hitboxes(self, scene: str) -> list:
        return self.hitboxes.get(scene, [])


def load_hitboxes() -> dict:
    empty = {"main": {"hitboxes": []}, "settings": {"hitboxes": []}, "gallery": {"hitboxes": []}}
    if not HITBOXES_FILE.exists():
        logger.warning(f"Hitboxes file not found: {HITBOXES_FILE}")
        return empty
    try:
        with open(HITBOXES_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load hitboxes: {e}")
        return empty


# ============================================================
# UI + SCENE IMPORTS
# ============================================================

from ui.overlay_renderer import OverlayRenderer
from ui.grid_overlay import GridOverlay
from ui.freeze_frame import FreezeFrame
from scenes.boot_scene import BootScene
from scenes.camera_scene import CameraScene
from scenes.settings_scene import SettingsScene
from scenes.gallery_scene import GalleryScene

# ============================================================
# HARDWARE IMPORTS - REAL HARDWARE ONLY (PI MODE)
# ============================================================

HARDWARE_IMPORT_ERRORS = {}


def _load_hardware_backend(component: str, module_path: str, class_name: str):
    try:
        module = __import__(module_path, fromlist=[class_name])
        backend_cls = getattr(module, class_name)
        logger.info(f"Hardware backend loaded: {component} -> {module_path}.{class_name}")
        return backend_cls
    except Exception as exc:
        HARDWARE_IMPORT_ERRORS[component] = f"{type(exc).__name__}: {exc}"
        logger.error(f"Hardware backend import failed [{component}] {module_path}.{class_name}: {exc}")
        return None


CameraBackend = _load_hardware_backend("camera", "hardware.camera_backend", "CameraBackend")
RotaryEncoder = _load_hardware_backend("encoder", "hardware.encoder", "RotaryEncoder")
DebouncedButton = _load_hardware_backend("buttons", "hardware.buttons", "DebouncedButton")
HapticDriver = _load_hardware_backend("haptic", "hardware.haptic", "HapticDriver")
LightSensor = _load_hardware_backend("light_sensor", "hardware.light_sensor", "LightSensor")
Gyroscope = _load_hardware_backend("gyro", "hardware.gyro", "Gyroscope")
FlashLED = _load_hardware_backend("flash_led", "hardware.flash_led", "FlashLED")
BatteryMonitor = _load_hardware_backend("battery", "hardware.battery", "BatteryMonitor")
BrightnessController = _load_hardware_backend("brightness", "hardware.brightness", "BrightnessController")

HARDWARE_IMPORTED = len(HARDWARE_IMPORT_ERRORS) == 0
if HARDWARE_IMPORTED:
    logger.info("All real hardware backends loaded")
else:
    logger.warning(f"Hardware import issues detected ({len(HARDWARE_IMPORT_ERRORS)} components)")


class _NoopBrightnessController:
    def __init__(self):
        self.available = False
        self._brightness = 120

    def set_brightness(self, value: int) -> bool:
        self._brightness = max(0, min(255, int(value)))
        return False

    def get_brightness(self) -> int:
        return self._brightness

    def cleanup(self):
        return


# ============================================================
# PERFORMANCE MONITOR
# ============================================================

class PerformanceMonitor:
    def __init__(self, window_size: int = 100):
        self.frame_times = deque(maxlen=window_size)
        self.fps_history = deque(maxlen=window_size)
        self.frame_start: Optional[float] = None
        self.avg_fps = 0.0
        self.avg_frame_time = 0.0
        self.process = None
        if psutil:
            try:
                self.process = psutil.Process()
            except Exception:
                pass

    def frame_begin(self):
        self.frame_start = time.time()

    def frame_end(self):
        if self.frame_start is None:
            return
        ft = (time.time() - self.frame_start) * 1000
        self.frame_times.append(ft)
        self.fps_history.append(1000.0 / ft if ft > 0 else 0)
        if self.frame_times:
            self.avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        if self.fps_history:
            self.avg_fps = sum(self.fps_history) / len(self.fps_history)
        self.frame_start = None

    def should_skip_frame(self, target_ms: float) -> bool:
        return bool(self.frame_times) and self.frame_times[-1] > target_ms * 1.5

    def get_memory_usage_mb(self) -> float:
        if self.process:
            try:
                return self.process.memory_info().rss / 1024 / 1024
            except Exception:
                pass
        return 0.0

    def print_stats(self):
        mem = self.get_memory_usage_mb()
        logger.debug(f"FPS: {self.avg_fps:.1f} | Frame: {self.avg_frame_time:.1f}ms | Mem: {mem:.1f}MB")


# ============================================================
# POWER MANAGER - STANDBY 10 SEKUNDEN
# ============================================================

class PowerManager:
    STATE_ACTIVE   = 'active'
    STATE_STANDBY  = 'standby'
    STATE_SHUTDOWN = 'shutdown'

    def __init__(self, config, brightness_ctrl):
        self.config = config
        self.brightness_ctrl = brightness_ctrl
        self.state = self.STATE_ACTIVE
        self.last_activity_time = time.time()
        # STANDBY: 10 Sekunden
        self.standby_timeout = config.get('power', 'standby_timeout_s', default=10)
        self.shutdown_long_press = config.get('power', 'shutdown_long_press_s', default=1.8)
        self.encoder_press_start: Optional[float] = None
        self.active_brightness: Optional[int] = None
        logger.info(f"PowerManager: standby={self.standby_timeout}s")

    def update_activity(self):
        self.last_activity_time = time.time()
        if self.state == self.STATE_STANDBY:
            self.wake_from_standby()

    def check_standby(self, motion_detected: bool = False) -> bool:
        if self.state != self.STATE_ACTIVE:
            return False
        if motion_detected:
            self.last_activity_time = time.time()
            return False
        if time.time() - self.last_activity_time >= self.standby_timeout:
            self.enter_standby()
            return True
        return False

    def enter_standby(self):
        if self.state == self.STATE_STANDBY:
            return
        logger.info("STANDBY")
        self.active_brightness = self.brightness_ctrl.get_brightness()
        self.brightness_ctrl.set_brightness(0)
        self.state = self.STATE_STANDBY

    def wake_from_standby(self):
        if self.state != self.STATE_STANDBY:
            return
        logger.info("WAKE")
        self.brightness_ctrl.set_brightness(self.active_brightness or 120)
        self.state = self.STATE_ACTIVE
        self.last_activity_time = time.time()

    def encoder_button_pressed(self):
        if self.state == self.STATE_STANDBY:
            self.wake_from_standby()
            self.update_activity()
            return
        self.encoder_press_start = time.time()
        self.update_activity()

    def encoder_button_released(self) -> bool:
        if self.encoder_press_start is None:
            return False
        duration = time.time() - self.encoder_press_start
        self.encoder_press_start = None
        if duration >= self.shutdown_long_press and self.state == self.STATE_ACTIVE:
            self.request_shutdown()
            return True
        return False

    def request_shutdown(self):
        logger.info("Shutdown requested")
        self.state = self.STATE_SHUTDOWN

    def is_active(self)   -> bool: return self.state == self.STATE_ACTIVE
    def is_standby(self)  -> bool: return self.state == self.STATE_STANDBY
    def is_shutdown(self) -> bool: return self.state == self.STATE_SHUTDOWN


# ============================================================
# SENSOR THREAD
# ============================================================

class SensorThread(threading.Thread):
    def __init__(self, app):
        super().__init__(daemon=True)
        self.app = app
        self.running = False
        self.lock = threading.Lock()
        self.last_lux     = 0.0
        self.last_gyro    = 0.0
        self.last_battery = 0.0
        self.lux_value: Optional[float] = None
        self.tilt_angle: float = 0.0
        self.battery_percent: Optional[int] = None

    def run(self):
        self.running = True
        logger.info("SensorThread started")
        while self.running:
            now = time.time()
            if now - self.last_lux >= 0.2:
                if self.app.light_sensor and self.app.light_sensor.available:
                    lux = self.app.light_sensor.read_lux()
                    with self.lock:
                        self.lux_value = lux
                self.last_lux = now
            if now - self.last_gyro >= 0.05:
                if self.app.gyro and self.app.gyro.available:
                    with self.lock:
                        self.tilt_angle = self.app.gyro.update_tilt()
                self.last_gyro = now
            if now - self.last_battery >= 1.0:
                if self.app.battery and self.app.battery.available:
                    with self.lock:
                        self.battery_percent = self.app.battery.read_percentage()
                self.last_battery = now
            time.sleep(0.01)

    def get_lux(self)     -> Optional[float]:
        with self.lock: return self.lux_value
    def get_tilt(self)    -> float:
        with self.lock: return self.tilt_angle
    def get_battery(self) -> Optional[int]:
        with self.lock: return self.battery_percent
    def stop(self): self.running = False


# ============================================================
# MAIN APPLICATION
# ============================================================

class CameraApp:
    def __init__(self):
        logger.info("=" * 70)
        logger.info(" SelimCam v2.0 - PRODUCTION BUILD")
        logger.info(" Platform: Raspberry Pi 3A+")
        logger.info(f" Display: logical {LOGICAL_W}x{LOGICAL_H}, physical {PHYSICAL_W}x{PHYSICAL_H}")
        logger.info(" Rotation: software 90 degrees clockwise")
        logger.info("=" * 70)

        self.perf_monitor = PerformanceMonitor()
        pygame.init()
        pygame.mouse.set_visible(False)
        pygame.event.set_allowed(None)
        pygame.event.set_allowed([
            pygame.QUIT,
            pygame.MOUSEBUTTONDOWN,
            pygame.FINGERDOWN,
            pygame.KEYDOWN,
            pygame.KEYUP,
        ])
        self.config = ConfigManager()

        # Physical framebuffer (landscape)
        flags = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.FULLSCREEN
        self.screen = pygame.display.set_mode((PHYSICAL_W, PHYSICAL_H), flags)

        # Logische Surface PORTRAIT (so wie App denkt)
        # Alle Scenes rendern NUR auf diese Surface!
        self.logical_surface = pygame.Surface((LOGICAL_W, LOGICAL_H))

        pygame.display.set_caption("SelimCam v2.0")
        logger.info(f"Display mode: logical {LOGICAL_W}x{LOGICAL_H} -> physical {PHYSICAL_W}x{PHYSICAL_H}")

        self.clock = pygame.time.Clock()
        self.target_fps = self.config.get('camera', 'preview_fps', default=24)
        self.running = True

        self.resource_manager = ResourceManager(str(APP_ROOT / "assets"))
        self.resource_manager.preload_all()

        photos_dir = self.config.get('storage', 'photos_dir',
                                     default="/home/pi/camera_app_data/photos")
        self.photo_manager = PhotoManager(photos_dir)

        self.hitbox_engine = HitboxEngine(load_hitboxes())
        logger.info("Hitbox system initialized")

        self.i2c_hardware_available = {
            'haptic': True,
            'light_sensor': True,
            'gyro': True,
        }

        self.hardware_available = self._init_hardware_safe()
        self._init_ui_components()
        self.power_manager = PowerManager(self.config, self.brightness_ctrl)
        self.state_machine = StateMachine(AppState.BOOT)
        self._init_scenes()
        self.sensor_thread = SensorThread(self)
        self.sensor_thread.start()
        self.last_standby_check = time.time()
        self.last_perf_print = time.time()
        self.last_health_write = 0.0
        self.health_file = HEALTH_FILE
        try:
            self.health_file.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        signal.signal(signal.SIGINT,  self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("Initialization complete")
        mem = self.perf_monitor.get_memory_usage_mb()
        if mem > 0:
            logger.info(f"Memory: {mem:.1f}MB")
        self._write_health_status("starting")

    def _write_health_status(self, status: str):
        now = time.time()
        payload = {
            "timestamp": now,
            "pid": os.getpid(),
            "status": status,
            "fps": round(self.perf_monitor.avg_fps, 2),
            "frame_ms": round(self.perf_monitor.avg_frame_time, 2),
            "memory_mb": round(self.perf_monitor.get_memory_usage_mb(), 2),
            "state": self.state_machine.current_state.value if hasattr(self, 'state_machine') else "unknown",
        }
        temp_file = self.health_file.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, separators=(",", ":"))
            os.replace(temp_file, self.health_file)
            self.last_health_write = now
        except Exception:
            pass


    # -------- TOUCH COORDINATE MAPPING (PORTRAIT) --------
    def _rotate_touch(self, px: int, py: int) -> tuple:
        """
        Physical landscape coordinates -> logical portrait coordinates.
        180-degree flip mapping: (480-x, 800-y)
        """
        lx = int(480 - px)
        ly = int(800 - py)
        lx = max(0, min(479, lx))
        ly = max(0, min(799, ly))
        return (lx, ly)

    # -------- HARDWARE INIT --------
