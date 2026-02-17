"""Freeze frame effect after photo capture."""

import pygame
import time
from typing import Optional
import numpy as np


class FreezeFrame:
    """
    Freeze frame effect: displays captured photo for 0.7 seconds.
    """
    
    def __init__(self, duration_ms: int = 700):
        """
        Initialize freeze frame.
        
        Args:
            duration_ms: Freeze duration in milliseconds
        """
        self.duration_ms = duration_ms
        
        # State
        self.is_active = False
        self.freeze_surface: Optional[pygame.Surface] = None
        self.freeze_start_time: Optional[float] = None
        
        print(f"[FreezeFrame] Initialized ({duration_ms}ms)")
    
    def trigger(self, frame: np.ndarray, screen_size: tuple) -> None:
        """
        Trigger freeze frame with captured image.
        
        Args:
            frame: Captured frame (numpy array)
            screen_size: Target screen size (width, height)
        """
        # Convert numpy array to pygame surface
        try:
            # Transpose for pygame (width, height) order
            surf = pygame.surfarray.make_surface(np.swapaxes(frame, 0, 1))
            
            # Scale to screen size
            self.freeze_surface = pygame.transform.scale(surf, screen_size)
            
            # Activate freeze
            self.is_active = True
            self.freeze_start_time = time.time()
            
            print("[FreezeFrame] Activated")
            
        except Exception as e:
            print(f"[FreezeFrame] Failed to create surface: {e}")
            self.is_active = False
    
    def update(self) -> bool:
        """
        Update freeze frame state.
        
        Returns:
            True if still active
        """
        if not self.is_active:
            return False
        
        # Check if duration elapsed
        if self.freeze_start_time is None:
            self.is_active = False
            return False
        
        elapsed_ms = (time.time() - self.freeze_start_time) * 1000
        
        if elapsed_ms >= self.duration_ms:
            self.is_active = False
            self.freeze_surface = None
            print("[FreezeFrame] Deactivated")
            return False
        
        return True
    
    def render(self, screen: pygame.Surface) -> None:
        """
        Render freeze frame if active.
        
        Args:
            screen: Surface to render on
        """
        if self.is_active and self.freeze_surface:
            screen.blit(self.freeze_surface, (0, 0))