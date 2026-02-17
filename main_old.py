"""
SelimCam v2.0 - PRODUCTION BUILD
Complete camera app with cross-platform support.
"""

import os
import sys
import platform

# ============================================================
# STEP 1: PLATFORM DETECTION
# ============================================================

def detect_platform():
    """Detect if running on Raspberry Pi."""
    if os.path.exists('/sys/firmware/devicetree/base/model'):
        try:
            with open('/sys/firmware/devicetree/base/model', 'r') as f:
                if 'Raspberry Pi' in f.read():
                    return True
        except:
            pass
    
    if platform.system() == 'Linux' and platform.machine().startswith('arm'):
        return True
    
    return False

IS_RASPBERRY_PI = detect_platform()

if IS_RASPBERRY_PI:
    print("[Platform] Raspberry Pi detected - using hardware backends")
else:
    print("[Platform] Non-Pi system detected - using simulators")
    print("\n" + "="*60)
    print(" SIMULATOR CONTROLS:")
    print("="*60)
    print("  LEFT/RIGHT  : Rotate encoder (zoom)")
    print("  RETURN      : Encoder button")
    print("  SPACE       : Shutter (capture photo)")
    print("  Q/W         : Adjust tilt (level indicator)")
    print("  +/- (or =)  : Adjust lux (brightness)")
    print("  G           : Toggle grid")
    print("  L           : Toggle level")
    print("  F           : Cycle flash mode")
    print("  S           : Capture (alternative)")
    print("  ESC         : Exit/Back")
    print("  MOUSE       : Touch simulation (click & drag)")
    print("="*60 + "\n")

# ============================================================
# STEP 2: STANDARD IMPORTS
# ============================================================

import pygame
import time
import signal
import threading
import traceback
from pathlib import Path
from typing import Optional
from collections import deque

try:
    import psutil
except ImportError:
    psutil = None

# Core imports
from core.config_manager import ConfigManager
from core.state_machine import StateMachine, AppState, AppEvent
from core.resource_manager import ResourceManager
from core.photo_manager import PhotoManager
from core.logger import logger

# UI imports
from ui.overlay_renderer import OverlayRenderer
from ui.grid_overlay import GridOverlay
from ui.freeze_frame import FreezeFrame

# Scene imports
from scenes.boot_scene import BootScene
from scenes.camera_scene import CameraScene
from scenes.settings_scene import SettingsScene
from scenes.gallery_scene import GalleryScene

# ============================================================
# STEP 3: CONDITIONAL HARDWARE IMPORTS
# ============================================================

# Import simulators FIRST (always safe)
from hardware.simulator import (
    CameraSimulator,
    EncoderSimulator,
    ButtonSimulator,
    HapticSimulator,
    LightSensorSimulator,
    GyroscopeSimulator,
    FlashLEDSimulator,
    BatterySimulator,
    BrightnessSimulator
)

# If on Pi, try real hardware
if IS_RASPBERRY_PI:
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
        
        logger.info("Real hardware backends loaded")
        HARDWARE_IMPORTED = True
    except Exception as e:
        logger.warning(f"Hardware import failed: {e}")
        logger.info("Falling back to simulators")
        HARDWARE_IMPORTED = False
        IS_RASPBERRY_PI = False
else:
    HARDWARE_IMPORTED = False

