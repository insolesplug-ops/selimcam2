"""DRV2605L haptic driver with effect library."""

import time
from smbus2 import SMBus
from typing import Optional


class HapticDriver:
    """
    DRV2605L haptic motor driver.
    Supports LRA (Linear Resonant Actuator) with effect library.
    """
    
    # I2C Address
    ADDR = 0x5A
    
    # Registers
    REG_STATUS = 0x00
    REG_MODE = 0x01
    REG_LIBRARY = 0x03
    REG_WAVEFORM_SEQ_1 = 0x04
    REG_WAVEFORM_SEQ_2 = 0x05
    REG_GO = 0x0C
    REG_OVERDRIVE_OFFSET = 0x0D
    REG_SUSTAIN_OFFSET_POS = 0x0E
    REG_SUSTAIN_OFFSET_NEG = 0x0F
    REG_BRAKE_TIME_OFFSET = 0x10
    REG_RATED_VOLTAGE = 0x16
    REG_CLAMP_VOLTAGE = 0x17
    REG_FEEDBACK_CONTROL = 0x1A
    REG_CONTROL3 = 0x1D
    
    # Modes
    MODE_INTERNAL_TRIGGER = 0x00
    MODE_EXT_TRIGGER_EDGE = 0x01
    MODE_EXT_TRIGGER_LEVEL = 0x02
    MODE_PWM_ANALOG = 0x03
    MODE_AUDIO = 0x04
    MODE_REAL_TIME = 0x05
    MODE_DIAGNOSTICS = 0x06
    MODE_AUTO_CALIBRATION = 0x07
    
    # Libraries
    LIB_EMPTY = 0x00
    LIB_LRA = 0x06  # LRA library for coin-type actuators
    
    def __init__(self, bus_num: int = 1):
        """
        Initialize DRV2605L.
        
        Args:
            bus_num: I2C bus number (usually 1 on Pi)
        """
        self.bus: Optional[SMBus] = None
        self.available = False
        
        try:
            self.bus = SMBus(bus_num)
            
            # Check device presence
            status = self.bus.read_byte_data(self.ADDR, self.REG_STATUS)
            print(f"[DRV2605L] Device found, status: 0x{status:02X}")
            
            # Initialize for LRA
            self._init_lra()
            
            self.available = True
            print("[DRV2605L] Initialized successfully")
            
        except Exception as e:
            print(f"[DRV2605L] Init failed: {e}")
            self.available = False
    
    def _init_lra(self) -> None:
        """Initialize for LRA (Linear Resonant Actuator)."""
        if not self.bus:
            return
        
        try:
            # Exit standby
            self.bus.write_byte_data(self.ADDR, self.REG_MODE, MODE_INTERNAL_TRIGGER)
            time.sleep(0.001)
            
            # Select LRA library
            self.bus.write_byte_data(self.ADDR, self.REG_LIBRARY, self.LIB_LRA)
            
            # Configure feedback control for LRA
            # Bit 7: N_ERM_LRA = 1 (LRA mode)
            # Bits 6-4: FB_BRAKE_FACTOR = 3
            # Bits 3-2: LOOP_GAIN = 2 (medium)
            # Bit 0: BEMF_GAIN = 0
            feedback = 0xB6  # 10110110
            self.bus.write_byte_data(self.ADDR, self.REG_FEEDBACK_CONTROL, feedback)
            
            # Set rated voltage for 10mm LRA coin (typical: 1.3V RMS)
            # Voltage = value * 5.6V / 255
            # For 1.3V: value = 1.3 * 255 / 5.6 ≈ 59 (0x3B)
            rated_voltage = 0x59  # 1.6V for stronger feel
            self.bus.write_byte_data(self.ADDR, self.REG_RATED_VOLTAGE, rated_voltage)
            
            # Set overdrive clamp voltage (peak, ~2V)
            clamp_voltage = 0x89  # 2.5V
            self.bus.write_byte_data(self.ADDR, self.REG_CLAMP_VOLTAGE, clamp_voltage)
            
            # Control3: Enable analog input, ERM/LRA auto-resonance
            control3 = 0x20  # Bit 5: ERM_OPEN_LOOP = 0, Bit 3: N_PWM_ANALOG = 1
            self.bus.write_byte_data(self.ADDR, self.REG_CONTROL3, control3)
            
            print("[DRV2605L] LRA configuration complete")
            
        except Exception as e:
            print(f"[DRV2605L] LRA init error: {e}")
    
    def play_effect(self, effect_id: int, strength: float = 1.0) -> None:
        """
        Play a haptic effect from the library.
        
        Args:
            effect_id: Effect number (1-123)
            strength: Intensity multiplier (0.0-1.0)
        
        Common effects for LRA library (0x06):
            1: Strong Click 100%
            10: Soft Bump 100%
            14: Double Click 100%
            47: Sharp Click 100%
            52: Short Double Click Strong 100%
        """
        if not self.available or not self.bus:
            return
        
        try:
            # Clamp values
            effect_id = max(1, min(123, effect_id))
            strength = max(0.0, min(1.0, strength))
            
            # Set overdrive offset (strength control)
            # Positive offset increases drive strength
            overdrive = int(strength * 127)  # 0-127
            self.bus.write_byte_data(self.ADDR, self.REG_OVERDRIVE_OFFSET, overdrive)
            
            # Set waveform sequence
            self.bus.write_byte_data(self.ADDR, self.REG_WAVEFORM_SEQ_1, effect_id)
            self.bus.write_byte_data(self.ADDR, self.REG_WAVEFORM_SEQ_2, 0x00)  # End marker
            
            # Trigger playback
            self.bus.write_byte_data(self.ADDR, self.REG_GO, 0x01)
            
        except Exception as e:
            print(f"[DRV2605L] Play effect error: {e}")
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        if self.bus:
            try:
                # Enter standby mode
                self.bus.write_byte_data(self.ADDR, self.REG_MODE, 0x40)
                self.bus.close()
            except:
                pass


# Pre-defined effect patterns
class HapticEffects:
    """Pre-defined haptic effect IDs for common UI interactions."""
    TICK = 1         # Very light click (encoder detent)
    CONFIRM = 10     # Soft bump (selection confirm)
    CAPTURE = 47     # Sharp click (photo capture)
    ERROR = 14       # Double click (error/warning)
    SUCCESS = 52     # Double sharp click (success)