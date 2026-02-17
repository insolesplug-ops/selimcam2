"""Flash LED control with precise timing and safety."""

import time
import threading
from gpiozero import OutputDevice
from typing import Optional


class FlashLED:
    """
    Flash LED controller with precise pulse timing.
    Controls LED via GPIO through BC337 transistor.
    """
    
    def __init__(self, pin: int = 27, max_duration_ms: int = 200):
        """
        Initialize flash LED.
        
        Args:
            pin: BCM GPIO pin
            max_duration_ms: Maximum pulse duration for safety
        """
        self.led = OutputDevice(pin, initial_value=False)
        self.max_duration_ms = max_duration_ms
        
        # Safety: watchdog timer
        self._watchdog_timer: Optional[threading.Timer] = None
        self._is_on = False
        
        print(f"[Flash LED] Initialized on GPIO{pin}")
    
    def on(self) -> None:
        """Turn flash LED on."""
        if not self._is_on:
            self.led.on()
            self._is_on = True
            
            # Safety watchdog: force off after max duration
            self._start_watchdog()
    
    def off(self) -> None:
        """Turn flash LED off."""
        if self._is_on:
            self.led.off()
            self._is_on = False
            
            # Cancel watchdog
            self._cancel_watchdog()
    
    def pulse(self, duration_ms: int) -> None:
        """
        Pulse flash LED for specified duration.
        
        Args:
            duration_ms: Pulse duration in milliseconds
        """
        # Safety clamp
        duration_ms = min(duration_ms, self.max_duration_ms)
        
        self.on()
        time.sleep(duration_ms / 1000.0)
        self.off()
    
    def pulse_async(self, duration_ms: int) -> None:
        """
        Pulse flash LED asynchronously (non-blocking).
        
        Args:
            duration_ms: Pulse duration in milliseconds
        """
        def _pulse():
            self.pulse(duration_ms)
        
        thread = threading.Thread(target=_pulse, daemon=True)
        thread.start()
    
    def _start_watchdog(self) -> None:
        """Start watchdog timer for safety."""
        self._cancel_watchdog()
        
        def _watchdog_timeout():
            print("[Flash LED] Watchdog timeout - forcing OFF")
            self.off()
        
        self._watchdog_timer = threading.Timer(
            self.max_duration_ms / 1000.0,
            _watchdog_timeout
        )
        self._watchdog_timer.start()
    
    def _cancel_watchdog(self) -> None:
        """Cancel watchdog timer."""
        if self._watchdog_timer:
            self._watchdog_timer.cancel()
            self._watchdog_timer = None
    
    @property
    def is_on(self) -> bool:
        """Check if LED is currently on."""
        return self._is_on
    
    def cleanup(self) -> None:
        """Cleanup resources - ensure LED is off."""
        self.off()
        self.led.close()
        print("[Flash LED] Cleanup complete")