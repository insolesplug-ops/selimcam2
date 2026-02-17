"""Grid overlay and level indicator (spirit level)."""

import pygame
import math


class GridOverlay:
    """
    Renders rule-of-thirds grid and spirit level indicator.
    """
    
    def __init__(self, screen_width: int = 480, screen_height: int = 800):
        """
        Initialize grid overlay.
        
        Args:
            screen_width: Screen width
            screen_height: Screen height
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Colors
        self.grid_color = (255, 255, 255, 80)  # Semi-transparent white
        self.level_color = (255, 255, 255, 200)
        
        print("[GridOverlay] Initialized")
    
    def render_grid(self, surface: pygame.Surface) -> None:
        """
        Render rule-of-thirds grid.
        
        Args:
            surface: Surface to render on
        """
        # Vertical lines
        x1 = self.screen_width // 3
        x2 = 2 * self.screen_width // 3
        
        pygame.draw.line(surface, self.grid_color, (x1, 0), (x1, self.screen_height), 1)
        pygame.draw.line(surface, self.grid_color, (x2, 0), (x2, self.screen_height), 1)
        
        # Horizontal lines
        y1 = self.screen_height // 3
        y2 = 2 * self.screen_height // 3
        
        pygame.draw.line(surface, self.grid_color, (0, y1), (self.screen_width, y1), 1)
        pygame.draw.line(surface, self.grid_color, (0, y2), (self.screen_width, y2), 1)
    
    def render_level(self, surface: pygame.Surface, tilt_angle: float) -> None:
        """
        Render spirit level indicator.
        
        Args:
            surface: Surface to render on
            tilt_angle: Tilt angle in degrees (-90 to +90)
        """
        # Map tilt angle to vertical position
        # -90° (full left) -> bottom
        # 0° (level) -> center
        # +90° (full right) -> top
        
        # Safe range: -45° to +45°
        tilt_angle = max(-45, min(45, tilt_angle))
        
        # Map to pixel range (100px from center in each direction)
        max_offset = 100
        offset = int((tilt_angle / 45.0) * max_offset)
        
        # Center position
        center_y = self.screen_height // 2
        
        # Line position
        line_y = center_y - offset
        
        # Draw horizontal line
        line_length = 60
        center_x = self.screen_width - 20  # Right side
        
        pygame.draw.line(
            surface,
            self.level_color,
            (center_x - line_length // 2, line_y),
            (center_x + line_length // 2, line_y),
            2
        )
        
        # Draw reference markers
        pygame.draw.line(
            surface,
            (255, 255, 255, 120),
            (center_x - line_length // 2 - 5, center_y),
            (center_x + line_length // 2 + 5, center_y),
            1
        )