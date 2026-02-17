"""
Main camera scene with live preview, zoom, filters, and capture.
"""

import pygame
import numpy as np
import time
from typing import Optional
from filters.filter_engine import FilterEngine, FilterType
from core.logger import logger


class CameraScene:
    """
    Main camera viewfinder scene.
    """
    
    def __init__(self, app):
        """Initialize camera scene."""
        self.app = app
        
        # Filter engine
        self.filter_engine = FilterEngine()
        
        # Photo store
        from core.photo_store import PhotoStore
        self.photo_store = PhotoStore("photos")
        
        # Zoom state
        self.zoom_target = 1.0
        self.zoom_current = 1.0
        self.zoom_min = app.config.get('zoom', 'min', default=1.0)
        self.zoom_max = app.config.get('zoom', 'max', default=2.5)
        self.zoom_step = app.config.get('zoom', 'step', default=0.05)
        self.zoom_smooth = app.config.get('zoom', 'smooth_factor', default=0.25)
        
        # Load hitboxes
        from core.hitbox_loader import HitboxLoader
        self.hitbox_loader = HitboxLoader()
        self.hitbox_loader.load("hitboxes_main.json")
        
        # UI overlays (PNGs loaded by resource manager)
        self.flash_overlays = {
            'off': app.resource_manager.get_image("ui/flash off.png"),
            'on': app.resource_manager.get_image("ui/flash on.png"),
            'auto': app.resource_manager.get_image("ui/flash automatically.png")
        }
        
        # Icons
        self.settings_icon = app.resource_manager.get_image("ui/settings.png")
        self.gallery_icon = app.resource_manager.get_image("ui/gallery.png")
        
        # Performance tracking
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()
        
        # Fonts with fallback
        try:
            self.font_regular = app.resource_manager.load_font("fonts/Inter_regular.ttf", 20)
            self.font_bold = app.resource_manager.load_font("fonts/inter_bold.ttf", 24)
        except:
            self.font_regular = pygame.font.SysFont("Arial", 20)
            self.font_bold = pygame.font.SysFont("Arial", 24, bold=True)
        
        logger.info("[CameraScene] Initialized")
    
    def on_enter(self):
        """Start camera preview."""
        if self.app.camera:
            self.app.camera.start_preview()
        
        self.zoom_current = self.app.config.get('zoom', 'current', default=1.0)
        self.zoom_target = self.zoom_current
    
    def on_exit(self):
        """Stop camera preview."""
        self.app.config.set('zoom', 'current', value=self.zoom_current, save=True)
    
    def handle_event(self, event: pygame.event.Event):
        """Handle input events."""
        from core.state_machine import AppEvent
        
        self.app.power_manager.update_activity()
        
        if event.type == pygame.KEYDOWN:
            # Keyboard shortcuts
            if event.key == pygame.K_s:
                self._capture_photo()
            elif event.key == pygame.K_g:
                self._toggle_grid()
            elif event.key == pygame.K_l:
                self._toggle_level()
            elif event.key == pygame.K_f:
                self._cycle_flash_mode()
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            # Check hitboxes
            hit_id = self.hitbox_loader.check_hit("hitboxes_main.json", mx, my)
            
            if hit_id == 'settings':
                logger.info("Opening Settings")
                self.app.state_machine.handle_event(AppEvent.OPEN_SETTINGS)
                if self.app.haptic and self.app.haptic.available:
                    self.app.haptic.play_effect(10, 0.5)
            
            elif hit_id == 'gallery':
                logger.info("Opening Gallery")
                self.app.state_machine.handle_event(AppEvent.OPEN_GALLERY)
                if self.app.haptic and self.app.haptic.available:
                    self.app.haptic.play_effect(10, 0.5)
            
            elif hit_id == 'flash':
                self._cycle_flash_mode()
                if self.app.haptic and self.app.haptic.available:
                    self.app.haptic.play_effect(10, 0.6)
    
    def _cycle_flash_mode(self):
        """Cycle flash mode: off -> on -> auto -> off."""
        current_mode = self.app.config.get('flash', 'mode', default='off')
        mode_cycle = {'off': 'on', 'on': 'auto', 'auto': 'off'}
        new_mode = mode_cycle[current_mode]
        self.app.config.set('flash', 'mode', value=new_mode, save=True)
        logger.info(f"Flash: {current_mode} -> {new_mode}")
    
    def _toggle_grid(self):
        """Toggle grid overlay."""
        current = self.app.config.get('ui', 'grid_enabled', default=False)
        self.app.config.set('ui', 'grid_enabled', value=not current, save=True)
        logger.info(f"Grid: {not current}")
    
    def _toggle_level(self):
        """Toggle level indicator."""
        current = self.app.config.get('ui', 'level_enabled', default=False)
        self.app.config.set('ui', 'level_enabled', value=not current, save=True)
        logger.info(f"Level: {not current}")
    
    def _capture_photo(self):
        """Capture photo with filter/ISO and freeze frame."""
        logger.info("Capture triggered")
        
        # Determine flash
        flash_mode = self.app.config.get('flash', 'mode', default='off')
        use_flash = False
        
        if flash_mode == 'on':
            use_flash = True
        elif flash_mode == 'auto':
            lux = self.app.sensor_thread.get_lux() if hasattr(self.app, 'sensor_thread') else None
            if lux is None and self.app.light_sensor:
                lux = self.app.light_sensor.read_lux()
            
            threshold = self.app.config.get('flash', 'auto_threshold_lux', default=60)
            
            if lux is not None and lux < threshold:
                use_flash = True
                logger.info(f"Auto-flash ON (lux={lux:.1f} < {threshold})")
        
        # Flash on
        if use_flash and self.app.flash_led:
            self.app.flash_led.on()
            time.sleep(0.05)
        
        # Capture frame
        if not self.app.camera:
            logger.error("No camera available")
            if use_flash and self.app.flash_led:
                self.app.flash_led.off()
            return
        
        raw_frame = self.app.camera.capture_array()
        
        if raw_frame is None:
            logger.error("Capture failed - no frame")
            if use_flash and self.app.flash_led:
                self.app.flash_led.off()
            if self.app.haptic and self.app.haptic.available:
                self.app.haptic.play_effect(14, 0.8)
            return
        
        # Flash off
        if use_flash and self.app.flash_led:
            time.sleep(0.05)
            self.app.flash_led.off()
        
        # Apply filter + ISO
        filter_type_str = self.app.config.get('filter', 'active', default='none')
        iso_value = self.app.config.get('filter', 'iso_fake', default=400)
        
        filter_type = FilterType(filter_type_str)
        processed_frame = self.filter_engine.process_frame(raw_frame, filter_type, iso_value)
        
        # Save to photo store
        filepath = self.photo_store.save_photo(processed_frame, extension='jpg')
        
        if filepath:
            logger.info(f"Saved (filter={filter_type_str}, ISO={iso_value}): {filepath.name}")
            
            # Haptic feedback
            if self.app.haptic and self.app.haptic.available:
                self.app.haptic.play_effect(47, 0.8)
            
            # Trigger freeze frame
            screen_w = self.app.config.get('display', 'width', default=480)
            screen_h = self.app.config.get('display', 'height', default=800)
            self.app.freeze_frame.trigger(processed_frame, (screen_w, screen_h))
            
            # Enforce limit
            max_photos = self.app.config.get('storage', 'max_photos', default=500)
            self.photo_store.delete_oldest(keep=max_photos)
        else:
            logger.error("Save failed")
            if self.app.haptic and self.app.haptic.available:
                self.app.haptic.play_effect(14, 0.8)
    
    def handle_encoder_rotation(self, delta: int):
        """Handle encoder rotation for zoom."""
        self.zoom_target += delta * self.zoom_step
        self.zoom_target = max(self.zoom_min, min(self.zoom_max, self.zoom_target))
        
        if delta != 0 and self.app.haptic and self.app.haptic.available:
            self.app.haptic.play_effect(1, 0.3)
    
    def update(self, dt: float):
        """Update scene logic."""
        # Smooth zoom
        if abs(self.zoom_target - self.zoom_current) > 0.001:
            self.zoom_current += (self.zoom_target - self.zoom_current) * self.zoom_smooth
        
        # Update freeze frame
        self.app.freeze_frame.update()
        
        # FPS tracking
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_fps_time = current_time
    
    def render(self, screen: pygame.Surface):
        """Render camera preview and UI overlays."""
        
        # If freeze frame active, show it
        if self.app.freeze_frame.is_active:
            self.app.freeze_frame.render(screen)
            return
        
        # Get preview frame
        frame = None
        if self.app.camera:
            frame = self.app.camera.get_preview_frame()
        
        if frame is not None:
            # Apply filter
            filter_type_str = self.app.config.get('filter', 'active', default='none')
            filter_type = FilterType(filter_type_str)
            iso_value = self.app.config.get('filter', 'iso_fake', default=400)
            
            filtered_frame = self.filter_engine.process_frame(frame, filter_type, iso_value)
            
            # Apply zoom
            zoomed_frame = self._apply_zoom(filtered_frame)
            
            # Convert to pygame surface
            surf = self._frame_to_surface(zoomed_frame)
            
            if surf:
                screen.blit(surf, (0, 0))
            else:
                screen.fill((20, 20, 20))
                self._render_error(screen, "Frame conversion failed")
        else:
            # No frame - show placeholder
            screen.fill((30, 30, 30))
            self._render_placeholder(screen)
        
        # Grid overlay
        if self.app.config.get('ui', 'grid_enabled', default=False):
            self.app.grid_overlay.render_grid(screen)
        
        # Level overlay
        if self.app.config.get('ui', 'level_enabled', default=False):
            tilt = self.app.sensor_thread.get_tilt() if hasattr(self.app, 'sensor_thread') else 0.0
            self.app.grid_overlay.render_level(screen, tilt)
        
        # Top info bar (optional debug info) - render BEFORE overlay so overlay can cover it
        info_mode = self.app.config.get('ui', 'info_display', default='minimal')
        if info_mode != 'off':
            self._render_info_bar(screen, info_mode)
        
        # Flash mode overlay - ALWAYS display (even in 'off' mode)
        # The overlay PNG contains the full UI with buttons and flash indicator
        # This MUST be rendered last so it appears on top of all other elements
        flash_mode = self.app.config.get('flash', 'mode', default='off')
        flash_overlay = self.flash_overlays.get(flash_mode)
        if flash_overlay:
            # Scale overlay to match screen dimensions if needed
            screen_w = self.app.config.get('display', 'width', default=480)
            screen_h = self.app.config.get('display', 'height', default=800)
            
            overlay_size = flash_overlay.get_size()
            if overlay_size != (screen_w, screen_h):
                flash_overlay = pygame.transform.scale(flash_overlay, (screen_w, screen_h))
            
            screen.blit(flash_overlay, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        
        # FPS debug
        if self.fps > 0:
            fps_surf = self.font_regular.render(f"{self.fps} FPS", True, (0, 255, 0))
            screen.blit(fps_surf, (10, 40))
    
    def _render_placeholder(self, screen: pygame.Surface):
        """Render 'No Camera' placeholder."""
        # Large centered text
        no_cam_surf = self.font_bold.render("NO CAMERA", True, (150, 150, 150))
        no_cam_rect = no_cam_surf.get_rect(center=(240, 400))
        screen.blit(no_cam_surf, no_cam_rect)
        
        # Smaller hint
        hint_surf = self.font_regular.render("Using simulator mode", True, (100, 100, 100))
        hint_rect = hint_surf.get_rect(center=(240, 450))
        screen.blit(hint_surf, hint_rect)
    
    def _render_error(self, screen: pygame.Surface, msg: str):
        """Render error message."""
        error_surf = self.font_regular.render(f"ERROR: {msg}", True, (255, 100, 100))
        error_rect = error_surf.get_rect(center=(240, 400))
        screen.blit(error_surf, error_rect)
    
    def _render_bottom_bar(self, screen: pygame.Surface):
        """Render PNG overlays only - no text labels.
        
        Shows the current flash mode overlay which contains all UI elements.
        """
        # Flash mode overlay already rendered in main render()
        # This method is kept for compatibility but the overlay
        # is now displayed directly in the render() method to ensure
        # it appears on top of all other content
        pass
    
    def _apply_zoom(self, frame: np.ndarray) -> np.ndarray:
        """Apply zoom by cropping center."""
        if self.zoom_current <= 1.01:
            return frame
        
        h, w = frame.shape[:2]
        
        crop_w = int(w / self.zoom_current)
        crop_h = int(h / self.zoom_current)
        
        x1 = (w - crop_w) // 2
        y1 = (h - crop_h) // 2
        x2 = x1 + crop_w
        y2 = y1 + crop_h
        
        return frame[y1:y2, x1:x2]
    
    def _frame_to_surface(self, frame: np.ndarray) -> Optional[pygame.Surface]:
        """Convert numpy frame to pygame surface."""
        try:
            screen_w = self.app.config.get('display', 'width', default=480)
            screen_h = self.app.config.get('display', 'height', default=800)
            
            surf = pygame.surfarray.make_surface(np.swapaxes(frame, 0, 1))
            surf = pygame.transform.scale(surf, (screen_w, screen_h))
            
            return surf
        except Exception as e:
            logger.error(f"Frame conversion failed: {e}")
            return None
    
    def _render_info_bar(self, screen: pygame.Surface, mode: str):
        """Render top info bar."""
        if mode == 'off':
            return
        
        from datetime import datetime
        
        battery_pct = self.app.sensor_thread.get_battery() if hasattr(self.app, 'sensor_thread') else None
        if battery_pct is None and self.app.battery:
            battery_pct = self.app.battery.read_percentage()
        
        datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if mode == 'minimal':
            self.app.overlay_renderer.render_minimal(screen, battery_pct, datetime_str)
        
        elif mode == 'extended':
            lux = self.app.sensor_thread.get_lux() if hasattr(self.app, 'sensor_thread') else None
            if lux is None and self.app.light_sensor:
                lux = self.app.light_sensor.read_lux()
            
            filter_name = self.app.config.get('filter', 'active', default='none')
            photo_count = self.photo_store.get_photo_count()
            
            self.app.overlay_renderer.render_extended(
                screen, battery_pct, datetime_str,
                lux, self.zoom_current, filter_name, photo_count
            )