# Assign backends
if IS_RASPBERRY_PI and HARDWARE_IMPORTED:
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
    """Real-time performance monitoring."""
    
    def __init__(self, window_size: int = 100):
        self.frame_times = deque(maxlen=window_size)
        self.fps_history = deque(maxlen=window_size)
        self.frame_start: Optional[float] = None
        self.avg_fps = 0.0
        self.avg_frame_time = 0.0
        self.max_frame_time = 0.0
        self.process = None
        
        if psutil:
            try:
                self.process = psutil.Process()
            except:
                pass
    
    def frame_begin(self):
        self.frame_start = time.time()
    
    def frame_end(self):
        if self.frame_start is None:
            return
        
        frame_time = (time.time() - self.frame_start) * 1000
        self.frame_times.append(frame_time)
        
        fps = 1000.0 / frame_time if frame_time > 0 else 0
        self.fps_history.append(fps)
        
        if self.frame_times:
            self.avg_frame_time = sum(self.frame_times) / len(self.frame_times)
            self.max_frame_time = max(self.frame_times)
        
        if self.fps_history:
            self.avg_fps = sum(self.fps_history) / len(self.fps_history)
        
        self.frame_start = None
    
    def should_skip_frame(self, target_ms: float) -> bool:
        if not self.frame_times:
            return False
        return self.frame_times[-1] > (target_ms * 1.5)
    
    def get_memory_usage_mb(self) -> float:
        if self.process:
            try:
                return self.process.memory_info().rss / 1024 / 1024
            except:
                pass
        return 0.0
    
    def print_stats(self):
        mem_mb = self.get_memory_usage_mb()
        if mem_mb > 0:
            logger.debug(f"FPS: {self.avg_fps:.1f} | Frame: {self.avg_frame_time:.1f}ms | Mem: {mem_mb:.1f}MB")
        else:
            logger.debug(f"FPS: {self.avg_fps:.1f} | Frame: {self.avg_frame_time:.1f}ms")


# ============================================================
# POWER MANAGER
# ============================================================

class PowerManager:
    STATE_ACTIVE = 'active'
    STATE_STANDBY = 'standby'
    STATE_SHUTDOWN = 'shutdown'
    
    def __init__(self, config, brightness_ctrl):
        self.config = config
        self.brightness_ctrl = brightness_ctrl
        self.state = self.STATE_ACTIVE
        self.last_activity_time = time.time()
        self.standby_timeout = config.get('power', 'standby_timeout_s', default=30)
        self.shutdown_long_press = config.get('power', 'shutdown_long_press_s', default=1.8)
        self.encoder_press_start: Optional[float] = None
        self.active_brightness: Optional[int] = None
        
        logger.info(f"PowerManager initialized (standby={self.standby_timeout}s)")
    
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
        idle_time = time.time() - self.last_activity_time
        if idle_time >= self.standby_timeout:
            self.enter_standby()
            return True
        return False
    
    def enter_standby(self):
        if self.state == self.STATE_STANDBY:
            return
        logger.info("Entering STANDBY")
        self.active_brightness = self.brightness_ctrl.get_brightness()
        self.brightness_ctrl.set_brightness(10)
        self.state = self.STATE_STANDBY
    
    def wake_from_standby(self):
        if self.state != self.STATE_STANDBY:
            return
        logger.info("WAKE from standby")
        if self.active_brightness is not None:
            self.brightness_ctrl.set_brightness(self.active_brightness)
        self.state = self.STATE_ACTIVE
        self.last_activity_time = time.time()
    
    def encoder_button_pressed(self):
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
    
    def is_active(self) -> bool:
        return self.state == self.STATE_ACTIVE
    
    def is_standby(self) -> bool:
        return self.state == self.STATE_STANDBY
    
    def is_shutdown(self) -> bool:
        return self.state == self.STATE_SHUTDOWN


# ============================================================
# SENSOR THREAD
# ============================================================

