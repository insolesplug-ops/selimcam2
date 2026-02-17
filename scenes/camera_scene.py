"""
Main camera scene with live preview, zoom, filters, and capture.
"""

import pygame
import numpy as np
import time
import os
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
        self._debug_frame_logs = bool(app.config.get('ui', 'debug_frame_logs', default=False))
        self._last_no_frame_log = 0.0
        
        # Fonts with fallback
        try:
            self.font_regular = app.resource_manager.load_font("fonts/Inter_regular.ttf", 20)
            self.font_bold = app.resource_manager.load_font("fonts/inter_bold.ttf", 24)
        except:
            self.font_regular = pygame.font.SysFont("Arial", 20)
            self.font_bold = pygame.font.SysFont("Arial", 24, bold=True)
        
        # Auto-rotation test mode (cycles every 10 seconds)
        self.rotation_test_timer = 0.0
        self.rotation_test_auto_cycle = False  # DISABLED - Mode 0 is correct with new +90° architecture
        
        logger.info("[CameraScene] Initialized")
    
    def on_enter(self):
        """Start camera preview."""
        if self.app.camera:
            self.app.camera.start_preview()
        
        self.zoom_current = self.app.config.get('zoom', 'current', default=1.0)
        self.zoom_target = self.zoom_current
    
    def on_exit(self):
        """Stop camera preview."""
        if self.app.camera:
            self.app.camera.stop_preview()
    
    def handle_event(self, event: pygame.event.Event):
        """Handle input events."""
        from core.state_machine import AppEvent
        
        self.app.power_manager.update_activity()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            # Check hitboxes
            hit_id = self.hitbox_loader.check_hit("hitboxes_main.json", mx, my)
            
            if hit_id == 'settings':
                logger.info("Opening Settings")
                self.app.state_machine.handle_event(AppEvent.OPEN_SETTINGS)
                if self.app.haptic and self.app.haptic.available:
                    self.app.haptic.tap()
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
            screen_w, screen_h = self.app.logical_surface.get_size()
            
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
        # AUTO-ROTATION TEST MODE: cycle every 10 seconds
        if self.rotation_test_auto_cycle:
            self.rotation_test_timer += dt
            if self.rotation_test_timer >= 10.0:
                current_mode = self.app.config.get('camera', 'rotation_test', default=0)
                next_mode = (current_mode + 1) % 4
                self.app.config.set('camera', 'rotation_test', value=next_mode)
                logger.info(f"[AUTO-TEST] Rotation mode: {current_mode} → {next_mode}")
                self.rotation_test_timer = 0.0
        
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
        preview_surface = None
        frame = None
        if self.app.camera:
            if hasattr(self.app.camera, "get_preview_surface"):
                preview_surface = self.app.camera.get_preview_surface()
            frame = self.app.camera.get_preview_frame()
            if self._debug_frame_logs:
                logger.debug(f"[RENDER] Camera preview: surface={preview_surface is not None}, frame={frame is not None}")
        else:
            logger.error("[RENDER] ✗ Camera not initialized!")

        if preview_surface is not None:
            if self._debug_frame_logs:
                logger.debug(f"[RENDER] Using preview_surface: {preview_surface.get_size()}")
            screen_w = self.app.config.get('display', 'width', default=480)
            screen_h = self.app.config.get('display', 'height', default=800)
            if preview_surface.get_size() != (screen_w, screen_h):
                preview_surface = pygame.transform.scale(preview_surface, (screen_w, screen_h))
            screen.blit(preview_surface, (0, 0))
        elif frame is not None:
            if self._debug_frame_logs:
                logger.debug(f"[RENDER] Converting numpy frame: {frame.shape}")
            filter_type_str = self.app.config.get('filter', 'active', default='none')
            filter_type = FilterType(filter_type_str)
            iso_value = self.app.config.get('filter', 'iso_fake', default=400)

            filtered_frame = self.filter_engine.process_frame(frame, filter_type, iso_value)
            zoomed_frame = self._apply_zoom(filtered_frame)
            surf = self._frame_to_surface(zoomed_frame)

            if surf:
                screen.blit(surf, (0, 0))
            else:
                logger.error("[RENDER] ✗ Frame conversion failed!")
                screen.fill((255, 0, 0))
                self._render_error(screen, "Frame→Surface error")
        else:
            now = time.time()
            if now - self._last_no_frame_log >= 1.0:
                logger.error("[RENDER] ✗ NO CAMERA FRAMES!")
                self._last_no_frame_log = now
            screen.fill((255, 100, 100))
            try:
                text_surf = self.font_bold.render("CAMERA ERROR", True, (255, 255, 255))
                screen.blit(text_surf, (100, 350))
            except:
                pass
        
        # Grid overlay
        if self.app.config.get('ui', 'grid_enabled', default=False):
            self.app.grid_overlay.render_grid(screen)
        
        # Level overlay
        if self.app.config.get('ui', 'level_enabled', default=False):
            tilt = self.app.sensor_thread.get_tilt() if hasattr(self.app, 'sensor_thread') else 0.0
            self.app.grid_overlay.render_level(screen, tilt)
        
        # ROTATION MODE INDICATOR + AUTO-TEST COUNTDOWN (bottom-left corner, white text)
        rotation_mode = self.app.config.get('camera', 'rotation_test', default=0)
        if self.rotation_test_auto_cycle:
            remaining_time = max(0, 10.0 - self.rotation_test_timer)
            mode_text = f"ROTATION: {rotation_mode} (auto in {remaining_time:.1f}s)"
        else:
            mode_text = f"ROTATION: {rotation_mode} (manual)"
        mode_surf = self.font_regular.render(mode_text, True, (255, 255, 255))
        screen.blit(mode_surf, (10, 760))  # Bottom-left, 30px from bottom
        
        # Top info bar (optional debug info) - render BEFORE overlay so overlay can cover it
        info_mode = self.app.config.get('ui', 'info_display', default='minimal')
        if info_mode != 'off':
            self._render_info_bar(screen, info_mode)
        
        # Optional flash overlay. Disabled by default because some placeholder PNGs
        # can cover the camera image with opaque white regions.
        if self.app.config.get('ui', 'flash_overlay_enabled', default=False):
            flash_mode = self.app.config.get('flash', 'mode', default='off')
            flash_overlay = self.flash_overlays.get(flash_mode)
            if flash_overlay:
                screen_w = self.app.config.get('display', 'width', default=480)
                screen_h = self.app.config.get('display', 'height', default=800)

                overlay_size = flash_overlay.get_size()
                if overlay_size != (screen_w, screen_h):
                    flash_overlay = pygame.transform.scale(flash_overlay, (screen_w, screen_h))

                screen.blit(flash_overlay, (0, 0))
        
        # FPS debug
        if self.fps > 0:
            fps_surf = self.font_regular.render(f"{self.fps} FPS", True, (0, 255, 0))
            screen.blit(fps_surf, (10, 40))
        
        # UI BUTTONS OVERLAY (Settings, Gallery, Flash)
        self._render_ui_buttons(screen)
    
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
        """Convert numpy frame to portrait preview surface (FULL 480x800 screen).

        Rotation modes (without additional 180° flip):
        - Mode 0: 90° CW only
        - Mode 1: No rotation (native landscape as-is)
        - Mode 2: 90° CCW only
        - Mode 3: 180° only
        """
        try:
            preview_w, preview_h = 480, 800

            # READ FROM CONFIG (NOT HARDCODED)
            rotation_mode = self.app.config.get('camera', 'rotation_test', default=0)

            if self._debug_frame_logs:
                logger.debug(f"[FRAME] Input: {frame.shape} | Rotation mode: {rotation_mode}")

            base = pygame.surfarray.make_surface(np.swapaxes(frame, 0, 1))

            if rotation_mode == 0:
                oriented = pygame.transform.rotate(base, -90)
                if self._debug_frame_logs:
                    logger.debug(f"[FRAME] Mode 0: 90° CW → {oriented.get_size()}")
            elif rotation_mode == 1:
                oriented = base
                if self._debug_frame_logs:
                    logger.debug(f"[FRAME] Mode 1: no rotation → {oriented.get_size()}")
            elif rotation_mode == 2:
                oriented = pygame.transform.rotate(base, 90)
                if self._debug_frame_logs:
                    logger.debug(f"[FRAME] Mode 2: 90° CCW → {oriented.get_size()}")
            else:
                oriented = pygame.transform.rotate(base, 180)
                if self._debug_frame_logs:
                    logger.debug(f"[FRAME] Mode 3: 180° → {oriented.get_size()}")

            # NO ADDITIONAL 180° FLIP - each mode is self-contained

            # Aspect-preserving scale into preview area 480x800 WITHOUT CROPPING (contain mode)
            src_w, src_h = oriented.get_size()
            scale = min(preview_w / src_w, preview_h / src_h)  # CONTAIN (not COVER)
            scaled_w = max(1, int(round(src_w * scale)))
            scaled_h = max(1, int(round(src_h * scale)))
            scaled = pygame.transform.scale(oriented, (scaled_w, scaled_h))

            # Center on final preview surface (480x800) with black bars if needed
            final = pygame.Surface((preview_w, preview_h))
            final.fill((0, 0, 0))  # Black background for pillarbox/letterbox
            
            # Center the scaled image
            x = (preview_w - scaled_w) // 2
            y = (preview_h - scaled_h) // 2
            final.blit(scaled, (x, y))

            if self._debug_frame_logs:
                logger.debug(f"[FRAME] Cover scale {src_w}x{src_h} -> {scaled_w}x{scaled_h}, crop ({x},{y}) -> {preview_w}x{preview_h}")
            return final
        except Exception as e:
            logger.error(f"[FRAME] ✗ Conversion failed: {e}", exc_info=True)
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
    
    def _render_ui_buttons(self, screen: pygame.Surface):
        """Render UI buttons using actual PNG coordinates from hitboxes."""
        # SETTINGS - (248, 735) 73x48
        if self.settings_icon:
            try:
                scaled_settings = pygame.transform.scale(self.settings_icon, (73, 48))
                screen.blit(scaled_settings, (248, 735))
            except Exception as e:
                logger.debug(f"[UI] Settings icon error: {e}")
        
        # FLASH - (321, 735) 73x48
        flash_mode = self.app.config.get('flash', 'mode', default='off')
        flash_overlay = self.flash_overlays.get(flash_mode)
        if flash_overlay:
            try:
                scaled_flash = pygame.transform.scale(flash_overlay, (73, 48))
                screen.blit(scaled_flash, (321, 735))
            except Exception as e:
                logger.debug(f"[UI] Flash overlay error: {e}")
        
        # GALLERY - (387, 735) 73x48
        if self.gallery_icon:
            try:
                scaled_gallery = pygame.transform.scale(self.gallery_icon, (73, 48))
                screen.blit(scaled_gallery, (387, 735))
            except Exception as e:
                logger.debug(f"[UI] Gallery icon error: {e}")
