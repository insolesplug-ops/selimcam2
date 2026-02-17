"""Battery monitoring via Waveshare UPS HAT (C)."""

import time
from smbus2 import SMBus
from typing import Optional


class BatteryMonitor:
    """
    Waveshare UPS HAT (C) battery monitor.
    
    NOTE: Actual I2C address and registers depend on UPS HAT model.
    This is a template - adjust based on your specific HAT.
    """
    
    # Common I2C addresses for fuel gauges
    POSSIBLE_ADDRS = [0x36, 0x55, 0x62]  # MAX17043, INA219, etc.
    
    def __init__(self, bus_num: int = 1):
        """
        Initialize battery monitor.
        
        Args:
            bus_num: I2C bus number
        """
        self.bus: Optional[SMBus] = None
        self.available = False
        self.addr: Optional[int] = None
        
        try:
            self.bus = SMBus(bus_num)
            
            # Try to detect fuel gauge
            for addr in self.POSSIBLE_ADDRS:
                try:
                    # Attempt read
                    self.bus.read_byte(addr)
                    self.addr = addr
                    print(f"[Battery] Found device at 0x{addr:02X}")
                    break
                except:
                    continue
            
            if self.addr:
                self.available = True
                print("[Battery] Monitor initialized")
            else:
                print("[Battery] No fuel gauge detected - using fallback")
                
        except Exception as e:
            print(f"[Battery] Init failed: {e}")
            self.available = False
    
    def read_percentage(self) -> Optional[int]:
        """
        Read battery percentage.
        
        Returns:
            Battery percentage (0-100) or None if unavailable
        """
        if not self.available or not self.bus or not self.addr:
            return None
        
        try:
            # Example for MAX17043 fuel gauge
            if self.addr == 0x36:
                # Read SOC register (0x04-0x05)
                data = self.bus.read_i2c_block_data(self.addr, 0x04, 2)
                soc_raw = (data[0] << 8) | data[1]
                percentage = soc_raw / 256.0
                return int(percentage)
            
            # Fallback: return None
            return None
            
        except Exception as e:
            return None
    
    def read_voltage(self) -> Optional[float]:
        """
        Read battery voltage.
        
        Returns:
            Voltage in volts or None if unavailable
        """
        if not self.available or not self.bus or not self.addr:
            return None
        
        try:
            # Example for MAX17043
            if self.addr == 0x36:
                data = self.bus.read_i2c_block_data(self.addr, 0x02, 2)
                vcell_raw = (data[0] << 8) | data[1]
                voltage = vcell_raw * 78.125 / 1000000.0  # Convert to volts
                return voltage
            
            return None
            
        except:
            return None
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        if self.bus:
            try:
                self.bus.close()
            except:
                pass