class SensorThread(threading.Thread):
    def __init__(self, app):
        super().__init__(daemon=True)
        self.app = app
        self.running = False
        self.lock = threading.Lock()
        
        self.lux_update_hz = 5
        self.gyro_update_hz = 20
        self.battery_update_hz = 1
        
        self.last_lux_update = 0.0
        self.last_gyro_update = 0.0
        self.last_battery_update = 0.0
        
        self.lux_value: Optional[float] = None
        self.tilt_angle: float = 0.0
        self.battery_percent: Optional[int] = None
    
    def run(self):
        self.running = True
        logger.info("SensorThread started")
        
        while self.running:
            current_time = time.time()
            
            if current_time - self.last_lux_update >= 1.0 / self.lux_update_hz:
                if self.app.light_sensor and self.app.light_sensor.available:
                    lux = self.app.light_sensor.read_lux()
                    with self.lock:
                        self.lux_value = lux
                    
                    if self.app.config.get('display', 'brightness_mode') == 'auto':
                        self._update_auto_brightness(lux)
                
                self.last_lux_update = current_time
            
            if current_time - self.last_gyro_update >= 1.0 / self.gyro_update_hz:
                if self.app.gyro and self.app.gyro.available:
                    tilt = self.app.gyro.update_tilt()
                    with self.lock:
                        self.tilt_angle = tilt
                self.last_gyro_update = current_time
            
            if current_time - self.last_battery_update >= 1.0 / self.battery_update_hz:
                if self.app.battery and self.app.battery.available:
                    pct = self.app.battery.read_percentage()
                    with self.lock:
                        self.battery_percent = pct
                self.last_battery_update = current_time
            
            time.sleep(0.01)
    
    def _update_auto_brightness(self, lux: float):
        if not self.app.power_manager.is_active():
            return
        
        min_brightness = self.app.config.get('display', 'brightness_dark', default=40)
        max_brightness = self.app.config.get('display', 'brightness_bright', default=220)
        
        target = self.app.brightness_ctrl.auto_brightness_from_lux(lux, min_brightness, max_brightness)
        current = self.app.brightness_ctrl.get_brightness()
        
        if current is not None:
            delta = target - current
            if abs(delta) > 10:
                delta = 10 if delta > 0 else -10
            self.app.brightness_ctrl.set_brightness(current + delta)
    
    def get_lux(self) -> Optional[float]:
        with self.lock:
            return self.lux_value
    
    def get_tilt(self) -> float:
        with self.lock:
            return self.tilt_angle
    
    def get_battery(self) -> Optional[int]:
        with self.lock:
            return self.battery_percent
    
    def stop(self):
        self.running = False


# ============================================================
# MAIN APPLICATION
# ============================================================

