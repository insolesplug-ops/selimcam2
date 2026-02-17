"""Resource manager for loading and caching assets."""

import pygame
from pathlib import Path
from typing import Dict, Optional


class ResourceManager:
    """
    Manages loading and caching of image and font assets.
    Loads once at startup to avoid per-frame disk access.
    """
    
    def __init__(self, assets_dir: str = "assets"):
        """
        Initialize resource manager.
        
        Args:
            assets_dir: Root assets directory
        """
        self.assets_dir = Path(assets_dir)
        
        # Caches
        self._images: Dict[str, pygame.Surface] = {}
        self._fonts: Dict[tuple, pygame.font.Font] = {}
        
        print("[ResourceManager] Initialized")
    
    def load_image(self, relative_path: str, convert_alpha: bool = True) -> Optional[pygame.Surface]:
        """
        Load and cache an image.
        
        Args:
            relative_path: Path relative to assets_dir
            convert_alpha: Whether to convert with alpha channel
        
        Returns:
            Pygame surface or None if not found
        """
        # Check cache first
        if relative_path in self._images:
            return self._images[relative_path]
        
        # Load from disk
        full_path = self.assets_dir / relative_path
        
        if not full_path.exists():
            print(f"[ResourceManager] Image not found: {full_path}")
            return None
        
        try:
            surface = pygame.image.load(str(full_path))
            
            if convert_alpha:
                surface = surface.convert_alpha()
            else:
                surface = surface.convert()
            
            # Cache
            self._images[relative_path] = surface
            
            print(f"[ResourceManager] Loaded image: {relative_path}")
            return surface
            
        except Exception as e:
            print(f"[ResourceManager] Failed to load {relative_path}: {e}")
            return None
    
    def load_font(self, relative_path: str, size: int) -> pygame.font.Font:
        """
        Load and cache a font.
        
        Args:
            relative_path: Path relative to assets_dir
            size: Font size
        
        Returns:
            Pygame font (fallback to system font if not found)
        """
        cache_key = (relative_path, size)
        
        # Check cache
        if cache_key in self._fonts:
            return self._fonts[cache_key]
        
        # Load from disk
        full_path = self.assets_dir / relative_path
        
        try:
            if full_path.exists():
                font = pygame.font.Font(str(full_path), size)
                print(f"[ResourceManager] Loaded font: {relative_path} @ {size}pt")
            else:
                print(f"[ResourceManager] Font not found: {full_path}, using default")
                font = pygame.font.Font(None, size)
            
            # Cache
            self._fonts[cache_key] = font
            
            return font
            
        except Exception as e:
            print(f"[ResourceManager] Failed to load font {relative_path}: {e}")
            # Fallback to default
            font = pygame.font.Font(None, size)
            self._fonts[cache_key] = font
            return font
    
    def get_image(self, relative_path: str) -> Optional[pygame.Surface]:
        """
        Get cached image.
        
        Args:
            relative_path: Path relative to assets_dir
        
        Returns:
            Cached surface or None
        """
        return self._images.get(relative_path)
    
    def preload_all(self) -> None:
        """Preload all common assets."""
        # UI overlays
        ui_assets = [
            "ui/flash off.png",
            "ui/flash on.png",
            "ui/flash automatically.png",
            "ui/gallery.png",
            "ui/settings.png",
            "ui/boot_logo.png"
        ]
        
        for asset in ui_assets:
            self.load_image(asset)
        
        # Fonts
        self.load_font("fonts/Inter_regular.ttf", 20)
        self.load_font("fonts/Inter_regular.ttf", 24)
        self.load_font("fonts/inter_bold.ttf", 28)
        self.load_font("fonts/inter_bold.ttf", 32)
        
        print("[ResourceManager] Preload complete")