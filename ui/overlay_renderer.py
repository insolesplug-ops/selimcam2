"""Overlay renderer for top info bar (battery, time, etc.)."""

import pygame
from datetime import datetime
from typing import Optional


class OverlayRenderer:
    """
    Renders top info bar with battery, time, and extended info.
    """
    
    def __init__(self, font_regular, font_bold, screen_width: int = 480):
        """
        Initialize overlay renderer.
        
        Args:
            font_regular: Regular font
            font_bold: Bold font
            screen_width: Screen width in pixels
        """
        self.font_regular = font_regular
        self.font_bold = font_bold
        self.screen_width = screen_width
        
        # Colors
        self.text_color = (200, 200, 200)
        self.bg_color = (30, 30, 30, 180)  # Semi-transparent dark
        
        print("[OverlayRenderer] Initialized")
    
    def render_minimal(self, surface: pygame.Surface, 
                      battery_percent: Optional[int],
                      datetime_str: str) -> None:
        """
        Render minimal info bar (battery + time).
        
        Args:
            surface: Surface to render on
            battery_percent: Battery percentage or None
            datetime_str: Formatted datetime string
        """
        # Background bar
        bar_height = 30
        bg_surf = pygame.Surface((self.screen_width, bar_height), pygame.SRCALPHA)
        bg_surf.fill(self.bg_color)
        surface.blit(bg_surf, (0, 0))
        
        # Battery (left)
        if battery_percent is not None:
            battery_text = f"{battery_percent}%"
        else:
            battery_text = "—%"
        
        battery_surf = self.font_regular.render(battery_text, True, self.text_color)
        surface.blit(battery_surf, (10, 5))
        
        # Time (right)
        time_surf = self.font_regular.render(datetime_str, True, self.text_color)
        time_rect = time_surf.get_rect()
        time_rect.right = self.screen_width - 10
        time_rect.top = 5
        surface.blit(time_surf, time_rect)
    
    def render_extended(self, surface: pygame.Surface,
                       battery_percent: Optional[int],
                       datetime_str: str,
                       lux: Optional[float],
                       zoom: float,
                       filter_name: str,
                       photo_count: int) -> None:
        """
        Render extended info bar with additional data.
        
        Args:
            surface: Surface to render on
            battery_percent: Battery percentage
            datetime_str: Formatted datetime
            lux: Ambient light level
            zoom: Current zoom level
            filter_name: Active filter name
            photo_count: Number of photos stored
        """
        # Background bar (taller)
        bar_height = 50
        bg_surf = pygame.Surface((self.screen_width, bar_height), pygame.SRCALPHA)
        bg_surf.fill(self.bg_color)
        surface.blit(bg_surf, (0, 0))
        
        # Row 1: Battery + Time
        if battery_percent is not None:
            battery_text = f"{battery_percent}%"
        else:
            battery_text = "—%"
        
        battery_surf = self.font_regular.render(battery_text, True, self.text_color)
        surface.blit(battery_surf, (10, 5))
        
        time_surf = self.font_regular.render(datetime_str, True, self.text_color)
        time_rect = time_surf.get_rect()
        time_rect.right = self.screen_width - 10
        time_rect.top = 5
        surface.blit(time_surf, time_rect)
        
        # Row 2: Extended info
        info_parts = []
        
        if lux is not None:
            info_parts.append(f"Lux:{int(lux)}")
        
        info_parts.append(f"Zoom:{zoom:.1f}x")
        
        if filter_name != "none":
            info_parts.append(f"Filter:{filter_name}")
        
        info_parts.append(f"Photos:{photo_count}")
        
        info_text = " | ".join(info_parts)
        info_surf = self.font_regular.render(info_text, True, (180, 180, 180))
        surface.blit(info_surf, (10, 28))