"""
SelimCam v2.0 - PRODUCTION BUILD
Pi 3A+ | 8MP Camera | Waveshare 4.3" DSI
FIXES: Software Rotation 90°, Standby 10s, No Stubs
"""

import os
import sys
import platform
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

# ============================================================
# PLATFORM - HARDCODED PI MODE
# ============================================================

# FORCE PI MODE - Pi 3A+ hardcoded
IS_RASPBERRY_PI = True
print("[Platform] 🍓 Raspberry Pi 3A+ - FORCE MODE")

# ============================================================
# DISPLAY ROTATION CONSTANTS
# ============================================================
# Display ist physisch Landscape (800x480)
# App rendert Portrait (480x800) und wird SOFTWARE-rotiert 90° rechts

PHYSICAL_W = 800   # Physisches Display: Breite
PHYSICAL_H = 480   # Physisches Display: Höhe
LOGICAL_W  = 480   # Logische App-Breite  (Portrait)
LOGICAL_H  = 800   # Logische App-Höhe    (Portrait)

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

HITBOXES_FILE = Path("hitboxes_ui.json")


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
# HARDWARE IMPORTS - SIMULATORS FIRST, DANN ECHTE HARDWARE
# ============================================================

from hardware.simulator import (
    CameraSimulator, EncoderSimulator, ButtonSimulator,
    HapticSimulator, LightSensorSimulator, GyroscopeSimulator,
    FlashLEDSimulator, BatterySimulator, BrightnessSimulator
)

# Echte Hardware laden - IS_RASPBERRY_PI bleibt IMMER True!
try:
    from hardware.camera_backend import CameraBackend as RealCamera
    from hardware.encoder import RotaryEncoder as RealEncoder
    from hardware.buttons import DebouncedButton as RealButton
    from hardware.haptic import HapticDriver as RealHaptic
    from hardware.light_sensor import LightSensor as RealLightSensor
    from hardware.gyro import Gyroscope as RealGyro
    from hardware.flash_led import FlashLED as RealFlashLED
    from hardware.battery import BatteryMonitor as RealBattery
    from hardware.brightness import BrightnessController as RealBrightness
    logger.info("✓ Real hardware backends loaded")
    HARDWARE_IMPORTED = True
except Exception as e:
    logger.error(f"Hardware import failed: {e}")
    logger.warning("Using simulators - IS_RASPBERRY_PI stays True!")
    HARDWARE_IMPORTED = False
    # WICHTIG: IS_RASPBERRY_PI = False ist VERBOTEN hier!

# Backends zuweisen
if HARDWARE_IMPORTED:
    CameraBackend = RealCamera
    RotaryEncoder = RealEncoder
    DebouncedButton = RealButton
    HapticDriver = RealHaptic
    LightSensor = RealLightSensor
    Gyroscope = RealGyro
    FlashLED = RealFlashLED
    BatteryMonitor = RealBattery
    BrightnessController = RealBrightness
