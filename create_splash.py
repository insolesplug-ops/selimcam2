#!/usr/bin/env python3
"""
SelimCam Boot Splash Screen Generator
Creates a minimal PNG for system boot display
No terminal output when run from systemd (ExecStartPre)
"""

import os
import sys

def create_splash_screen():
    """Create a simple PNG splash screen."""
    
    splash_path = "/tmp/selimcam_splash.png"
    
    # Try PIL first (lighter than pygame)
    try:
        from PIL import Image, ImageDraw
        
        WIDTH, HEIGHT = 480, 800
        img = Image.new('RGB', (WIDTH, HEIGHT), color=(10, 15, 35))
        draw = ImageDraw.Draw(img)
        
        # Vertical gradient
        for y in range(HEIGHT):
            intensity = int((y / HEIGHT) * 30)
            color = (10, 15, 35 + intensity)
            draw.line([(0, y), (WIDTH, y)], fill=color)
        
        # Center box
        box_x1, box_y1 = 80, 300
        box_x2, box_y2 = 400, 500
        draw.rectangle([box_x1, box_y1, box_x2, box_y2], 
                      outline=(100, 200, 255), width=3)
        
        # Simple text lines in center
        draw.line([(100, 380), (380, 380)], fill=(100, 200, 255), width=2)
        draw.line([(100, 400), (380, 400)], fill=(100, 200, 255), width=2)
        
        img.save(splash_path)
        return True
        
    except ImportError:
        # Fallback to pygame
        try:
            import pygame
            pygame.init()
            
            WIDTH, HEIGHT = 480, 800
            surface = pygame.Surface((WIDTH, HEIGHT))
            
            # Gradient
            for y in range(HEIGHT):
                intensity = int((y / HEIGHT) * 30)
                pygame.draw.line(surface, (10, 15, 35 + intensity),
                               (0, y), (WIDTH, y))
            
            # Box
            pygame.draw.rect(surface, (100, 200, 255), (80, 300, 320, 200), 3)
            
            pygame.image.save(surface, splash_path)
            pygame.quit()
            return True
            
        except ImportError:
            # No image library - create minimal fallback
            return False

if __name__ == "__main__":
    success = create_splash_screen()
    sys.exit(0 if success else 1)
