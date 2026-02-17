"""Boot scene with cool animated startup sequence."""

import pygame
import time
import math
from typing import Optional


class BootScene:
    """
    Cool boot animation with animated elements.
    Smooth visual feedback while camera initializes.
    """
    
    def __init__(self, app, duration_s: float = 2.0):
        """
        Initialize boot scene.
        
        Args:
            app: Main application reference
            duration_s: Boot animation duration
        """
        self.app = app
        self.duration_s = duration_s
        
        # Animation state
        self.start_time: Optional[float] = None
        self.logo_surface: Optional[pygame.Surface] = None
        
        # Fonts
        self.font_bold = app.resource_manager.load_font("fonts/inter_bold.ttf", 40)
        self.font_regular = app.resource_manager.load_font("fonts/Inter_regular.ttf", 16)
        
        # Load logo if available
        self.logo_surface = app.resource_manager.get_image("ui/boot_logo.png")
        
        # Animation parameters
        self.pulse_speed = 2.0  # Speed of pulse animation
        self.rotate_speed = 180.0  # Degrees per second
        
    def on_enter(self) -> None:
        """Called when scene becomes active."""
        self.start_time = time.time()
        
        # Play subtle haptic
        if self.app.haptic:
            try:
                self.app.haptic.play_effect(5, 0.2)
            except:
                pass
    
    def update(self, dt: float) -> None:
        """Update animation."""
        if self.start_time is None:
            return
        
        # Check if boot complete
        elapsed = time.time() - self.start_time
        if elapsed >= self.duration_s:
            # Transition to camera
            try:
                from core.state_machine import AppEvent
                self.app.state_machine.handle_event(AppEvent.BOOT_COMPLETE)
            except:
                pass
    
    def render(self, screen: pygame.Surface) -> None:
        """Render cool boot animation."""
        screen_w = self.app.config.get('display', 'width', default=480)
        screen_h = self.app.config.get('display', 'height', default=800)
        
        # Background gradient effect (black to dark blue)
        screen.fill((10, 15, 35))
        
        if self.start_time is None:
            return
        
        elapsed = time.time() - self.start_time
        progress = min(elapsed / self.duration_s, 1.0)  # 0.0 to 1.0
        
        # === ANIMATED LOGO ===
        logo_y = screen_h // 2 - 80
        
        # Pulse effect: grows from small to full size
        logo_scale = 0.3 + (progress * 0.7)  # Scales from 0.3 to 1.0
        
        if self.logo_surface:
            # Scale and blit logo
            scaled_logo = pygame.transform.scale(
                self.logo_surface,
                (int(self.logo_surface.get_width() * logo_scale),
                 int(self.logo_surface.get_height() * logo_scale))
            )
            logo_rect = scaled_logo.get_rect(center=(screen_w // 2, logo_y))
            
            # Fade in effect
            if progress < 0.3:
                alpha = int(255 * (progress / 0.3))
                scaled_logo.set_alpha(alpha)
            
            screen.blit(scaled_logo, logo_rect)
        else:
            # Text fallback with glow effect
            title_text = "SelimCam"
            title_surf = self.font_bold.render(title_text, True, (100, 200, 255))
            
            # Glow background (subtle)
            glow_rect = title_surf.get_rect(center=(screen_w // 2, logo_y))
            glow_rect.inflate_ip(40, 20)
            pygame.draw.rect(screen, (30, 60, 100), glow_rect, border_radius=10)
            
            title_rect = title_surf.get_rect(center=(screen_w // 2, logo_y))
            screen.blit(title_surf, title_rect)
        
        # === ANIMATED DOTS / PROGRESS BAR ===
        bar_y = screen_h // 2 + 60
        bar_width = 100
        bar_height = 4
        bar_x = (screen_w - bar_width) // 2
        
        # Background bar
        pygame.draw.rect(screen, (40, 40, 60), (bar_x, bar_y, bar_width, bar_height), border_radius=2)
        
        # Animated fill
        fill_width = int(bar_width * progress)
        pygame.draw.rect(screen, (100, 200, 255), (bar_x, bar_y, fill_width, bar_height), border_radius=2)
        
        # === STATUS TEXT ===
        status_y = bar_y + 40
        status_text = "Initializing Camera..."
        status_surf = self.font_regular.render(status_text, True, (150, 150, 180))
        status_rect = status_surf.get_rect(center=(screen_w // 2, status_y))
        screen.blit(status_surf, status_rect)
        
        # === ANIMATED ORBITING DOTS ===
        orbit_y = status_y + 50
        orbit_radius = 30
        
        # Rotate based on time
        angle = (elapsed * self.rotate_speed * math.pi / 180) % (2 * math.pi)
        
        for i in range(3):
            # Three dots in orbit
            dot_angle = angle + (i * 2 * math.pi / 3)
            dot_x = screen_w // 2 + math.cos(dot_angle) * orbit_radius
            dot_y = orbit_y + math.sin(dot_angle) * orbit_radius
            
            # Brightness varies with orbit position
            brightness = int(150 + 105 * math.sin(dot_angle))
            color = (brightness // 2, brightness // 1.5, brightness)
            
            pygame.draw.circle(screen, color, (int(dot_x), int(dot_y)), 4)
        
        # === VERSION TEXT ===
        version_text = "v2.0 Production"
        version_surf = self.font_regular.render(version_text, True, (80, 80, 100))
        version_rect = version_surf.get_rect(bottomright=(screen_w - 20, screen_h - 20))
        screen.blit(version_surf, version_rect)
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle input (ignored during boot)."""
        pass
    
    def on_exit(self) -> None:
        """Called when leaving scene."""
        pass