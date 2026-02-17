"""Configuration manager with atomic writes and migration."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict
import shutil


class ConfigManager:
    """
    Configuration manager with atomic writes.
    Ensures config integrity even on power loss.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize config manager.
        
        Args:
            config_path: Path to config file (auto-detected if None)
        """
        # Auto-detect config path based on platform
        if config_path is None:
            # On Raspberry Pi, use /home/pi
            if os.path.exists('/home/pi'):
                config_path = "/home/pi/camera_app_data/config.json"
            else:
                # On simulator/macOS, use local directory
                config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.json")
        
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        
        # Ensure directory exists
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            # Fallback to a writable directory
            fallback_path = Path.cwd() / "config" / "config.json"
            print(f"[Config] Could not create {self.config_path.parent}: {e}")
            print(f"[Config] Falling back to {fallback_path.parent}")
            self.config_path = fallback_path
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load config
        self.load()
        
        print(f"[Config] Loaded from {self.config_path}")
    
    def load(self) -> None:
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                print("[Config] Loaded successfully")
            except Exception as e:
                print(f"[Config] Load error: {e}, using defaults")
                self.config = self._get_defaults()
                self.save()
        else:
            print("[Config] No config found, creating defaults")
            self.config = self._get_defaults()
            self.save()
    
    def save(self) -> bool:
        """
        Save configuration with atomic write.
        
        Uses temp file + fsync + rename pattern for atomicity.
        
        Returns:
            True if successful
        """
        try:
            # Write to temporary file
            temp_fd, temp_path = tempfile.mkstemp(
                dir=self.config_path.parent,
                prefix='.config_',
                suffix='.tmp'
            )
            
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
            
            # Atomic rename
            shutil.move(temp_path, self.config_path)
            
            return True
            
        except Exception as e:
            print(f"[Config] Save error: {e}")
            # Cleanup temp file if it exists
            try:
                if 'temp_path' in locals():
                    os.unlink(temp_path)
            except:
                pass
            return False
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Get nested config value.
        
        Example: get('camera', 'preview_fps')
        
        Returns:
            Value or default if not found
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set(self, *keys: str, value: Any, save: bool = True) -> None:
        """
        Set nested config value.
        
        Example: set('camera', 'preview_fps', value=30)
        
        Args:
            *keys: Path to value
            value: Value to set
            save: Whether to save immediately
        """
        if len(keys) == 0:
            return
        
        # Navigate to parent dict
        current = self.config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set value
        current[keys[-1]] = value
        
        # Save if requested
        if save:
            self.save()
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration."""
        # Auto-detect photos directory based on platform
        photos_dir = "/home/pi/camera_app_data/photos" if os.path.exists('/home/pi') else "camera_app_data/photos"
        
        return {
            "camera": {
                "preview_width": 640,
                "preview_height": 480,
                "preview_fps": 24,
                "capture_width": 2592,
                "capture_height": 1944,
                "capture_quality": 92
            },
            "display": {
                "width": 480,
                "height": 800,
                "brightness_mode": "auto",
                "brightness_dark": 40,
                "brightness_medium": 120,
                "brightness_bright": 220
            },
            "filter": {
                "active": "none",
                "iso_fake": 400
            },
            "flash": {
                "mode": "off",
                "auto_threshold_lux": 60,
                "pulse_duration_ms": 120
            },
            "ui": {
                "grid_enabled": False,
                "level_enabled": False,
                "info_display": "minimal",
                "freeze_duration_ms": 700
            },
            "zoom": {
                "current": 1.0,
                "min": 1.0,
                "max": 2.5,
                "step": 0.05,
                "smooth_factor": 0.25
            },
            "haptic": {
                "enabled": True,
                "tick": 1,
                "confirm": 10,
                "capture": 47,
                "error": 14
            },
            "power": {
                "standby_timeout_s": 30,
                "shutdown_long_press_s": 1.8
            },
            "datetime": {
                "last_set": "2026-02-13T14:30:00"
            },
            "storage": {
                "photos_dir": photos_dir,
                "max_photos": 500
            }
        }