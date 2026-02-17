"""Debounced button with press/release callbacks."""

import time
from typing import Callable, Optional

try:
    from gpiozero import Button
    GPIOZERO_AVAILABLE = True
except ImportError:
    GPIOZERO_AVAILABLE = False


class DebouncedButton:
    """Button with debouncing and long-press detection."""
    
    def __init__(self,
                 pin: int,
                 debounce_ms: float = 50,
                 on_press: Optional[Callable] = None,
                 on_release: Optional[Callable] = None):
        """Initialize button."""
        
        if not GPIOZERO_AVAILABLE:
            raise RuntimeError("gpiozero not available - use ButtonSimulator")
        
        self.on_press = on_press
        self.on_release = on_release
        
        self.button = Button(pin, bounce_time=debounce_ms / 1000.0)
        
        self.press_start_time: Optional[float] = None
        
        # Setup callbacks
        self.button.when_pressed = self._handle_press
        self.button.when_released = self._handle_release
        
        print(f"[DebouncedButton] Initialized on pin {pin}")
    
    def _handle_press(self):
        self.press_start_time = time.time()
        if self.on_press:
            self.on_press()
    
    def _handle_release(self):
        if self.on_release and self.press_start_time:
            duration = time.time() - self.press_start_time
            self.on_release(duration)
        self.press_start_time = None
    
    def cleanup(self):
        if hasattr(self, 'button'):
            self.button.close()