else:
    CameraBackend = CameraSimulator
    RotaryEncoder = EncoderSimulator
    DebouncedButton = ButtonSimulator
    HapticDriver = HapticSimulator
    LightSensor = LightSensorSimulator
    Gyroscope = GyroscopeSimulator
    FlashLED = FlashLEDSimulator
    BatteryMonitor = BatterySimulator
    BrightnessController = BrightnessSimulator
    logger.info("Simulator backends active")


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
        logger.info("📴 STANDBY")
        self.active_brightness = self.brightness_ctrl.get_brightness()
        self.brightness_ctrl.set_brightness(0)
        self.state = self.STATE_STANDBY

    def wake_from_standby(self):
        if self.state != self.STATE_STANDBY:
            return
        logger.info("🔋 WAKE")
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
        logger.info(f" Display:  SOFTWARE ROTATION 90° right")
        logger.info(f"           Physical {PHYSICAL_W}x{PHYSICAL_H} → Logical {LOGICAL_W}x{LOGICAL_H}")
        logger.info("=" * 70)

        self.perf_monitor = PerformanceMonitor()
        pygame.init()
        pygame.mouse.set_visible(False)
        self.config = ConfigManager()

        # Physisches Fenster LANDSCAPE (so wie Hardware)
        flags = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.FULLSCREEN
        self.screen = pygame.display.set_mode((PHYSICAL_W, PHYSICAL_H), flags)

        # Logische Surface PORTRAIT (so wie App denkt)
        # Alle Scenes rendern NUR auf diese Surface!
        self.logical_surface = pygame.Surface((LOGICAL_W, LOGICAL_H))

        pygame.display.set_caption("SelimCam v2.0")
        logger.info(f"Physical: {PHYSICAL_W}x{PHYSICAL_H} | Logical: {LOGICAL_W}x{LOGICAL_H}")

        self.clock = pygame.time.Clock()
        self.target_fps = self.config.get('camera', 'preview_fps', default=24)
        self.running = True

        self.resource_manager = ResourceManager("assets")
        self.resource_manager.preload_all()

        photos_dir = self.config.get('storage', 'photos_dir',
                                     default="/home/pi/camera_app_data/photos")
        self.photo_manager = PhotoManager(photos_dir)

        self.hitbox_engine = HitboxEngine(load_hitboxes())
        logger.info("Hitbox system initialized")

        self.hardware_available = self._init_hardware_safe()
        self._init_ui_components()
        self.power_manager = PowerManager(self.config, self.brightness_ctrl)
        self.state_machine = StateMachine(AppState.BOOT)
        self._init_scenes()
        self.sensor_thread = SensorThread(self)
        self.sensor_thread.start()
        self.last_standby_check = time.time()
        self.last_perf_print = time.time()

        signal.signal(signal.SIGINT,  self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("Initialization complete")
        mem = self.perf_monitor.get_memory_usage_mb()
        if mem > 0:
            logger.info(f"Memory: {mem:.1f}MB")

    # ── TOUCH KOORDINATEN UMRECHNEN ─────────────────────────────────
    def _rotate_touch(self, px: int, py: int) -> tuple:
        """
        Physische Landscape-Koordinaten → Logische Portrait-Koordinaten.
        Rotation 90° nach rechts (clockwise):
          lx = PHYSICAL_H - 1 - py  (skaliert)
          ly = px                    (skaliert)
        """
        lx = int((PHYSICAL_H - 1 - py) * LOGICAL_W / PHYSICAL_H)
        ly = int(px * LOGICAL_H / PHYSICAL_W)
        # Clamp
        lx = max(0, min(LOGICAL_W - 1, lx))
        ly = max(0, min(LOGICAL_H - 1, ly))
        return (lx, ly)

    # ── HARDWARE INIT ────────────────────────────────────────────────
    def _init_hardware_safe(self) -> dict:
        logger.info("Initializing hardware...")
        av = {}

        try:
            pw  = self.config.get('camera', 'preview_width',  default=640)
            ph  = self.config.get('camera', 'preview_height', default=480)
            cw  = self.config.get('camera', 'capture_width',  default=3280)
            ch  = self.config.get('camera', 'capture_height', default=2464)
            fps = self.config.get('camera', 'preview_fps',    default=24)
            self.camera = CameraBackend((pw, ph), (cw, ch), fps)
            av['camera'] = True
            logger.info("✓ Camera")
        except Exception as e:
            logger.error(f"Camera init failed: {e}")
            self.camera = None
            av['camera'] = False

        try:
            self.encoder = RotaryEncoder(5, 6, 2.0, self._encoder_cw, self._encoder_ccw)
            av['encoder'] = True
            logger.info("✓ Encoder")
        except Exception as e:
            logger.error(f"Encoder init failed: {e}")
            self.encoder = None
            av['encoder'] = False

        try:
            self.encoder_button = DebouncedButton(13, 50, self._encoder_button_press, self._encoder_button_release)
            self.shutter_button = DebouncedButton(26, 50, self._shutter_press)
            av['buttons'] = True
            logger.info("✓ Buttons")
        except Exception as e:
            logger.error(f"Buttons init failed: {e}")
            self.encoder_button = None
            self.shutter_button = None
            av['buttons'] = False

        try:
            self.haptic = HapticDriver()
            av['haptic'] = self.haptic.available
            if self.haptic.available: logger.info("✓ Haptic")
        except Exception as e:
            logger.error(f"Haptic init failed: {e}")
            self.haptic = None
            av['haptic'] = False

        try:
            self.light_sensor = LightSensor()
            av['light_sensor'] = self.light_sensor.available
            if self.light_sensor.available: logger.info("✓ Light Sensor")
        except Exception as e:
            logger.error(f"Light sensor init failed: {e}")
            self.light_sensor = None
            av['light_sensor'] = False

        try:
            self.gyro = Gyroscope()
            av['gyro'] = self.gyro.available
            if self.gyro.available: logger.info("✓ Gyroscope")
        except Exception as e:
            logger.error(f"Gyro init failed: {e}")
            self.gyro = None
            av['gyro'] = False

        try:
            flash_dur = self.config.get('flash', 'pulse_duration_ms', default=120)
            self.flash_led = FlashLED(27, flash_dur)
            av['flash_led'] = True
            logger.info("✓ Flash LED")
        except Exception as e:
            logger.error(f"Flash LED init failed: {e}")
            self.flash_led = None
            av['flash_led'] = False

        try:
            self.battery = BatteryMonitor()
            av['battery'] = self.battery.available
            if self.battery.available: logger.info("✓ Battery")
        except Exception as e:
            logger.error(f"Battery init failed: {e}")
            self.battery = None
            av['battery'] = False

        try:
            self.brightness_ctrl = BrightnessController()
            av['brightness'] = self.brightness_ctrl.available
            if self.brightness_ctrl.available:
                logger.info("✓ Brightness")
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
            self.brightness_ctrl = BrightnessController()
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
                            logger.info("⏰ Woke from standby")
                        continue

                    # Mouse (PC Simulator + Pi Touch via X11)
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.power_manager.update_activity()
                        px, py = event.pos
                        lx, ly = self._rotate_touch(px, py)
                        scene_name = self.state_machine.current_state.value
                        result = self.hitbox_engine.hit_test(scene_name, lx, ly)
                        if result:
                            hitbox_id, action = result
                            logger.info(f"Hitbox: {hitbox_id} → {action}")
                            self._execute_hitbox_action(action)
                        else:
                            scene = self.scenes.get(self.state_machine.current_state)
                            if scene:
                                scene.handle_event(event)

                    # Finger Touch (direktes KMS/DRM Touch Event)
                    elif event.type == pygame.FINGERDOWN:
                        self.power_manager.update_activity()
                        px = int(event.x * PHYSICAL_W)
                        py = int(event.y * PHYSICAL_H)
                        lx, ly = self._rotate_touch(px, py)
                        scene_name = self.state_machine.current_state.value
                        result = self.hitbox_engine.hit_test(scene_name, lx, ly)
                        if result:
                            hitbox_id, action = result
                            self._execute_hitbox_action(action)

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

                    # ══ SOFTWARE ROTATION 90° RECHTS ══════════════════
                    # logical_surface (480x800) → rotate(-90°) → (800x480)
                    # Auf physisches Display (800x480) blitten
                    rotated = pygame.transform.rotate(self.logical_surface, -90)
                    self.screen.blit(rotated, (0, 0))
                    # ══════════════════════════════════════════════════

                    pygame.display.flip()
                else:
                    # Standby: Screen schwarz
                    self.screen.fill((0, 0, 0))
                    pygame.display.flip()
                    time.sleep(0.2)

                self.perf_monitor.frame_end()

                target_ms = 1000.0 / self.target_fps
                if self.perf_monitor.should_skip_frame(target_ms):
                    frame_skip = True

                if now - self.last_perf_print >= 5.0:
                    self.perf_monitor.print_stats()
                    self.last_perf_print = now

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.critical(f"Fatal error: {e}")
            traceback.print_exc()
        finally:
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
```

---

# 📋 **WAS GEÄNDERT WURDE - ÜBERSICHT**
```
main.py Änderungen:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ IS_RASPBERRY_PI = True  (hardcoded, kein detect_platform)
✅ IS_RASPBERRY_PI = False VERBOTEN im except Block
✅ SOFTWARE ROTATION 90° rechts via pygame.transform.rotate
✅ PHYSICAL 800x480 + LOGICAL 480x800 Surface System
✅ Touch-Koordinaten werden mitrotiert (_rotate_touch)
✅ Standby = 10 Sekunden (default=10)
✅ Standby = echter schwarzer Screen + sleep(0.2)
```

---

# 🗑️ **DIESE DATEIEN IN VS CODE LÖSCHEN!**
```
selimcam2/picamera2.py   ← Rechtsklick → Delete
selimcam2/smbus2.py      ← Rechtsklick → Delete
selimcam2/gpiozero.py    ← Rechtsklick → Delete