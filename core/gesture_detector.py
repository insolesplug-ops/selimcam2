"""Touch gesture detector for swipes and taps."""

import time
from typing import Optional, Tuple
from enum import Enum, auto


class GestureType(Enum):
    """Detected gesture types."""
    TAP = auto()
    SWIPE_LEFT = auto()
    SWIPE_RIGHT = auto()
    SWIPE_UP = auto()
    SWIPE_DOWN = auto()


class GestureDetector:
    """
    Detects touch gestures (tap, swipe).
    Optimized for gallery navigation.
    """
    
    def __init__(self, 
                 swipe_threshold: int = 60,
                 swipe_max_time: float = 0.4,
                 tap_max_time: float = 0.3,
                 tap_max_distance: int = 20):
        """
        Initialize gesture detector.
        
        Args:
            swipe_threshold: Minimum distance for swipe (pixels)
            swipe_max_time: Maximum time for swipe (seconds)
            tap_max_time: Maximum time for tap (seconds)
            tap_max_distance: Maximum movement for tap (pixels)
        """
        self.swipe_threshold = swipe_threshold
        self.swipe_max_time = swipe_max_time
        self.tap_max_time = tap_max_time
        self.tap_max_distance = tap_max_distance
        
        # Touch tracking
        self.touch_start_pos: Optional[Tuple[int, int]] = None
        self.touch_start_time: Optional[float] = None
        
        print("[GestureDetector] Initialized")
    
    def on_touch_down(self, x: int, y: int) -> None:
        """
        Handle touch down event.
        
        Args:
            x, y: Touch position
        """
        self.touch_start_pos = (x, y)
        self.touch_start_time = time.time()
    
    def on_touch_up(self, x: int, y: int) -> Optional[GestureType]:
        """
        Handle touch up event and detect gesture.
        
        Args:
            x, y: Touch release position
        
        Returns:
            Detected gesture or None
        """
        if self.touch_start_pos is None or self.touch_start_time is None:
            return None
        
        # Calculate delta
        dx = x - self.touch_start_pos[0]
        dy = y - self.touch_start_pos[1]
        distance = (dx**2 + dy**2) ** 0.5
        duration = time.time() - self.touch_start_time
        
        # Reset tracking
        self.touch_start_pos = None
        self.touch_start_time = None
        
        # Detect gesture
        
        # Tap: short duration, small movement
        if duration < self.tap_max_time and distance < self.tap_max_distance:
            return GestureType.TAP
        
        # Swipe: within time limit and above threshold
        if duration < self.swipe_max_time and distance >= self.swipe_threshold:
            # Determine direction (dominant axis)
            if abs(dx) > abs(dy):
                # Horizontal swipe
                if dx > 0:
                    return GestureType.SWIPE_RIGHT
                else:
                    return GestureType.SWIPE_LEFT
            else:
                # Vertical swipe
                if dy > 0:
                    return GestureType.SWIPE_DOWN
                else:
                    return GestureType.SWIPE_UP
        
        # No gesture detected
        return None
    
    def cancel(self) -> None:
        """Cancel current touch tracking."""
        self.touch_start_pos = None
        self.touch_start_time = None