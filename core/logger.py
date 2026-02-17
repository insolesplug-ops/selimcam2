"""
Centralized logging with lazy initialization.
"""

import pygame
import sys
import traceback
from typing import List, Tuple
from datetime import datetime
import os


class Logger:
    """
    Centralized logger with UI overlay.
    Lazy font initialization to avoid pygame.font before pygame.init().
    """
    
    def __init__(self):
        self.messages: List[Tuple[str, str, float]] = []
        self.max_messages = 100
        self.ui_messages: List[Tuple[str, str, float]] = []
        self.ui_duration = 3.0
        
        # Quiet mode for Pi boot (no console spam)
        self.quiet_mode = os.getenv('SELIMCAM_QUIET', 'false').lower() == 'true'
        
        # Font will be initialized lazily
        self._font = None
    
    @property
    def font(self):
        """Lazy font initialization."""
        if self._font is None:
            try:
                self._font = pygame.font.SysFont("Arial", 16)
            except:
                try:
                    self._font = pygame.font.Font(None, 16)
                except:
                    # If even this fails, create dummy font
                    self._font = None
        return self._font
    
    def debug(self, msg: str):
        """Log debug message."""
        self._log("DEBUG", msg, show_console=True)
    
    def info(self, msg: str):
        """Log info message."""
        self._log("INFO", msg, show_console=False)
    
    def warning(self, msg: str):
        """Log warning message."""
        self._log("WARNING", msg, show_console=True)
        self._add_ui_message("WARNING", msg)
    
    def error(self, msg: str):
        """Log error message."""
        self._log("ERROR", msg, show_console=True)
        self._add_ui_message("ERROR", msg)
    
    def critical(self, msg: str):
        """Log critical message."""
        self._log("CRITICAL", msg, show_console=True)
        self._add_ui_message("CRITICAL", msg)
    
    def _log(self, level: str, msg: str, show_console: bool = True):
        """Internal log function."""
        timestamp = datetime.now().timestamp()
        self.messages.append((level, msg, timestamp))
        
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
        
        # Only print important messages or if not in quiet mode
        if not self.quiet_mode or level in ['ERROR', 'CRITICAL', 'WARNING']:
            if show_console:
                time_str = datetime.now().strftime("%H:%M:%S")
                print(f"[{time_str}] [{level}] {msg}")
    
    def _add_ui_message(self, level: str, msg: str):
        """Add message to UI overlay."""
        timestamp = datetime.now().timestamp()
        self.ui_messages.append((level, msg, timestamp))
    
    def render_ui(self, screen: pygame.Surface):
        """Render error messages on screen."""
        if not self.font:
            return  # Font not available, skip UI rendering
        
        current_time = datetime.now().timestamp()
        
        # Remove expired messages
        self.ui_messages = [
            (level, msg, ts) for level, msg, ts in self.ui_messages
            if current_time - ts < self.ui_duration
        ]
        
        if not self.ui_messages:
            return
        
        # Render messages
        y = 100
        for level, msg, ts in self.ui_messages[-5:]:
            color = (200, 50, 50) if level in ["ERROR", "CRITICAL"] else (200, 150, 50)
            
            try:
                text_surf = self.font.render(f"{level}: {msg[:60]}", True, (255, 255, 255))
                
                bg_rect = text_surf.get_rect()
                bg_rect.topleft = (10, y)
                bg_rect.width += 20
                bg_rect.height += 10
                
                bg_surf = pygame.Surface((bg_rect.width, bg_rect.height))
                bg_surf.set_alpha(180)
                bg_surf.fill(color)
                
                screen.blit(bg_surf, (10, y))
                pygame.draw.rect(screen, (255, 255, 255), bg_rect, 2)
                screen.blit(text_surf, (20, y + 5))
                
                y += bg_rect.height + 5
            except:
                pass  # Skip if rendering fails


# Global logger instance
logger = Logger()


def log_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler."""
    if exc_type is KeyboardInterrupt:
        return
    
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    tb_text = "".join(tb_lines)
    
    logger.critical(f"Unhandled exception: {exc_value}")
    print("\n" + "="*70)
    print(" UNHANDLED EXCEPTION")
    print("="*70)
    print(tb_text)
    print("="*70)


# Install global exception handler
sys.excepthook = log_exception