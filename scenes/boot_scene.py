"""Boot scene - minimal, just show boot_logo with premium touch."""

import pygame
import time
from typing import Optional


class BootScene:
    """
    Boot scene - displays centered logo for quick startup with skip-on-tap.
    Fade in/out transitions for premium feel.
    """
    
    def __init__(self, app, duration_s: float = 1.5):
        """Initialize boot scene."""
        self.app = app
        self.duration_s = duration_s  # 1.5 seconds total
        self.start_time: Optional[float] = None
        self.logo_surface: Optional[pygame.Surface] = None
        self.fade_alpha = 0  # Start transparent, fade in
        self.can_skip = False  # Only allow skip after 300ms
        
        # Load logo with error handling
        try:
            self.logo_surface = app.resource_manager.get_image("ui/boot_logo.png")
        except Exception as e:
            print(f"[BootScene] Failed to load boot_logo: {e}")
            self.logo_surface = None
        
    def on_enter(self) -> None:
        """Called when scene becomes active."""
        self.start_time = time.time()
        self.fade_alpha = 0
        self.can_skip = False
        
        # Play haptic on boot start
        if self.app.haptic:
            try:
                self.app.haptic.play_effect(5, 0.1)
            except:
                pass
    
    def update(self, dt: float) -> None:
        """Update boot timer and fade transitions."""
        if self.start_time is None:
            return
        
        elapsed = time.time() - self.start_time
        
        # Fade in for first 0.3s
        if elapsed < 0.3:
            self.fade_alpha = int((elapsed / 0.3) * 255)
            self.can_skip = False
        # Hold for middle portion
        elif elapsed < self.duration_s - 0.3:
            self.fade_alpha = 255
            self.can_skip = True
        # Fade out for last 0.3s
        elif elapsed < self.duration_s:
            progress = (elapsed - (self.duration_s - 0.3)) / 0.3
            self.fade_alpha = int((1.0 - progress) * 255)
        # Transition complete
        else:
            try:
                from core.state_machine import AppEvent
                self.app.state_machine.handle_event(AppEvent.BOOT_COMPLETE)
            except Exception as e:
                print(f"[BootScene] Transition error: {e}")
    
    def render(self, screen: pygame.Surface) -> None:
        """Render boot logo centered with fade effect."""
        screen.fill((0, 0, 0))  # Black background
        
        if self.logo_surface:
            # Apply alpha for fade effect
            logo = self.logo_surface.copy()
            logo.set_alpha(self.fade_alpha)
            
            # Center logo
            logo_rect = logo.get_rect()
            logo_rect.center = (240, 400)  # Center of 480x800
            screen.blit(logo, logo_rect)
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle input events. Boot scene can be skipped on tap."""
        from core.state_machine import AppEvent
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Skip boot screen on touch
            if self.start_time is not None:
                elapsed = time.time() - self.start_time
                if elapsed > 0.3:  # Ignore initial touches
                    try:
                        self.app.state_machine.handle_event(AppEvent.BOOT_COMPLETE)
                    except:
                        pass
    
    def on_exit(self) -> None:
        """Called when leaving boot scene."""
        pass