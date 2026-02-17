"""Real-time image filter engine with LUT-based processing."""

import numpy as np
from typing import Optional, Callable, Dict
from enum import Enum


class FilterType(Enum):
    """Available filter types."""
    NONE = "none"
    NIGHT_VISION = "night_vision"
    RED = "red"
    GREEN = "green"
    PINK = "pink"
    WARM = "warm"
    COLD = "cold"
    MONOCHROM = "monochrom"
    ORANGE = "orange"
    YELLOW = "yellow"


class FilterEngine:
    """
    Real-time image filter engine optimized for Raspberry Pi 3B+.
    Uses LUT (Look-Up Table) approach for maximum performance.
    """
    
    def __init__(self):
        """Initialize filter engine."""
        # Pre-computed LUTs
        self._luts: Dict[FilterType, Optional[np.ndarray]] = {}
        
        # ISO fake gain (brightness adjustment)
        self._iso_gain = 1.0
        
        # Build LUTs
        self._build_luts()
        
        print("[FilterEngine] Initialized with LUTs")
    
    def _build_luts(self) -> None:
        """Pre-compute lookup tables for filters."""
        # LUT structure: 256x3 array mapping input RGB to output RGB
        
        # Monochrome LUT
        mono_lut = np.zeros((256, 3), dtype=np.uint8)
        for i in range(256):
            # Standard luminance formula
            mono_lut[i] = [i, i, i]
        self._luts[FilterType.MONOCHROM] = mono_lut
        
        # Warm LUT (boost red/yellow)
        warm_lut = np.zeros((256, 3), dtype=np.uint8)
        for i in range(256):
            r = min(255, int(i * 1.15))  # +15% red
            g = min(255, int(i * 1.05))  # +5% green
            b = max(0, int(i * 0.9))     # -10% blue
            warm_lut[i] = [r, g, b]
        self._luts[FilterType.WARM] = warm_lut
        
        # Cold LUT (boost blue)
        cold_lut = np.zeros((256, 3), dtype=np.uint8)
        for i in range(256):
            r = max(0, int(i * 0.9))     # -10% red
            g = min(255, int(i * 1.0))   # no change
            b = min(255, int(i * 1.2))   # +20% blue
            cold_lut[i] = [r, g, b]
        self._luts[FilterType.COLD] = cold_lut
        
        # Other filters will be computed on-the-fly (simpler operations)
    
    def apply_filter(self, frame: np.ndarray, filter_type: FilterType) -> np.ndarray:
        """
        Apply filter to frame.
        
        Args:
            frame: Input RGB frame (HxWx3, uint8)
            filter_type: Filter to apply
        
        Returns:
            Filtered frame
        """
        if filter_type == FilterType.NONE:
            return frame
        
        # Copy frame (avoid modifying input)
        output = frame.copy()
        
        # Apply filter
        if filter_type == FilterType.MONOCHROM:
            # Grayscale conversion
            gray = (0.299 * output[:,:,0] + 
                   0.587 * output[:,:,1] + 
                   0.114 * output[:,:,2]).astype(np.uint8)
            output[:,:,0] = gray
            output[:,:,1] = gray
            output[:,:,2] = gray
        
        elif filter_type == FilterType.NIGHT_VISION:
            # Strong green channel, boost brightness
            gray = (0.299 * output[:,:,0] + 
                   0.587 * output[:,:,1] + 
                   0.114 * output[:,:,2]).astype(np.uint8)
            # Boost and apply green tint
            boosted = np.clip(gray.astype(np.float32) * 1.5, 0, 255).astype(np.uint8)
            output[:,:,0] = boosted // 4  # Dim red
            output[:,:,1] = boosted       # Full green
            output[:,:,2] = boosted // 4  # Dim blue
        
        elif filter_type == FilterType.RED:
            # Boost red channel
            output[:,:,0] = np.clip(output[:,:,0].astype(np.float32) * 1.5, 0, 255).astype(np.uint8)
            output[:,:,1] = (output[:,:,1] * 0.5).astype(np.uint8)
            output[:,:,2] = (output[:,:,2] * 0.5).astype(np.uint8)
        
        elif filter_type == FilterType.GREEN:
            # Boost green channel
            output[:,:,0] = (output[:,:,0] * 0.5).astype(np.uint8)
            output[:,:,1] = np.clip(output[:,:,1].astype(np.float32) * 1.5, 0, 255).astype(np.uint8)
            output[:,:,2] = (output[:,:,2] * 0.5).astype(np.uint8)
        
        elif filter_type == FilterType.PINK:
            # Pink tint
            output[:,:,0] = np.clip(output[:,:,0].astype(np.float32) * 1.3, 0, 255).astype(np.uint8)
            output[:,:,1] = (output[:,:,1] * 0.8).astype(np.uint8)
            output[:,:,2] = np.clip(output[:,:,2].astype(np.float32) * 1.2, 0, 255).astype(np.uint8)
        
        elif filter_type == FilterType.WARM:
            # Apply warm LUT
            output = self._apply_lut_per_channel(output, self._luts[FilterType.WARM])
        
        elif filter_type == FilterType.COLD:
            # Apply cold LUT
            output = self._apply_lut_per_channel(output, self._luts[FilterType.COLD])
        
        elif filter_type == FilterType.ORANGE:
            # Orange tint
            output[:,:,0] = np.clip(output[:,:,0].astype(np.float32) * 1.4, 0, 255).astype(np.uint8)
            output[:,:,1] = np.clip(output[:,:,1].astype(np.float32) * 1.1, 0, 255).astype(np.uint8)
            output[:,:,2] = (output[:,:,2] * 0.6).astype(np.uint8)
        
        elif filter_type == FilterType.YELLOW:
            # Yellow tint
            output[:,:,0] = np.clip(output[:,:,0].astype(np.float32) * 1.3, 0, 255).astype(np.uint8)
            output[:,:,1] = np.clip(output[:,:,1].astype(np.float32) * 1.3, 0, 255).astype(np.uint8)
            output[:,:,2] = (output[:,:,2] * 0.7).astype(np.uint8)
        
        return output
    
    def _apply_lut_per_channel(self, frame: np.ndarray, lut: np.ndarray) -> np.ndarray:
        """Apply LUT to each channel."""
        output = frame.copy()
        output[:,:,0] = lut[frame[:,:,0], 0]
        output[:,:,1] = lut[frame[:,:,1], 1]
        output[:,:,2] = lut[frame[:,:,2], 2]
        return output
    
    def apply_iso_gain(self, frame: np.ndarray, iso_value: int) -> np.ndarray:
        """
        Apply ISO fake gain (brightness adjustment).
        
        Args:
            frame: Input frame
            iso_value: ISO value (100, 200, 400, 800)
        
        Returns:
            Adjusted frame
        """
        # Map ISO to gain
        gain_map = {
            100: 0.7,
            200: 0.85,
            400: 1.0,
            800: 1.3
        }
        
        gain = gain_map.get(iso_value, 1.0)
        
        if gain == 1.0:
            return frame
        
        # Apply gain with clipping
        adjusted = np.clip(frame.astype(np.float32) * gain, 0, 255).astype(np.uint8)
        
        return adjusted
    
    def process_frame(self, frame: np.ndarray, 
                     filter_type: FilterType,
                     iso_value: int = 400) -> np.ndarray:
        """
        Full processing pipeline: ISO + Filter.
        
        Args:
            frame: Input frame
            filter_type: Filter to apply
            iso_value: ISO fake value
        
        Returns:
            Processed frame
        """
        # Apply ISO gain first
        processed = self.apply_iso_gain(frame, iso_value)
        
        # Apply filter
        processed = self.apply_filter(processed, filter_type)
        
        return processed