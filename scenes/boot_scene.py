"""Boot scene - minimal, just show boot_logo."""

import pygame
import time
from typing import Optional


class BootScene:
    """
    Minimal boot scene - just display boot_logo, no animations.
    """
    
    def __init__(self, app, duration_s: float = 1.0):
        """Initialize boot scene."""
        self.app = app
        self.duration_s = duration_s  # Quick 1 second
        self.start_time: Optional[float] = None
        self.logo_surface: Optional[pygame.Surface] = None
        
        # Load logo
        self.logo_surface = app.resource_manager.get_image("ui/boot_logo.png")
        
    def on_enter(self) -> None:
        """Called when scene becomes active."""
        self.start_time = time.time()
        if self.app.haptic:
            try:
                self.app.haptic.play_effect(5, 0.1)
            except:
                pass
    
    def update(self, dt: float) -> None:
        """Update boot timer."""
        if self.start_time is None:
            return
        
        elapsed = time.time() - self.start_time
        if elapsed >= self.duration_s:
            try:
                from core.state_machine import AppEvent
                self.app.state_machine.handle_event(AppEvent.BOOT_COMPLETE)
            except:
                pass
    
    def render(self, screen: pygame.Surface) -> None:
        """Render boot logo centered."""
        screen.fill((0, 0, 0))  # Black background
        
        if self.logo_surface:
            # Center logo on screen
            logo_rect = self.logo_surface.get_rect()
            logo_rect.center = (240, 400)  # Center of 480x800
            screen.blit(self.logo_surface, logo_rect)
    
    def on_exit(self) -> None:
        """Called when leaving boot scene."""
        pass