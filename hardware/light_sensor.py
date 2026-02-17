"""BH1750 ambient light sensor driver."""

import time
from smbus2 import SMBus
from typing import Optional
from collections import deque


class LightSensor:
    """
    BH1750 digital light sensor.
    Provides lux readings for auto-brightness and auto-flash.
    """
    
    # I2C Address
    ADDR = 0x23
    
    # Commands
    POWER_DOWN = 0x00
    POWER_ON = 0x01
    RESET = 0x07
    CONTINUOUS_HIGH_RES = 0x10  # 1 lux resolution
    CONTINUOUS_HIGH_RES2 = 0x11  # 0.5 lux resolution
    CONTINUOUS_LOW_RES = 0x13    # 4 lux resolution
    ONE_TIME_HIGH_RES = 0x20
    ONE_TIME_HIGH_RES2 = 0x21
    ONE_TIME_LOW_RES = 0x23
    
    def __init__(self, bus_num: int = 1, mode: int = CONTINUOUS_HIGH_RES, 
                 avg_window: int = 5):
        """
        Initialize BH1750.
        
        Args:
            bus_num: I2C bus number
            mode: Measurement mode (default: continuous high-res)
            avg_window: Number of samples for moving average
        """
        self.bus: Optional[SMBus] = None
        self.available = False
        self.mode = mode
        
        # Moving average filter
        self.lux_history = deque(maxlen=avg_window)
        
        try:
            self.bus = SMBus(bus_num)
            
            # Power on
            self.bus.write_byte(self.ADDR, self.POWER_ON)
            time.sleep(0.01)
            
            # Start measurement
            self.bus.write_byte(self.ADDR, self.mode)
            time.sleep(0.18)  # Wait for first measurement
            
            # Test read
            test_lux = self._read_raw()
            print(f"[BH1750] Device found, initial reading: {test_lux:.1f} lux")
            
            self.available = True
            print("[BH1750] Initialized successfully")
            
        except Exception as e:
            print(f"[BH1750] Init failed: {e}")
            self.available = False
    
    def _read_raw(self) -> float:
        """
        Read raw lux value.
        
        Returns:
            Lux value, or 0.0 on error
        """
        if not self.bus or not self.available:
            return 0.0
        
        try:
            # Read 2 bytes
            data = self.bus.read_i2c_block_data(self.ADDR, self.mode, 2)
            
            # Convert to lux
            # Formula: lux = (high_byte << 8 | low_byte) / 1.2
            raw = (data[0] << 8) | data[1]
            lux = raw / 1.2
            
            return lux
            
        except Exception as e:
            print(f"[BH1750] Read error: {e}")
            return 0.0
    
    def read_lux(self) -> float:
        """
        Read filtered lux value with moving average.
        
        Returns:
            Smoothed lux value
        """
        raw_lux = self._read_raw()
        
        # Add to history
        self.lux_history.append(raw_lux)
        
        # Return average
        if len(self.lux_history) > 0:
            return sum(self.lux_history) / len(self.lux_history)
        else:
            return raw_lux
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        if self.bus:
            try:
                self.bus.write_byte(self.ADDR, self.POWER_DOWN)
                self.bus.close()
            except:
                pass