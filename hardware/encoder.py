"""Rotary encoder driver with Gray-code decoding."""

import time
from typing import Callable, Optional

try:
    from gpiozero import RotaryEncoder as GPIORotaryEncoder
    GPIOZERO_AVAILABLE = True
except ImportError:
    GPIOZERO_AVAILABLE = False


class RotaryEncoder:
    """Rotary encoder with callbacks."""
    
    def __init__(self, 
                 pin_a: int,
                 pin_b: int,
                 debounce_ms: float = 2.0,
                 on_clockwise: Optional[Callable] = None,
                 on_counter_clockwise: Optional[Callable] = None):
        """Initialize encoder."""
        
        if not GPIOZERO_AVAILABLE:
            raise RuntimeError("gpiozero not available - use EncoderSimulator")
        
        self.on_cw = on_clockwise
        self.on_ccw = on_counter_clockwise
        
        self.encoder = GPIORotaryEncoder(pin_a, pin_b, max_steps=0)
        
        # Setup callbacks
        self.encoder.when_rotated_clockwise = self._handle_cw
        self.encoder.when_rotated_counter_clockwise = self._handle_ccw
        
        print(f"[RotaryEncoder] Initialized on pins {pin_a}/{pin_b}")
    
    def _handle_cw(self):
        if self.on_cw:
            self.on_cw()
    
    def _handle_ccw(self):
        if self.on_ccw:
            self.on_ccw()
    
    def cleanup(self):
        if hasattr(self, 'encoder'):
            self.encoder.close()