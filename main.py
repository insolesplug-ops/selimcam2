"""
SelimCam v2.0 - PRODUCTION BUILD
Pi 3A+ | 8MP Camera | Waveshare 4.3" DSI
FIXES: KMS Hardware Rotation 180deg, Touch Mapping, Debug Logging
"""

import os
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

# Force SDL framebuffer + rotation mapping before pygame.init()
os.environ['SDL_FBDEV'] = '/dev/fb0'
os.environ['SDL_VIDEO_KMSDRM_ROTATION'] = '270'

# ============================================================
# PLATFORM - HARDCODED PI MODE
# ============================================================

# FORCE PI MODE - Pi 3A+ hardcoded
IS_RASPBERRY_PI = True
print("[Platform] Raspberry Pi 3A+ - FORCE MODE")

# ============================================================
# DISPLAY ROTATION CONSTANTS
# ============================================================
# KMS Hardware rotation: SDL_VIDEO_KMSDRM_ROTATION="1" (90 degrees CW)
# - Logical app space: portrait (480x800)
# - Physical framebuffer: portrait (480x800) - native from KMS 90° rotation
# - Touch mapping: (y_raw, width - x_raw) for 90 degree CW HW rotation

LOGICAL_W  = 480
LOGICAL_H  = 800
PHYSICAL_W = 480
PHYSICAL_H = 800

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
        self.last_touch_point = None
        self.last_touch_ts = 0.0

        pygame.display.set_caption("SelimCam v2.0")
        logger.info(f"Display mode: {LOGICAL_W}x{LOGICAL_H} portrait (cmdline rotation, SDL rotation disabled)")

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

    def _rotate_touch(self, px: int, py: int) -> tuple:
        """Transform touch input based on active rotation mode."""
        rotation_mode = self.config.get('camera', 'rotation_test', default=0)
        
        if rotation_mode == 0:
            # Mode 0: 90° CW
            lx = int(py)
            ly = int(480 - px)
        elif rotation_mode == 1:
            # Mode 1: No rotation (identity)
            lx = int(px)
            ly = int(py)
        elif rotation_mode == 2:
            # Mode 2: 90° CCW (THIS IS YOUR SETUP!)
            lx = int(800 - py)
            ly = int(px)
        else:  # Mode 3
            # Mode 3: 180° flip
            lx = int(480 - px)
            ly = int(800 - py)

        lx = max(0, min(LOGICAL_W - 1, lx))
        ly = max(0, min(LOGICAL_H - 1, ly))
        return (lx, ly)

    def _init_hardware_safe(self) -> dict:
        logger.info("Initializing hardware...")
        av = {}

        try:
            if CameraBackend is None:
                import_error = HARDWARE_IMPORT_ERRORS.get('camera', 'unknown import error')
                raise RuntimeError(f"Camera backend unavailable: {import_error}")

            pw  = self.config.get('camera', 'preview_width',  default=640)
            ph  = self.config.get('camera', 'preview_height', default=480)
            cw  = self.config.get('camera', 'capture_width',  default=3280)
            ch  = self.config.get('camera', 'capture_height', default=2464)
            fps = self.config.get('camera', 'preview_fps',    default=24)
            retries = 3
            retry_delay_s = 0.35
            last_error = None
            self.camera = None
            for attempt in range(1, retries + 1):
                try:
                    self.camera = CameraBackend((pw, ph), (cw, ch), fps)
                    break
                except Exception as cam_exc:
                    last_error = cam_exc
                    logger.error(f"Camera init attempt {attempt}/{retries} failed: {cam_exc}")
                    if attempt < retries:
                        time.sleep(retry_delay_s)

            if self.camera is None:
                raise RuntimeError(f"Camera backend init failed after {retries} attempts: {last_error}")

            av['camera'] = True
            logger.info("Camera initialized")
        except Exception as e:
            logger.critical(f"Camera init failed: {e}")
            raise RuntimeError("Camera initialization failed on Raspberry Pi") from e

        try:
            if RotaryEncoder is None:
                raise RuntimeError(HARDWARE_IMPORT_ERRORS.get('encoder', 'backend import failed'))
            self.encoder = RotaryEncoder(5, 6, 2.0, self._encoder_cw, self._encoder_ccw)
            av['encoder'] = True
            logger.info("Encoder initialized")
        except Exception as e:
            logger.error(f"Encoder init failed: {e}")
            self.encoder = None
            av['encoder'] = False

        try:
            if DebouncedButton is None:
                raise RuntimeError(HARDWARE_IMPORT_ERRORS.get('buttons', 'backend import failed'))
            self.encoder_button = DebouncedButton(13, 50, self._encoder_button_press, self._encoder_button_release)
            self.shutter_button = DebouncedButton(26, 50, self._shutter_press)
            av['buttons'] = True
            logger.info("Buttons initialized")
        except Exception as e:
            logger.error(f"Buttons init failed: {e}")
            self.encoder_button = None
            self.shutter_button = None
            av['buttons'] = False

        try:
            if HapticDriver is None:
                raise RuntimeError(HARDWARE_IMPORT_ERRORS.get('haptic', 'backend import failed'))
            self.haptic = HapticDriver()
            av['haptic'] = self.haptic.available
            if self.haptic.available: logger.info("Haptic initialized")
        except Exception as e:
            logger.error(f"Haptic init failed: {e}")
            self.haptic = None
            av['haptic'] = False
            self.i2c_hardware_available['haptic'] = False

        try:
            if LightSensor is None:
                raise RuntimeError(HARDWARE_IMPORT_ERRORS.get('light_sensor', 'backend import failed'))
            self.light_sensor = LightSensor()
            av['light_sensor'] = self.light_sensor.available
            if self.light_sensor.available: logger.info("Light Sensor initialized")
        except Exception as e:
            logger.error(f"Light sensor init failed: {e}")
            self.light_sensor = None
            av['light_sensor'] = False
            self.i2c_hardware_available['light_sensor'] = False

        try:
            if Gyroscope is None:
                raise RuntimeError(HARDWARE_IMPORT_ERRORS.get('gyro', 'backend import failed'))
            self.gyro = Gyroscope()
            av['gyro'] = self.gyro.available
            if self.gyro.available: logger.info("Gyroscope initialized")
        except Exception as e:
            logger.error(f"Gyro init failed: {e}")
            self.gyro = None
            av['gyro'] = False
            self.i2c_hardware_available['gyro'] = False

        try:
            if FlashLED is None:
                raise RuntimeError(HARDWARE_IMPORT_ERRORS.get('flash_led', 'backend import failed'))
            flash_dur = self.config.get('flash', 'pulse_duration_ms', default=120)
            self.flash_led = FlashLED(27, flash_dur)
            av['flash_led'] = True
            logger.info("Flash LED initialized")
        except Exception as e:
            logger.error(f"Flash LED init failed: {e}")
            self.flash_led = None
            av['flash_led'] = False

        try:
            if BatteryMonitor is None:
                raise RuntimeError(HARDWARE_IMPORT_ERRORS.get('battery', 'backend import failed'))
            self.battery = BatteryMonitor()
            av['battery'] = self.battery.available
            if self.battery.available: logger.info("Battery initialized")
        except Exception as e:
            logger.error(f"Battery init failed: {e}")
            self.battery = None
            av['battery'] = False

        try:
            if BrightnessController is None:
                raise RuntimeError(HARDWARE_IMPORT_ERRORS.get('brightness', 'backend import failed'))
            self.brightness_ctrl = BrightnessController()
            av['brightness'] = self.brightness_ctrl.available
            if self.brightness_ctrl.available:
                logger.info("Brightness initialized")
                mode = self.config.get('display', 'brightness_mode', default='medium')
                if mode != 'auto':
                    values = {
                        'dark':   self.config.get('display', 'brightness_dark',   default=40),
                        'medium': self.config.get('display', 'brightness_medium', default=120),
                        'bright': self.config.get('display', 'brightness_bright', default=220),
                    }
                    self.brightness_ctrl.set_brightness(values.get(mode, 120))
        except Exception as e:
            logger.error(f"Brightness init failed: {e}")
            self.brightness_ctrl = _NoopBrightnessController()
            av['brightness'] = False

        return av

    def _init_ui_components(self):
        font_r = self.resource_manager.load_font("fonts/Inter_regular.ttf", 20)
        font_b = self.resource_manager.load_font("fonts/inter_bold.ttf",    24)
        self.overlay_renderer = OverlayRenderer(font_r, font_b, LOGICAL_W)
        self.grid_overlay     = GridOverlay(LOGICAL_W, LOGICAL_H)
        freeze_dur            = self.config.get('ui', 'freeze_duration_ms', default=700)
        self.freeze_frame     = FreezeFrame(freeze_dur)

    def _init_scenes(self):
        self.scenes = {
            AppState.BOOT:     BootScene(self),
            AppState.CAMERA:   CameraScene(self),
            AppState.SETTINGS: SettingsScene(self),
            AppState.GALLERY:  GalleryScene(self),
        }
        for state, scene in self.scenes.items():
            self.state_machine.on_enter(state, scene.on_enter)
            self.state_machine.on_exit(state,  scene.on_exit)
        self.scenes[AppState.BOOT].on_enter()

    # ── ENCODER CALLBACKS ────────────────────────────────────────────
    def _encoder_cw(self):
        self.power_manager.update_activity()
        scene = self.scenes.get(self.state_machine.current_state)
        if hasattr(scene, 'handle_encoder_rotation'):
            scene.handle_encoder_rotation(1)

    def _encoder_ccw(self):
        self.power_manager.update_activity()
        scene = self.scenes.get(self.state_machine.current_state)
        if hasattr(scene, 'handle_encoder_rotation'):
            scene.handle_encoder_rotation(-1)

    def _encoder_button_press(self):
        self.power_manager.encoder_button_pressed()

    def _encoder_button_release(self, duration: float):
        if self.power_manager.encoder_button_released():
            self.state_machine.handle_event(AppEvent.SHUTDOWN_REQUEST)

    def _shutter_press(self):
        self.power_manager.update_activity()
        if self.state_machine.is_camera:
            scene = self.scenes[AppState.CAMERA]
            if hasattr(scene, '_capture_photo'):
                scene._capture_photo()

    def _signal_handler(self, sig, frame):
        logger.info(f"Signal {sig}, shutting down...")
        self.running = False

    def _execute_hitbox_action(self, action: str):
        if action == "go_to_settings":
            self.state_machine.handle_event(AppEvent.OPEN_SETTINGS)
        elif action == "go_to_gallery":
            self.state_machine.handle_event(AppEvent.OPEN_GALLERY)
        elif action == "go_to_main":
            self.state_machine.handle_event(AppEvent.BACK_TO_CAMERA)
        elif action == "cycle_flash":
            current  = self.config.get('flash', 'mode', default='off')
            modes    = ['off', 'on', 'auto']
            idx      = modes.index(current) if current in modes else 0
            new_mode = modes[(idx + 1) % 3]
            self.config.set('flash', 'mode', value=new_mode, save=True)
            logger.info(f"Flash: {current} → {new_mode}")
        elif action == "delete_photo":
            if self.state_machine.current_state == AppState.GALLERY:
                scene = self.scenes.get(AppState.GALLERY)
                if scene and hasattr(scene, '_delete_current_photo'):
                    scene._delete_current_photo()

    # ── MAIN LOOP ────────────────────────────────────────────────────
    def run(self):
        logger.info("Starting main loop...")
        logger.info(f"Target: {self.target_fps} FPS")
        frame_skip = False

        try:
            while self.running:
                self.perf_monitor.frame_begin()
                dt  = self.clock.tick(self.target_fps) / 1000.0
                now = time.time()

                if self.power_manager.is_shutdown():
                    self._execute_shutdown()
                    break

                # Standby alle 2s prüfen
                if now - self.last_standby_check >= 2.0:
                    motion = False
                    if self.gyro and self.gyro.available:
                        motion = self.gyro.is_moving(threshold=10.0)
                    self.power_manager.check_standby(motion)
                    self.last_standby_check = now

                # Events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        continue

                    # Standby: jede Eingabe weckt auf
                    if self.power_manager.is_standby():
                        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN, pygame.FINGERDOWN):
                            self.power_manager.update_activity()
                            logger.info("Woke from standby")
                        continue

                    # Mouse (PC Simulator + Pi Touch via X11)
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.power_manager.update_activity()
                        px, py = event.pos
                        lx, ly = self._rotate_touch(px, py)
                        self.last_touch_point = (lx, ly)
                        self.last_touch_ts = time.time()
                        logger.debug(f"[TOUCH] Raw: ({px}, {py}) → Mapped: ({lx}, {ly})")
                        rotated_event = pygame.event.Event(
                            pygame.MOUSEBUTTONDOWN,
                            {
                                "pos": (lx, ly),
                                "button": getattr(event, "button", 1),
                                "touch": getattr(event, "touch", False),
                                "window": getattr(event, "window", None),
                            },
                        )
                        scene_name = self.state_machine.current_state.value
                        result = self.hitbox_engine.hit_test(scene_name, lx, ly)
                        if result:
                            hitbox_id, action = result
                            logger.info(f"Hitbox: {hitbox_id} → {action}")
                            self._execute_hitbox_action(action)
                        else:
                            scene = self.scenes.get(self.state_machine.current_state)
                            if scene:
                                scene.handle_event(rotated_event)

                    # Finger Touch (direktes KMS/DRM Touch Event)
                    elif event.type == pygame.FINGERDOWN:
                        self.power_manager.update_activity()
                        px = int(event.x * PHYSICAL_W)
                        py = int(event.y * PHYSICAL_H)
                        lx, ly = self._rotate_touch(px, py)
                        self.last_touch_point = (lx, ly)
                        self.last_touch_ts = time.time()
                        logger.debug(f"[TOUCH] Raw: ({px}, {py}) → Mapped: ({lx}, {ly})")
                        rotated_event = pygame.event.Event(
                            pygame.MOUSEBUTTONDOWN,
                            {
                                "pos": (lx, ly),
                                "button": 1,
                                "touch": True,
                                "window": getattr(event, "window", None),
                            },
                        )
                        scene_name = self.state_machine.current_state.value
                        result = self.hitbox_engine.hit_test(scene_name, lx, ly)
                        if result:
                            hitbox_id, action = result
                            self._execute_hitbox_action(action)
                        else:
                            scene = self.scenes.get(self.state_machine.current_state)
                            if scene:
                                scene.handle_event(rotated_event)

                    elif event.type == pygame.KEYDOWN:
                        self.power_manager.update_activity()
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                        else:
                            scene = self.scenes.get(self.state_machine.current_state)
                            if scene:
                                scene.handle_event(event)
                    else:
                        scene = self.scenes.get(self.state_machine.current_state)
                        if scene:
                            scene.handle_event(event)

                if frame_skip:
                    frame_skip = False
                    continue

                # Update
                scene = self.scenes.get(self.state_machine.current_state)
                if scene:
                    scene.update(dt)

                # Render
                if not self.power_manager.is_standby():
                    if scene:
                        # Scene rendert auf logical_surface (PORTRAIT 480x800)
                        scene.render(self.logical_surface)

                    # Logger overlay auf logical_surface
                    logger.render_ui(self.logical_surface)

                    # Touch debug overlay: red point where mapped touch is processed
                    if self.config.get('ui', 'touch_debug_overlay', default=True):
                        if self.last_touch_point and (time.time() - self.last_touch_ts) < 1.2:
                            pygame.draw.circle(self.logical_surface, (255, 0, 0), self.last_touch_point, 10)
                            pygame.draw.circle(self.logical_surface, (255, 255, 255), self.last_touch_point, 12, 2)

                    # Direct blit: logical 480x800 renders natively to physical 480x800 (KMS 90° rotation)
                    self.screen.blit(self.logical_surface, (0, 0))

                    pygame.display.update([pygame.Rect(0, 0, PHYSICAL_W, PHYSICAL_H)])
                else:
                    # Standby: Screen schwarz
                    self.screen.fill((0, 0, 0))
                    pygame.display.update([pygame.Rect(0, 0, PHYSICAL_W, PHYSICAL_H)])
                    time.sleep(0.2)

                self.perf_monitor.frame_end()

                target_ms = 1000.0 / self.target_fps
                if self.perf_monitor.should_skip_frame(target_ms):
                    frame_skip = True

                if now - self.last_perf_print >= 5.0:
                    self.perf_monitor.print_stats()
                    self.last_perf_print = now

                if now - self.last_health_write >= 5.0:
                    self._write_health_status("running")

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.critical(f"Fatal error: {e}")
            traceback.print_exc()
        finally:
            self._write_health_status("stopping")
            self.cleanup()

    def _execute_shutdown(self):
        logger.info("SHUTDOWN")
        self.screen.fill((0, 0, 0))
        try:
            font = self.resource_manager.load_font("fonts/inter_bold.ttf", 48)
        except Exception:
            font = pygame.font.SysFont("Arial", 48, bold=True)
        text = font.render("Shutting down...", True, (255, 255, 255))
        self.screen.blit(text, text.get_rect(center=(PHYSICAL_W // 2, PHYSICAL_H // 2)))
        pygame.display.flip()
        if self.haptic and self.haptic.available:
            self.haptic.play_effect(14, 1.0)
        time.sleep(1.5)
        if hasattr(self, 'sensor_thread') and self.sensor_thread:
            self.sensor_thread.stop()
            self.sensor_thread.join(timeout=1.0)
        self.config.save()
        try:
            os.system("sudo shutdown -h now")
        except Exception as e:
            logger.error(f"Shutdown failed: {e}")
        self.running = False

    def cleanup(self):
        logger.info("CLEANUP")
        if hasattr(self, 'sensor_thread') and self.sensor_thread:
            self.sensor_thread.stop()
            self.sensor_thread.join(timeout=2.0)
        if hasattr(self, 'config'):
            self.config.save()
        if hasattr(self, 'camera') and self.camera:
            self.camera.cleanup()
        for attr in ['encoder', 'encoder_button', 'shutter_button',
                     'flash_led', 'haptic', 'light_sensor', 'gyro', 'battery']:
            if hasattr(self, attr):
                comp = getattr(self, attr)
                if comp:
                    try: comp.cleanup()
                    except Exception: pass
        pygame.quit()
        logger.info("CLEANUP COMPLETE")


# ============================================================
# ENTRY POINT
# ============================================================

def main():
    try:
        logger.info("\n" + "=" * 70)
        logger.info(" SELIMCAM v2.0 - STARTING")
        logger.info("=" * 70 + "\n")
        app = CameraApp()
        app.run()
        logger.info("\n" + "=" * 70)
        logger.info(" SELIMCAM TERMINATED")
        logger.info("=" * 70 + "\n")
    except Exception as e:
        logger.critical(f"\nFATAL ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
