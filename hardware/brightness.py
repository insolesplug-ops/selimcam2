"""Display backlight brightness control."""

import os
import time
from pathlib import Path
from typing import Optional


class BrightnessController:
    """
    Display backlight brightness controller.
    Controls via sysfs interface.
    """
    
    # Common backlight paths
    BACKLIGHT_PATHS = [
        "/sys/class/backlight/rpi_backlight/brightness",
        "/sys/class/backlight/10-0045/brightness",  # Common DSI path
        "/sys/class/backlight/backlight/brightness"
    ]
    
    MAX_BRIGHTNESS_PATHS = [
        "/sys/class/backlight/rpi_backlight/max_brightness",
        "/sys/class/backlight/10-0045/max_brightness",
        "/sys/class/backlight/backlight/max_brightness"
    ]
    
    def __init__(self):
        """Initialize brightness controller."""
        self.brightness_path: Optional[Path] = None
        self.max_brightness = 255
        self.available = False
        
        # Find backlight interface
        for path in self.BACKLIGHT_PATHS:
            if os.path.exists(path):
                self.brightness_path = Path(path)
                break
        
        if self.brightness_path:
            # Get max brightness
            for path in self.MAX_BRIGHTNESS_PATHS:
                if os.path.exists(path):
                    try:
                        with open(path, 'r') as f:
                            self.max_brightness = int(f.read().strip())
                        break
                    except:
                        pass
            
            self.available = True
            print(f"[Brightness] Controller initialized (max={self.max_brightness})")
        else:
            print("[Brightness] No backlight interface found")
    
    def set_brightness(self, value: int) -> bool:
        """
        Set display brightness.
        
        Args:
            value: Brightness value (0 to max_brightness)
        
        Returns:
            True if successful
        """
        if not self.available or not self.brightness_path:
            return False
        
        # Clamp value
        value = max(0, min(self.max_brightness, value))
        
        try:
            with open(self.brightness_path, 'w') as f:
                f.write(str(value))
            return True
        except Exception as e:
            print(f"[Brightness] Set failed: {e}")
            return False
    
    def set_brightness_percent(self, percent: int) -> bool:
        """
        Set display brightness as percentage.
        
        Args:
            percent: Brightness percentage (0-100)
        
        Returns:
            True if successful
        """
        percent = max(0, min(100, percent))
        value = int(self.max_brightness * percent / 100.0)
        return self.set_brightness(value)
    
    def get_brightness(self) -> Optional[int]:
        """
        Get current brightness value.
        
        Returns:
            Current brightness or None if unavailable
        """
        if not self.available or not self.brightness_path:
            return None
        
        try:
            with open(self.brightness_path, 'r') as f:
                return int(f.read().strip())
        except:
            return None
    
    def auto_brightness_from_lux(self, lux: float, 
                                 min_brightness: int = 40,
                                 max_brightness_val: int = 220) -> int:
        """
        Calculate brightness from lux reading.
        
        Args:
            lux: Ambient light in lux
            min_brightness: Minimum brightness value
            max_brightness_val: Maximum brightness value
        
        Returns:
            Calculated brightness value
        """
        import math
        
        # Logarithmic mapping: brightness = a * log(lux + 1) + b
        # Calibration points:
        # - 0 lux -> min_brightness
        # - 500 lux -> max_brightness_val
        
        if lux < 1:
            return min_brightness
        
        # Logarithmic scale
        brightness = min_brightness + (max_brightness_val - min_brightness) * math.log(lux + 1) / math.log(501)
        
        # Clamp
        brightness = max(min_brightness, min(max_brightness_val, int(brightness)))
        
        return brightness