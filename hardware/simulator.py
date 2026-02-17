"""
Simulator backends for Windows/Mac development.
These are the DEFAULT backends when not on Raspberry Pi.
"""

import pygame
import numpy as np
import time
from typing import Optional, Callable


class CameraSimulator:
    """Simulated camera with animated gradient preview."""
    
    def __init__(self, preview_size=(640, 480), capture_size=(2592, 1944), preview_fps=24):
        self.preview_size = preview_size
        self.capture_size = capture_size
        self.preview_fps = preview_fps
        self.is_running = False
        self.frame_count = 0
        
        print(f"[CameraSim] Initialized {preview_size[0]}x{preview_size[1]} @ {preview_fps}fps")
    
    def start_preview(self):
        self.is_running = True
        print("[CameraSim] Preview started")
    
    def stop_preview(self):
        self.is_running = False
        print("[CameraSim] Preview stopped")
    
    def get_preview_frame(self) -> Optional[np.ndarray]:
        """Generate animated gradient frame."""
        if not self.is_running:
            return None
        
        h, w = self.preview_size[1], self.preview_size[0]
        
        # Animated rainbow gradient
        offset = (self.frame_count % 255)
        self.frame_count += 1
        
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Create colorful gradient
        for y in range(h):
            for x in range(w):
                r = int((x / w) * 255) ^ offset
                g = int((y / h) * 255) ^ offset
                b = int(((x + y) / (w + h)) * 255) ^ offset
                frame[y, x] = [r % 256, g % 256, b % 256]
        
        return frame
    
    def capture_photo(self, filepath: str, quality: int = 92) -> bool:
        """Simulate photo capture."""
        try:
            h, w = self.capture_size[1], self.capture_size[0]
            frame = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
            
            from PIL import Image
            img = Image.fromarray(frame)
            img.save(filepath, quality=quality)
            print(f"[CameraSim] Captured: {filepath}")
            return True
        except Exception as e:
            print(f"[CameraSim] Capture failed: {e}")
            return False
    
    def capture_array(self) -> Optional[np.ndarray]:
        """Capture current frame as array."""
        frame = self.get_preview_frame()
        if frame is not None:
            return frame.copy()
        return None
    
    def set_controls(self, **controls):
        pass
    
    def cleanup(self):
        self.stop_preview()


class EncoderSimulator:
    """Simulated rotary encoder via arrow keys."""
    
    def __init__(self, pin_a, pin_b, debounce_ms, on_clockwise, on_counter_clockwise):
        self.on_cw = on_clockwise
        self.on_ccw = on_counter_clockwise
        self.last_key_time = 0
        self.debounce_s = debounce_ms / 1000.0
        print("[EncoderSim] Use LEFT/RIGHT arrow keys")
    
    def handle_key(self, key):
        """Process keyboard input (called from main loop)."""
        current_time = time.time()
        
        if current_time - self.last_key_time < self.debounce_s:
            return
        
        self.last_key_time = current_time
        
        if key == pygame.K_LEFT and self.on_ccw:
            self.on_ccw()
        elif key == pygame.K_RIGHT and self.on_cw:
            self.on_cw()
    
    def cleanup(self):
        pass


class ButtonSimulator:
    """Simulated button via keyboard."""
    
    def __init__(self, pin, debounce_ms, on_press, on_release=None):
        self.on_press = on_press
        self.on_release = on_release
        self.is_pressed = False
        self.press_start_time = None
        print(f"[ButtonSim] Initialized on pin {pin}")
    
    def handle_key_down(self):
        if not self.is_pressed:
            self.is_pressed = True
            self.press_start_time = time.time()
            if self.on_press:
                self.on_press()
    
    def handle_key_up(self):
        if self.is_pressed:
            self.is_pressed = False
            if self.on_release and self.press_start_time:
                duration = time.time() - self.press_start_time
                self.on_release(duration)
            self.press_start_time = None
    
    def cleanup(self):
        pass


class HapticSimulator:
    """Simulated haptic - console output."""
    
    def __init__(self):
        self.available = True
        print("[HapticSim] Initialized")
    
    def play_effect(self, effect_id: int, strength: float = 1.0):
        effects = {1: "TICK", 10: "CONFIRM", 14: "ERROR", 47: "CAPTURE", 52: "SUCCESS"}
        name = effects.get(effect_id, f"EFFECT_{effect_id}")
        print(f"[HapticSim] {name} @ {strength:.1f}")
    
    def cleanup(self):
        pass


class LightSensorSimulator:
    """Simulated light sensor."""
    
    def __init__(self):
        self.available = True
        self.lux = 150.0
        print("[LightSensorSim] Initialized (use +/- to adjust)")
    
    def read_lux(self) -> float:
        return self.lux
    
    def adjust_lux(self, delta: float):
        self.lux = max(0, min(1000, self.lux + delta))
        print(f"[LightSensorSim] Lux: {self.lux:.0f}")
    
    def cleanup(self):
        pass


class GyroscopeSimulator:
    """Simulated gyroscope."""
    
    def __init__(self, bus_num=1, sample_rate_hz=100):
        self.available = True
        self.tilt_angle = 0.0
        print("[GyroSim] Initialized (use Q/W to tilt)")
    
    def update_tilt(self) -> float:
        return self.tilt_angle
    
    def adjust_tilt(self, delta: float):
        self.tilt_angle += delta
        self.tilt_angle = max(-45, min(45, self.tilt_angle))
        print(f"[GyroSim] Tilt: {self.tilt_angle:.1f}°")
    
    def is_moving(self, threshold: float = 10.0) -> bool:
        return False
    
    def cleanup(self):
        pass


class FlashLEDSimulator:
    """Simulated flash LED."""
    
    def __init__(self, pin=27, max_duration_ms=200):
        self.is_on = False
        print("[FlashSim] Initialized")
    
    def on(self):
        self.is_on = True
        print("[FlashSim] ON")
    
    def off(self):
        self.is_on = False
        print("[FlashSim] OFF")
    
    def pulse(self, duration_ms: int):
        self.on()
        time.sleep(duration_ms / 1000.0)
        self.off()
    
    def cleanup(self):
        self.off()


class BatterySimulator:
    """Simulated battery."""
    
    def __init__(self, bus_num=1):
        self.available = True
        self.percentage = 75
        print("[BatterySim] Initialized (75%)")
    
    def read_percentage(self) -> int:
        return self.percentage
    
    def read_voltage(self) -> float:
        return 3.7 * (self.percentage / 100.0)
    
    def cleanup(self):
        pass


class BrightnessSimulator:
    """Simulated brightness controller."""
    
    def __init__(self):
        self.available = True
        self.brightness = 120
        self.max_brightness = 255
        print("[BrightnessSim] Initialized")
    
    def set_brightness(self, value: int) -> bool:
        self.brightness = max(0, min(self.max_brightness, value))
        print(f"[BrightnessSim] {self.brightness}/{self.max_brightness}")
        return True
    
    def set_brightness_percent(self, percent: int) -> bool:
        value = int(self.max_brightness * percent / 100.0)
        return self.set_brightness(value)
    
    def get_brightness(self) -> int:
        return self.brightness
    
    def auto_brightness_from_lux(self, lux: float, min_brightness: int, max_brightness_val: int) -> int:
        import math
        if lux < 1:
            return min_brightness
        brightness = min_brightness + (max_brightness_val - min_brightness) * math.log(lux + 1) / math.log(501)
        return max(min_brightness, min(max_brightness_val, int(brightness)))