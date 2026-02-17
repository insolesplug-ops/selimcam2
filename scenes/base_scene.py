"""Base scene class for all scenes - provides common interface and error handling."""

import pygame
from abc import ABC, abstractmethod
from typing import Optional


class BaseScene(ABC):
    """Abstract base class for all scenes - ensures consistent interface."""
    
    def __init__(self, app, name: str = "UnnamedScene"):
        """Initialize scene with common setup."""
        self.app = app
        self.name = name
        self.active = False
        self.alpha = 255  # For fade transitions
        self.transition_progress = 0.0
    
    @abstractmethod
    def on_enter(self) -> None:
        """Called when scene becomes active. Override in subclass."""
        self.active = True
        
    @abstractmethod
    def on_exit(self) -> None:
        """Called when scene is deactivated. Override in subclass."""
        self.active = False
        
    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle pygame event. Override in subclass."""
        pass
        
    @abstractmethod
    def update(self, dt: float) -> None:
        """Update scene state. dt in seconds."""
        pass
        
    @abstractmethod
    def render(self, screen: pygame.Surface) -> None:
        """Render scene to screen."""
        pass
    
    # Safe fallback methods
    def safe_on_enter(self) -> None:
        """Safely call on_enter with error handling."""
        try:
            self.on_enter()
        except Exception as e:
            print(f"[{self.name}] on_enter error: {e}")
    
    def safe_on_exit(self) -> None:
        """Safely call on_exit with error handling."""
        try:
            self.on_exit()
        except Exception as e:
            print(f"[{self.name}] on_exit error: {e}")
    
    def safe_handle_event(self, event: pygame.event.Event) -> None:
        """Safely call handle_event with error handling."""
        try:
            self.handle_event(event)
        except Exception as e:
            print(f"[{self.name}] handle_event error: {e}")
    
    def safe_update(self, dt: float) -> None:
        """Safely call update with error handling."""
        try:
            self.update(dt)
        except Exception as e:
            print(f"[{self.name}] update error: {e}")
    
    def safe_render(self, screen: pygame.Surface) -> None:
        """Safely call render with error handling."""
        try:
            self.render(screen)
        except Exception as e:
            print(f"[{self.name}] render error: {e}")
    
    def fade_in(self, duration: float = 0.5) -> float:
        """Smooth fade in transition."""
        self.transition_progress = min(1.0, self.transition_progress + 1.0 / (60 * duration))
        self.alpha = int(255 * self.transition_progress)
        return self.transition_progress
    
    def fade_out(self, duration: float = 0.5) -> float:
        """Smooth fade out transition."""
        self.transition_progress = max(0.0, self.transition_progress - 1.0 / (60 * duration))
        self.alpha = int(255 * self.transition_progress)
        return self.transition_progress
    
    def reset_transition(self) -> None:
        """Reset transition state."""
        self.transition_progress = 0.0
        self.alpha = 255
