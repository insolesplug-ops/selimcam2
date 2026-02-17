"""
Gallery scene for viewing captured photos.
WITH DELETE FUNCTION.
"""

import pygame
from typing import List, Optional
from pathlib import Path
from datetime import datetime


class GalleryScene:
    """Photo gallery with swipe navigation and delete."""
    
    def __init__(self, app):
        """Initialize gallery scene."""
        self.app = app
        
        # Photo store
        from core.photo_store import PhotoStore
        self.photo_store = PhotoStore("photos")
        
        # State
        self.photos: List[Path] = []
        self.current_index = 0
        
        # Surface cache - LIMITED TO 2 IMAGES FOR Pi 3A+ (512MB) COMPATIBILITY
        self.surface_cache = {}
        self.MAX_CACHE_SIZE = 2  # Each photo surface ~1.2 MB
        
        # Gesture detection
        from core.gesture_detector import GestureDetector
        self.gesture_detector = GestureDetector()
        
        # Load hitboxes
        from core.hitbox_loader import HitboxLoader
        self.hitbox_loader = HitboxLoader()
        self.hitbox_loader.load("hitboxes_gallery.json")
        
        # Load gallery overlay PNG
        self.gallery_overlay = app.resource_manager.get_image("ui/gallery.png")
        
        # Fonts with fallback
        try:
            self.font_title = app.resource_manager.load_font("fonts/inter_bold.ttf", 28)
            self.font_info = app.resource_manager.load_font("fonts/Inter_regular.ttf", 20)
        except:
            self.font_title = pygame.font.SysFont("Arial", 28, bold=True)
            self.font_info = pygame.font.SysFont("Arial", 20)
        
        print("[GalleryScene] Initialized")
    
    def on_enter(self):
        """Load photos on enter."""
        self.photos = self.photo_store.list_photos()
        self.current_index = 0
        self.surface_cache.clear()
        
        print(f"[GalleryScene] Loaded {len(self.photos)} photos")
        
        if self.photos:
            self._load_photo_surface(0)
    
    def on_exit(self):
        """Clear cache on exit."""
        self.surface_cache.clear()
    
    def handle_event(self, event: pygame.event.Event):
        """Handle input events."""
        from core.state_machine import AppEvent
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self._prev_photo()
            elif event.key == pygame.K_RIGHT:
                self._next_photo()
            elif event.key == pygame.K_DELETE:
                self._delete_current_photo()
            elif event.key in [pygame.K_ESCAPE, pygame.K_SPACE]:
                self.app.state_machine.handle_event(AppEvent.BACK_TO_CAMERA)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            # Start gesture detection for swipe navigation
            # Back button hitbox is handled by main.py HitboxEngine
            # Delete button hitbox is handled by main.py HitboxEngine
            self.gesture_detector.on_touch_down(mx, my)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            mx, my = event.pos
            
            gesture = self.gesture_detector.on_touch_up(mx, my)
            
            if gesture:
                # FIX: gesture is a GestureType enum, use .name directly
                if gesture.name == 'SWIPE_LEFT':
                    self._next_photo()
                elif gesture.name == 'SWIPE_RIGHT':
                    self._prev_photo()
    
    def _prev_photo(self):
        """Go to previous photo."""
        if not self.photos:
            return
        
        self.current_index = (self.current_index - 1) % len(self.photos)
        self._load_photo_surface(self.current_index)
    
    def _next_photo(self):
        """Go to next photo."""
        if not self.photos:
            return
        
        self.current_index = (self.current_index + 1) % len(self.photos)
        self._load_photo_surface(self.current_index)
    
    def _delete_current_photo(self):
        """Delete current photo."""
        if not self.photos or self.current_index >= len(self.photos):
            return
        
        photo_path = self.photos[self.current_index]
        
        try:
            photo_path.unlink()
            print(f"[Gallery] Deleted: {photo_path.name}")
            
            # Refresh photos list
            self.photos = self.photo_store.list_photos()
            self.surface_cache.clear()
            
            # Adjust index
            if not self.photos:
                self.current_index = 0
            elif self.current_index >= len(self.photos):
                self.current_index = len(self.photos) - 1
            
            # Haptic feedback
            if self.app.haptic and self.app.haptic.available:
                self.app.haptic.play_effect(14, 0.6)
        
        except Exception as e:
            print(f"[Gallery] Delete failed: {e}")
    
    def _load_photo_surface(self, index: int) -> Optional[pygame.Surface]:
        """Load photo as pygame surface (with caching)."""
        if index < 0 or index >= len(self.photos):
            return None
        
        # Check cache
        if index in self.surface_cache:
            return self.surface_cache[index]
        
        # Load from disk
        try:
            photo_path = self.photos[index]
            
            from PIL import Image
            img = Image.open(photo_path)
            
            # Resize to fit screen
            screen_w = self.app.config.get('display', 'width', default=480)
            screen_h = self.app.config.get('display', 'height', default=800)
            
            img.thumbnail((screen_w, screen_h), Image.Resampling.LANCZOS)
            
            # Convert to pygame surface
            mode = img.mode
            size = img.size
            data = img.tobytes()
            
            surf = pygame.image.fromstring(data, size, mode)
            
            # Manage cache size - keep only N recent photos cached (memory efficient for Pi 3A+)
            if len(self.surface_cache) >= self.MAX_CACHE_SIZE:
                # Remove oldest cached photo
                oldest_key = min(self.surface_cache.keys())
                del self.surface_cache[oldest_key]
            
            self.surface_cache[index] = surf
            
            return surf
            
        except Exception as e:
            print(f"[GalleryScene] Load photo failed: {e}")
            return None
    
    def handle_encoder_rotation(self, delta: int):
        """Handle encoder rotation."""
        if delta > 0:
            self._next_photo()
        elif delta < 0:
            self._prev_photo()
    
    def update(self, dt: float):
        """Update scene."""
        pass
    
    def render(self, screen: pygame.Surface):
        """Render gallery with Apple Photos-style dark mode design."""
        # Deep dark background (like iOS dark mode)
        screen.fill((10, 10, 12))
        
        if not self.photos:
            # Empty state - minimal, elegant
            no_photos_surf = self.font_title.render("No Photos", True, (120, 120, 130))
            no_photos_rect = no_photos_surf.get_rect(center=(240, 380))
            screen.blit(no_photos_surf, no_photos_rect)
            
            hint_surf = self.font_info.render("Take your first photo", True, (80, 80, 90))
            hint_rect = hint_surf.get_rect(center=(240, 430))
            screen.blit(hint_surf, hint_rect)
        else:
            # Show current photo - centered with subtle shadows
            surf = self._load_photo_surface(self.current_index)
            
            if surf:
                # Scale photo to fit nicely (leaving space for title and controls)
                max_width = 440
                max_height = 580
                
                scale_x = max_width / surf.get_width()
                scale_y = max_height / surf.get_height()
                scale = min(scale_x, scale_y, 1.0)
                
                new_size = (int(surf.get_width() * scale), int(surf.get_height() * scale))
                scaled_surf = pygame.transform.scale(surf, new_size)
                
                # Center photo with subtle shadow background
                photo_rect = scaled_surf.get_rect(center=(240, 360))
                
                # Draw subtle shadow/border (iOS style)
                shadow_rect = photo_rect.inflate(8, 8)
                pygame.draw.rect(screen, (30, 30, 35), shadow_rect, border_radius=12)
                
                screen.blit(scaled_surf, photo_rect)
            
            # Photo info at top (minimal, elegant)
            self._render_photo_header(screen)
            
            # Alternative gesture hint at bottom
            self._render_gesture_hint(screen)
        
        # Display gallery.png overlay on top (contains UI buttons)
        if self.gallery_overlay:
            screen.blit(self.gallery_overlay, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
    
    def _render_photo_header(self, screen: pygame.Surface):
        """Render header with photo count - iOS style."""
        if not self.photos or self.current_index >= len(self.photos):
            return
        
        # Photo count: Apple-style minimal
        count_str = f"{self.current_index + 1} of {len(self.photos)}"
        count_surf = self.font_info.render(count_str, True, (150, 150, 160))
        count_rect = count_surf.get_rect()
        count_rect.centerx = 240
        count_rect.top = 25
        screen.blit(count_surf, count_rect)
        
        # Optional: date of current photo
        try:
            photo_path = self.photos[self.current_index]
            mtime = photo_path.stat().st_mtime
            from datetime import datetime
            date_str = datetime.fromtimestamp(mtime).strftime("%b %d, %Y")
            date_surf = self.font_info.render(date_str, True, (100, 100, 110))
            date_rect = date_surf.get_rect()
            date_rect.centerx = 240
            date_rect.top = 47
            screen.blit(date_surf, date_rect)
        except:
            pass
    
    def _render_gesture_hint(self, screen: pygame.Surface):
        """Render subtle gesture hint - iOS notification style."""
        hint_text = "← Swipe →  to navigate"
        hint_surf = self.font_info.render(hint_text, True, (80, 80, 95))
        hint_surf.set_alpha(180)
        hint_rect = hint_surf.get_rect()
        hint_rect.centerx = 240
        hint_rect.bottom = 710
        screen.blit(hint_surf, hint_rect)
    
    def _render_info_overlay(self, screen: pygame.Surface):
        """Render photo info overlay."""
        if not self.photos or self.current_index >= len(self.photos):
            return
        
        photo_path = self.photos[self.current_index]
        
        # Get timestamp
        try:
            mtime = photo_path.stat().st_mtime
            dt = datetime.fromtimestamp(mtime)
            date_str = dt.strftime("%Y-%m-%d %H:%M")
        except:
            date_str = "Unknown"
        
        # Index
        index_str = f"{self.current_index + 1}/{len(self.photos)}"
        
        # Background
        bg_rect = pygame.Rect(10, 10, 300, 60)
        bg_surf = pygame.Surface((300, 60))
        bg_surf.set_alpha(180)
        bg_surf.fill((20, 20, 20))
        screen.blit(bg_surf, (10, 10))
        
        # Text
        date_surf = self.font_info.render(date_str, True, (255, 255, 255))
        screen.blit(date_surf, (20, 20))
        
        index_surf = self.font_info.render(index_str, True, (200, 200, 200))
        screen.blit(index_surf, (20, 45))
    
    def _render_controls(self, screen: pygame.Surface):
        """Render bottom controls."""
        # Semi-transparent bar
        bar_surf = pygame.Surface((480, 70))
        bar_surf.set_alpha(180)
        bar_surf.fill((20, 20, 20))
        screen.blit(bar_surf, (0, 730))
        
        # Back button + action buttons handled by hitboxes (no text labels)