"""
Settings scene with all configurable options.
Full keyboard + encoder + touch navigation.
"""

import pygame
from typing import List, Dict, Any
from datetime import datetime


class SettingsScene:
    """
    Settings menu with 10 configurable options.
    """
    
    def __init__(self, app):
        """Initialize settings scene."""
        self.app = app
        
        # UI state
        self.selected_index = 0
        self.edit_mode = False
        
        # Build settings list
        self._build_settings_list()
        
        # Load settings overlay PNG
        self.settings_overlay = app.resource_manager.get_image("ui/settings.png")
        
        # Fonts
        try:
            self.font_title = app.resource_manager.load_font("fonts/inter_bold.ttf", 32)
            self.font_label = app.resource_manager.load_font("fonts/Inter_regular.ttf", 22)
            self.font_value = app.resource_manager.load_font("fonts/inter_bold.ttf", 22)
        except:
            self.font_title = pygame.font.SysFont("Arial", 32, bold=True)
            self.font_label = pygame.font.SysFont("Arial", 22)
            self.font_value = pygame.font.SysFont("Arial", 22, bold=True)
        
        # Load hitboxes
        try:
            from core.hitbox_loader import HitboxLoader
            self.hitbox_loader = HitboxLoader()
            self.hitbox_loader.load("hitboxes_settings.json")
        except:
            self.hitbox_loader = None
        
        print("[SettingsScene] Initialized")
    
    def _build_settings_list(self):
        """Build simplified settings list - only working options."""
        self.settings = [
            {
                'label': 'Brightness',
                'type': 'choice',
                'config_path': ('display', 'brightness_mode'),
                'choices': ['dark', 'medium', 'bright', 'auto'],
                'default': 'medium'
            },
            {
                'label': 'Filter',
                'type': 'choice',
                'config_path': ('filter', 'active'),
                'choices': ['none', 'warm', 'cold', 'monochrom'],
                'default': 'none'
            },
            {
                'label': 'Flash Mode',
                'type': 'choice',
                'config_path': ('flash', 'mode'),
                'choices': ['off', 'on', 'auto'],
                'default': 'off'
            },
            {
                'label': 'Grid Overlay',
                'type': 'bool',
                'config_path': ('ui', 'grid_enabled'),
                'default': False
            },
            {
                'label': 'Level Indicator',
                'type': 'bool',
                'config_path': ('ui', 'level_enabled'),
                'default': False
            },
            {
                'label': 'Info Display',
                'type': 'choice',
                'config_path': ('ui', 'info_display'),
                'choices': ['off', 'minimal'],
                'default': 'minimal'
            },
        ]
    
    def on_enter(self):
        """Called when entering scene."""
        self.selected_index = 0
        self.edit_mode = False
    
    def on_exit(self):
        """Called when exiting scene."""
        pass
    
    def handle_event(self, event: pygame.event.Event):
        """Handle input events."""
        from core.state_machine import AppEvent
        
        if event.type == pygame.KEYDOWN:
            if self.edit_mode:
                # Edit mode controls
                if event.key == pygame.K_ESCAPE:
                    self.edit_mode = False
                elif event.key == pygame.K_LEFT:
                    self._adjust_value(-1)
                elif event.key == pygame.K_RIGHT:
                    self._adjust_value(1)
                elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    self.edit_mode = False
            else:
                # Navigation mode
                if event.key == pygame.K_UP:
                    self.selected_index = max(0, self.selected_index - 1)
                elif event.key == pygame.K_DOWN:
                    self.selected_index = min(len(self.settings) - 1, self.selected_index + 1)
                elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    self._activate_setting()
                elif event.key == pygame.K_ESCAPE:
                    self.app.state_machine.handle_event(AppEvent.BACK_TO_CAMERA)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            # Check if clicked on a setting to edit it
            clicked_index = self._get_clicked_setting(mx, my)
            if clicked_index is not None:
                self.selected_index = clicked_index
                self._activate_setting()
                # Auto-increment value by touching (easier than encoder)
                self._adjust_value(1)
            # Note: Back button hitbox is handled by main.py HitboxEngine
    
    def _get_clicked_setting(self, x: int, y: int) -> int:
        """Get setting index from click position."""
        # Settings list starts at y=100, each item is 60px tall
        start_y = 100
        item_height = 60
        
        if y < start_y:
            return None
        
        index = (y - start_y) // item_height
        
        if 0 <= index < len(self.settings):
            return index
        
        return None
    
    def _activate_setting(self):
        """Activate/edit current setting."""
        setting = self.settings[self.selected_index]
        
        if setting['type'] in ['choice', 'int', 'bool']:
            self.edit_mode = True
        elif setting['type'] == 'datetime':
            # TODO: Show datetime picker
            print("[Settings] DateTime picker not implemented yet")
        elif setting['type'] == 'info':
            # Just info, no action
            pass
    
    def _adjust_value(self, delta: int):
        """Adjust current setting value."""
        setting = self.settings[self.selected_index]
        config_path = setting.get('config_path')
        
        if not config_path:
            return
        
        if setting['type'] == 'choice':
            # Cycle through choices
            choices = setting['choices']
            current = self.app.config.get(config_path[0], config_path[1], default=setting['default'])
            
            try:
                current_idx = choices.index(current)
            except ValueError:
                current_idx = 0
            
            new_idx = (current_idx + delta) % len(choices)
            new_value = choices[new_idx]
            
            self.app.config.set(config_path[0], config_path[1], value=new_value, save=True)
            
            # Apply immediately if brightness
            if config_path == ('display', 'brightness_mode'):
                self._apply_brightness(new_value)
        
        elif setting['type'] == 'int':
            # Increment/decrement
            current = self.app.config.get(config_path[0], config_path[1], default=setting['default'])
            step = setting.get('step', 1)
            min_val = setting.get('min', 0)
            max_val = setting.get('max', 100)
            
            new_value = current + (delta * step)
            new_value = max(min_val, min(max_val, new_value))
            
            self.app.config.set(config_path[0], config_path[1], value=new_value, save=True)
        
        elif setting['type'] == 'bool':
            # Toggle
            current = self.app.config.get(config_path[0], config_path[1], default=setting['default'])
            new_value = not current
            self.app.config.set(config_path[0], config_path[1], value=new_value, save=True)
    
    def _apply_brightness(self, mode: str):
        """Apply brightness mode immediately."""
        if not self.app.brightness_ctrl or not self.app.brightness_ctrl.available:
            return
        
        if mode == 'auto':
            # Auto mode handled by sensor thread
            pass
        else:
            values = {
                'dark': self.app.config.get('display', 'brightness_dark', default=40),
                'medium': self.app.config.get('display', 'brightness_medium', default=120),
                'bright': self.app.config.get('display', 'brightness_bright', default=220)
            }
            self.app.brightness_ctrl.set_brightness(values.get(mode, 120))
    
    def handle_encoder_rotation(self, delta: int):
        """Handle encoder rotation."""
        if self.edit_mode:
            self._adjust_value(delta)
        else:
            # Navigate
            self.selected_index += delta
            self.selected_index = max(0, min(len(self.settings) - 1, self.selected_index))
    
    def update(self, dt: float):
        """Update scene."""
        pass
    
    def render(self, screen: pygame.Surface):
        """Render settings with overlay and settings list."""
        screen.fill((20, 20, 20))
        
        # Display settings.png overlay first (background)
        if self.settings_overlay:
            screen.blit(self.settings_overlay, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        
        # Render settings list on top (clean, minimal style)
        self._render_settings_list(screen)
    
    def _render_settings_list(self, screen: pygame.Surface):
        """Render scrollable settings list - Apple dark mode style."""
        # Title
        title_surf = self.font_title.render("Settings", True, (255, 255, 255))
        title_rect = title_surf.get_rect()
        title_rect.centerx = 240
        title_rect.top = 25
        screen.blit(title_surf, title_rect)
        
        # Settings items - iOS-style cells
        start_y = 85
        item_height = 52
        
        for i, setting in enumerate(self.settings):
            # Get current value
            config_path = setting.get('config_path')
            
            if config_path:
                value = self.app.config.get(config_path[0], config_path[1], default=setting['default'])
            else:
                value = setting.get('value', '')
            
            # Format value for display
            if setting['type'] == 'bool':
                value_str = "On" if value else "Off"
                value_color = (100, 255, 100) if value else (150, 150, 150)
            elif setting['type'] == 'datetime':
                value_str = datetime.now().strftime("%H:%M") if not value else value
                value_color = (100, 200, 255)
            elif setting['type'] == 'info':
                value_str = str(value)
                value_color = (150, 150, 150)
            else:
                value_str = str(value).upper() if isinstance(value, str) else str(value)
                value_color = (120, 200, 255)
            
            y = start_y + i * item_height
            
            # Skip if off screen
            if y > 700:
                break
            
            is_selected = i == self.selected_index
            
            # iOS-style cell with separator
            cell_bg = pygame.Rect(15, y - 3, 450, 50)
            
            # Selected cell: blue highlight
            if is_selected:
                pygame.draw.rect(screen, (50, 90, 150), cell_bg, border_radius=10)
                pygame.draw.rect(screen, (100, 180, 255), cell_bg, width=2, border_radius=10)
                label_color = (255, 255, 255)
            else:
                # Unselected: subtle separator
                pygame.draw.line(screen, (40, 40, 40), (20, y + 45), (460, y + 45), 1)
                label_color = (200, 200, 200)
            
            # Label (left, bold)
            label_surf = self.font_label.render(setting['label'], True, label_color)
            label_rect = label_surf.get_rect()
            label_rect.left = 30
            label_rect.centery = y + 20
            screen.blit(label_surf, label_rect)
            
            # Value (right, colored)
            value_surf = self.font_value.render(value_str, True, value_color)
            value_rect = value_surf.get_rect()
            value_rect.right = 440
            value_rect.centery = y + 20
            screen.blit(value_surf, value_rect)
        
        # Back button + UI buttons handled by overlays (no text labels)
        # Touch hitboxes handle navigation