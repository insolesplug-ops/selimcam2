"""L3G4200D 3-axis gyroscope driver with tilt estimation."""

import time
import math
from smbus2 import SMBus
from typing import Optional, Tuple
from collections import deque


class Gyroscope:
    """
    L3G4200D 3-axis MEMS gyroscope.
    Provides rotation rate and simplified tilt estimation for level indicator.
    """
    
    # I2C Address
    ADDR = 0x69
    
    # Registers
    REG_WHO_AM_I = 0x0F
    REG_CTRL_REG1 = 0x20
    REG_CTRL_REG2 = 0x21
    REG_CTRL_REG3 = 0x22
    REG_CTRL_REG4 = 0x23
    REG_CTRL_REG5 = 0x24
    REG_OUT_TEMP = 0x26
    REG_STATUS = 0x27
    REG_OUT_X_L = 0x28
    REG_OUT_X_H = 0x29
    REG_OUT_Y_L = 0x2A
    REG_OUT_Y_H = 0x2B
    REG_OUT_Z_L = 0x2C
    REG_OUT_Z_H = 0x2D
    
    # Expected WHO_AM_I value
    WHO_AM_I_VALUE = 0xD3
    
    # Sensitivity (250 dps mode): 8.75 mdps/digit
    SENSITIVITY_250 = 8.75 / 1000.0  # degrees per second per digit
    
    def __init__(self, bus_num: int = 1, sample_rate_hz: int = 100):
        """
        Initialize L3G4200D.
        
        Args:
            bus_num: I2C bus number
            sample_rate_hz: Output data rate (100, 200, 400, 800 Hz)
        """
        self.bus: Optional[SMBus] = None
        self.available = False
        
        # Tilt estimation state
        self.tilt_angle = 0.0  # degrees (-90 to +90)
        self.tilt_history = deque(maxlen=10)  # Smoothing
        
        # Drift compensation
        self.drift_bias_x = 0.0
        self.drift_bias_y = 0.0
        self.drift_bias_z = 0.0
        self.last_update_time = time.time()
        
        try:
            self.bus = SMBus(bus_num)
            
            # Check WHO_AM_I
            who_am_i = self.bus.read_byte_data(self.ADDR, self.REG_WHO_AM_I)
            if who_am_i != self.WHO_AM_I_VALUE:
                raise RuntimeError(f"Wrong WHO_AM_I: 0x{who_am_i:02X}, expected 0x{self.WHO_AM_I_VALUE:02X}")
            
            # Configure gyroscope
            self._configure(sample_rate_hz)
            
            # Calibrate (measure bias while stationary)
            self._calibrate()
            
            self.available = True
            print(f"[L3G4200D] Initialized @ {sample_rate_hz}Hz")
            
        except Exception as e:
            print(f"[L3G4200D] Init failed: {e}")
            self.available = False
    
    def _configure(self, sample_rate_hz: int) -> None:
        """Configure gyroscope registers."""
        if not self.bus:
            return
        
        # CTRL_REG1: Enable all axes, set ODR
        # Bits 7-6: DR (data rate)
        # Bits 5-4: BW (bandwidth)
        # Bit 3: PD (power down, 1=normal)
        # Bit 2: Zen (Z enable)
        # Bit 1: Yen (Y enable)
        # Bit 0: Xen (X enable)
        
        if sample_rate_hz >= 800:
            odr_bits = 0b11  # 800 Hz
        elif sample_rate_hz >= 400:
            odr_bits = 0b10  # 400 Hz
        elif sample_rate_hz >= 200:
            odr_bits = 0b01  # 200 Hz
        else:
            odr_bits = 0b00  # 100 Hz
        
        ctrl_reg1 = (odr_bits << 6) | 0x0F  # Enable all axes + normal mode
        self.bus.write_byte_data(self.ADDR, self.REG_CTRL_REG1, ctrl_reg1)
        
        # CTRL_REG4: Full scale selection (250 dps)
        # Bits 5-4: FS (00 = 250 dps)
        ctrl_reg4 = 0x00
        self.bus.write_byte_data(self.ADDR, self.REG_CTRL_REG4, ctrl_reg4)
        
        time.sleep(0.1)  # Stabilize
    
    def _calibrate(self, samples: int = 100) -> None:
        """
        Calibrate gyroscope by measuring bias while stationary.
        
        Args:
            samples: Number of samples for calibration
        """
        if not self.bus or not self.available:
            return
        
        print("[L3G4200D] Calibrating (keep device still)...")
        
        sum_x, sum_y, sum_z = 0.0, 0.0, 0.0
        
        for _ in range(samples):
            x, y, z = self._read_raw_rotation()
            sum_x += x
            sum_y += y
            sum_z += z
            time.sleep(0.01)
        
        self.drift_bias_x = sum_x / samples
        self.drift_bias_y = sum_y / samples
        self.drift_bias_z = sum_z / samples
        
        print(f"[L3G4200D] Calibration complete: bias=({self.drift_bias_x:.2f}, {self.drift_bias_y:.2f}, {self.drift_bias_z:.2f})")
    
    def _read_raw_rotation(self) -> Tuple[float, float, float]:
        """
        Read raw rotation rates.
        
        Returns:
            (x_dps, y_dps, z_dps) in degrees per second
        """
        if not self.bus:
            return (0.0, 0.0, 0.0)
        
        try:
            # Read 6 bytes (X, Y, Z) with auto-increment
            data = self.bus.read_i2c_block_data(self.ADDR, 0x80 | self.REG_OUT_X_L, 6)
            
            # Combine bytes (little endian, signed 16-bit)
            x_raw = self._to_signed_16(data[0] | (data[1] << 8))
            y_raw = self._to_signed_16(data[2] | (data[3] << 8))
            z_raw = self._to_signed_16(data[4] | (data[5] << 8))
            
            # Convert to dps
            x_dps = x_raw * self.SENSITIVITY_250
            y_dps = y_raw * self.SENSITIVITY_250
            z_dps = z_raw * self.SENSITIVITY_250
            
            return (x_dps, y_dps, z_dps)
            
        except Exception as e:
            return (0.0, 0.0, 0.0)
    
    def read_rotation(self) -> Tuple[float, float, float]:
        """
        Read calibrated rotation rates.
        
        Returns:
            (x_dps, y_dps, z_dps) with bias compensation
        """
        x, y, z = self._read_raw_rotation()
        
        # Apply bias compensation
        x -= self.drift_bias_x
        y -= self.drift_bias_y
        z -= self.drift_bias_z
        
        return (x, y, z)
    
    def update_tilt(self) -> float:
        """
        Update tilt angle estimation (simplified integration).
        
        NOTE: Without accelerometer, this will drift over time.
        We reset drift periodically when device appears still.
        
        Returns:
            Current tilt angle in degrees (-90 to +90)
        """
        if not self.available:
            return 0.0
        
        # Get rotation rate
        x_dps, y_dps, z_dps = self.read_rotation()
        
        # Calculate time delta
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Check if device is still (for drift reset)
        motion_threshold = 5.0  # dps
        is_still = (abs(x_dps) < motion_threshold and 
                   abs(y_dps) < motion_threshold and 
                   abs(z_dps) < motion_threshold)
        
        if is_still:
            # Slowly decay tilt back to zero (drift compensation)
            self.tilt_angle *= 0.98
        else:
            # Integrate Y-axis rotation for roll angle
            # (Assuming device is held vertically, Y-axis represents roll)
            delta_angle = y_dps * dt
            self.tilt_angle += delta_angle
            
            # Clamp to realistic range
            self.tilt_angle = max(-90, min(90, self.tilt_angle))
        
        # Smooth with history
        self.tilt_history.append(self.tilt_angle)
        smoothed_tilt = sum(self.tilt_history) / len(self.tilt_history)
        
        return smoothed_tilt
    
    def is_moving(self, threshold: float = 10.0) -> bool:
        """
        Check if device is moving.
        
        Args:
            threshold: Motion threshold in dps
        
        Returns:
            True if any axis exceeds threshold
        """
        x, y, z = self.read_rotation()
        return (abs(x) > threshold or abs(y) > threshold or abs(z) > threshold)
    
    @staticmethod
    def _to_signed_16(value: int) -> int:
        """Convert unsigned 16-bit to signed."""
        if value > 32767:
            return value - 65536
        return value
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        if self.bus:
            try:
                # Power down
                self.bus.write_byte_data(self.ADDR, self.REG_CTRL_REG1, 0x00)
                self.bus.close()
            except:
                pass