class CameraApp:
    def __init__(self):
        logger.info("="*70)
        logger.info(" SelimCam v2.0 - PRODUCTION BUILD")
        logger.info(f" Platform: {'Raspberry Pi' if IS_RASPBERRY_PI else 'Simulator'}")
        logger.info("="*70)
        
        # Log working directory
        logger.info(f"Working directory: {os.getcwd()}")
        
        self.perf_monitor = PerformanceMonitor()
        
        pygame.init()
        pygame.mouse.set_visible(not IS_RASPBERRY_PI)
        
        self.config = ConfigManager()
        
        screen_w = self.config.get('display', 'width', default=480)
        screen_h = self.config.get('display', 'height', default=800)
        
        if IS_RASPBERRY_PI:
            flags = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.FULLSCREEN
        else:
            flags = pygame.HWSURFACE | pygame.DOUBLEBUF
        
        self.screen = pygame.display.set_mode((screen_w, screen_h), flags)
        pygame.display.set_caption("SelimCam v2.0")
        
        logger.info(f"Display: {screen_w}x{screen_h}")
        
        self.clock = pygame.time.Clock()
        self.target_fps = self.config.get('camera', 'preview_fps', default=24)
        self.running = True
        
        self.resource_manager = ResourceManager("assets")
        self.resource_manager.preload_all()
        
        photos_dir = self.config.get('storage', 'photos_dir', 
                                    default="photos" if not IS_RASPBERRY_PI 
                                    else "/home/pi/camera_app_data/photos")
        self.photo_manager = PhotoManager(photos_dir)
        
        self.hardware_available = self._init_hardware_safe()
        self._init_ui_components()
        
        self.power_manager = PowerManager(self.config, self.brightness_ctrl)
        self.state_machine = StateMachine(AppState.BOOT)
        self._init_scenes()
        
        self.sensor_thread = SensorThread(self)
        self.sensor_thread.start()
        
        self.last_standby_check = time.time()
        self.last_perf_print = time.time()
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Initialization complete")
        mem = self.perf_monitor.get_memory_usage_mb()
        if mem > 0:
            logger.info(f"Memory: {mem:.1f}MB")
    
    def _init_hardware_safe(self) -> dict:
        """Initialize hardware with error handling."""
        logger.info("Initializing hardware...")
        availability = {}
        
        # Camera
        try:
            preview_w = self.config.get('camera', 'preview_width', default=640)
            preview_h = self.config.get('camera', 'preview_height', default=480)
            capture_w = self.config.get('camera', 'capture_width', default=2592)
            capture_h = self.config.get('camera', 'capture_height', default=1944)
            preview_fps = self.config.get('camera', 'preview_fps', default=24)
            
            self.camera = CameraBackend((preview_w, preview_h), (capture_w, capture_h), preview_fps)
            availability['camera'] = True
            logger.info("Camera initialized")
        except Exception as e:
            logger.error(f"Camera init failed: {e}")
            self.camera = None
            availability['camera'] = False
        
        # Encoder
        try:
            self.encoder = RotaryEncoder(5, 6, 2.0, self._encoder_cw, self._encoder_ccw)
            availability['encoder'] = True
            logger.info("Encoder initialized")
        except Exception as e:
            logger.error(f"Encoder init failed: {e}")
            self.encoder = None
            availability['encoder'] = False
        
        # Buttons
        try:
            self.encoder_button = DebouncedButton(13, 50, self._encoder_button_press, self._encoder_button_release)
            self.shutter_button = DebouncedButton(26, 50, self._shutter_press)
            availability['buttons'] = True
            logger.info("Buttons initialized")
        except Exception as e:
            logger.error(f"Buttons init failed: {e}")
            self.encoder_button = None
            self.shutter_button = None
            availability['buttons'] = False
        
        # Haptic
        try:
            self.haptic = HapticDriver()
            availability['haptic'] = self.haptic.available
            if self.haptic.available:
                logger.info("Haptic initialized")
        except Exception as e:
            logger.error(f"Haptic init failed: {e}")
            self.haptic = None
            availability['haptic'] = False
        
        # Light sensor
        try:
            self.light_sensor = LightSensor()
            availability['light_sensor'] = self.light_sensor.available
            if self.light_sensor.available:
                logger.info("Light Sensor initialized")
        except Exception as e:
            logger.error(f"Light sensor init failed: {e}")
            self.light_sensor = None
            availability['light_sensor'] = False
        
        # Gyro
        try:
            self.gyro = Gyroscope()
            availability['gyro'] = self.gyro.available
            if self.gyro.available:
                logger.info("Gyroscope initialized")
        except Exception as e:
            logger.error(f"Gyro init failed: {e}")
            self.gyro = None
            availability['gyro'] = False
        
        # Flash LED
        try:
            flash_duration = self.config.get('flash', 'pulse_duration_ms', default=120)
            self.flash_led = FlashLED(27, flash_duration)
            availability['flash_led'] = True
            logger.info("Flash LED initialized")
        except Exception as e:
            logger.error(f"Flash LED init failed: {e}")
            self.flash_led = None
            availability['flash_led'] = False
        
        # Battery
        try:
            self.battery = BatteryMonitor()
            availability['battery'] = self.battery.available
            if self.battery.available:
                logger.info("Battery initialized")
        except Exception as e:
            logger.error(f"Battery init failed: {e}")
            self.battery = None
            availability['battery'] = False
        
        # Brightness
        try:
            self.brightness_ctrl = BrightnessController()
            availability['brightness'] = self.brightness_ctrl.available
            if self.brightness_ctrl.available:
                logger.info("Brightness initialized")
                mode = self.config.get('display', 'brightness_mode', default='medium')
                if mode != 'auto':
                    values = {
                        'dark': self.config.get('display', 'brightness_dark', default=40),
                        'medium': self.config.get('display', 'brightness_medium', default=120),
                        'bright': self.config.get('display', 'brightness_bright', default=220)
                    }
                    self.brightness_ctrl.set_brightness(values.get(mode, 120))
        except Exception as e:
            logger.error(f"Brightness init failed: {e}")
            self.brightness_ctrl = BrightnessController()
            availability['brightness'] = False
        
        return availability
    
    def _init_ui_components(self):
        font_regular = self.resource_manager.load_font("fonts/Inter_regular.ttf", 20)
        font_bold = self.resource_manager.load_font("fonts/inter_bold.ttf", 24)
        screen_w = self.config.get('display', 'width', default=480)
        screen_h = self.config.get('display', 'height', default=800)
        
        self.overlay_renderer = OverlayRenderer(font_regular, font_bold, screen_w)
        self.grid_overlay = GridOverlay(screen_w, screen_h)
        freeze_duration = self.config.get('ui', 'freeze_duration_ms', default=700)
        self.freeze_frame = FreezeFrame(freeze_duration)
    
    def _init_scenes(self):
        self.scenes = {
            AppState.BOOT: BootScene(self),
            AppState.CAMERA: CameraScene(self),
            AppState.SETTINGS: SettingsScene(self),
            AppState.GALLERY: GalleryScene(self)
        }
        
        for state, scene in self.scenes.items():
            self.state_machine.on_enter(state, scene.on_enter)
            self.state_machine.on_exit(state, scene.on_exit)
        
        self.scenes[AppState.BOOT].on_enter()
    
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
    
    def _handle_simulator_keys(self, key, is_down: bool):
        """Handle simulator keyboard controls."""
        if is_down:
            if hasattr(self.encoder, 'handle_key'):
                self.encoder.handle_key(key)
            
            if key == pygame.K_RETURN and self.encoder_button:
                self.encoder_button.handle_key_down()
            elif key == pygame.K_SPACE and self.shutter_button:
                self.shutter_button.handle_key_down()
            elif key in [pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS]:
                if hasattr(self.light_sensor, 'adjust_lux'):
                    self.light_sensor.adjust_lux(20)
            elif key in [pygame.K_MINUS, pygame.K_KP_MINUS]:
                if hasattr(self.light_sensor, 'adjust_lux'):
                    self.light_sensor.adjust_lux(-20)
            elif key == pygame.K_q:
                if hasattr(self.gyro, 'adjust_tilt'):
                    self.gyro.adjust_tilt(-5)
            elif key == pygame.K_w:
                if hasattr(self.gyro, 'adjust_tilt'):
                    self.gyro.adjust_tilt(5)
            elif key == pygame.K_ESCAPE:
                self.running = False
        else:
            if key == pygame.K_RETURN and self.encoder_button:
                self.encoder_button.handle_key_up()
            elif key == pygame.K_SPACE and self.shutter_button:
                self.shutter_button.handle_key_up()
    
    def run(self):
        """Main loop."""
        logger.info("Starting main loop...")
        logger.info(f"Target: {self.target_fps} FPS")
        
        frame_skip = False
        
        try:
            while self.running:
                self.perf_monitor.frame_begin()
                dt = self.clock.tick(self.target_fps) / 1000.0
                
                if self.power_manager.is_shutdown():
                    self._execute_shutdown()
                    break
                
                current_time = time.time()
                if current_time - self.last_standby_check >= 2.0:
                    motion_detected = False
                    if self.gyro and self.gyro.available:
                        motion_detected = self.gyro.is_moving(threshold=10.0)
                    self.power_manager.check_standby(motion_detected)
                    self.last_standby_check = current_time
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN and not IS_RASPBERRY_PI:
                        self._handle_simulator_keys(event.key, True)
                    elif event.type == pygame.KEYUP and not IS_RASPBERRY_PI:
                        self._handle_simulator_keys(event.key, False)
                    else:
                        scene = self.scenes.get(self.state_machine.current_state)
                        if scene:
                            scene.handle_event(event)
                
                if frame_skip:
                    frame_skip = False
                    continue
                
                scene = self.scenes.get(self.state_machine.current_state)
                if scene:
                    scene.update(dt)
                
                if not self.power_manager.is_standby():
                    if scene:
                        scene.render(self.screen)
                    
                    # Render logger UI overlay
                    logger.render_ui(self.screen)
                    
                    pygame.display.flip()
                else:
                    self.screen.fill((0, 0, 0))
                    pygame.display.flip()
                    time.sleep(0.1)
                
                self.perf_monitor.frame_end()
                
                target_ms = 1000.0 / self.target_fps
                if self.perf_monitor.should_skip_frame(target_ms):
                    frame_skip = True
                
                if current_time - self.last_perf_print >= 5.0:
                    self.perf_monitor.print_stats()
                    self.last_perf_print = current_time
                
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.critical(f"Fatal error: {e}")
            traceback.print_exc()
        finally:
            self.cleanup()
    
    def _execute_shutdown(self):
        """Shutdown sequence."""
        logger.info("SHUTDOWN")
        
        self.screen.fill((0, 0, 0))
        try:
            font = self.resource_manager.load_font("fonts/inter_bold.ttf", 48)
        except:
            font = pygame.font.SysFont("Arial", 48, bold=True)
        
        text = font.render("Shutting down...", True, (255, 255, 255))
        text_rect = text.get_rect(center=(240, 400))
        self.screen.blit(text, text_rect)
        pygame.display.flip()
        
        if self.haptic and self.haptic.available:
            self.haptic.play_effect(14, 1.0)
        
        time.sleep(1.5)
        
        if self.sensor_thread:
            self.sensor_thread.stop()
            self.sensor_thread.join(timeout=1.0)
        
        self.config.save()
        
        if IS_RASPBERRY_PI:
            try:
                import RPi.GPIO as GPIO
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(19, GPIO.OUT)
                GPIO.output(19, GPIO.HIGH)
                time.sleep(0.5)
            except:
                pass
            
            try:
                import os
                os.system("sudo shutdown -h now")
            except:
                pass
        
        self.running = False
    
    def cleanup(self):
        """Cleanup resources."""
        logger.info("CLEANUP")
        
        if hasattr(self, 'sensor_thread') and self.sensor_thread:
            self.sensor_thread.stop()
            self.sensor_thread.join(timeout=2.0)
        
        if hasattr(self, 'config'):
            self.config.save()
        
        if hasattr(self, 'camera') and self.camera:
            self.camera.cleanup()
        
        components = [
            ('encoder', 'Encoder'),
            ('encoder_button', 'Encoder Button'),
            ('shutter_button', 'Shutter'),
            ('flash_led', 'Flash LED'),
            ('haptic', 'Haptic'),
            ('light_sensor', 'Light Sensor'),
            ('gyro', 'Gyro'),
            ('battery', 'Battery')
        ]
        
        for attr, name in components:
            if hasattr(self, attr):
                comp = getattr(self, attr)
                if comp:
                    try:
                        comp.cleanup()
                    except:
                        pass
        
        pygame.quit()
        logger.info("CLEANUP COMPLETE")


def main():
    """Entry point."""
    try:
        logger.info("\n" + "="*70)
        logger.info(" SELIMCAM v2.0 - STARTING")
        logger.info("="*70 + "\n")
        
        app = CameraApp()
        app.run()
        
        logger.info("\n" + "="*70)
        logger.info(" SELIMCAM TERMINATED")
        logger.info("="*70 + "\n")
        
    except Exception as e:
        logger.critical(f"\nFATAL ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()