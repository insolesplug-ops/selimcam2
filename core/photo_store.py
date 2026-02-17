"""Photo storage manager."""

import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime


class PhotoStore:
    """
    Manages photo storage and retrieval.
    """
    
    def __init__(self, photos_dir: str = "photos"):
        """
        Initialize photo store.
        
        Args:
            photos_dir: Directory to store photos
        """
        self.photos_dir = Path(photos_dir)
        self.photos_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[PhotoStore] Storage: {self.photos_dir.absolute()}")
    
    def list_photos(self) -> List[Path]:
        """
        List all photos sorted by newest first.
        
        Returns:
            List of photo paths
        """
        try:
            photos = list(self.photos_dir.glob("photo_*.jpg"))
            photos.extend(self.photos_dir.glob("photo_*.png"))
            
            # Sort by modification time (newest first)
            photos.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            
            return photos
        except Exception as e:
            print(f"[PhotoStore] List photos failed: {e}")
            return []
    
    def save_photo(self, image_data, extension: str = "jpg") -> Optional[Path]:
        """
        Save photo to storage.
        
        Args:
            image_data: numpy array or pygame Surface
            extension: File extension ('jpg' or 'png')
        
        Returns:
            Path to saved photo or None
        """
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photo_{timestamp}.{extension}"
            filepath = self.photos_dir / filename
            
            # Ensure unique filename
            counter = 1
            while filepath.exists():
                filename = f"photo_{timestamp}_{counter:02d}.{extension}"
                filepath = self.photos_dir / filename
                counter += 1
            
            # Save
            import pygame
            import numpy as np
            from PIL import Image
            
            if isinstance(image_data, pygame.Surface):
                pygame.image.save(image_data, str(filepath))
            elif isinstance(image_data, np.ndarray):
                img = Image.fromarray(image_data)
                quality = 92 if extension == "jpg" else None
                img.save(filepath, quality=quality)
            else:
                raise TypeError(f"Unsupported image type: {type(image_data)}")
            
            print(f"[PhotoStore] Saved: {filepath.name}")
            return filepath
            
        except Exception as e:
            print(f"[PhotoStore] Save failed: {e}")
            return None
    
    def get_photo_count(self) -> int:
        """Get total photo count."""
        return len(self.list_photos())
    
    def delete_oldest(self, keep: int = 500):
        """
        Delete oldest photos to stay under limit.
        
        Args:
            keep: Maximum number of photos to keep
        """
        photos = self.list_photos()
        
        if len(photos) <= keep:
            return
        
        to_delete = photos[keep:]
        for photo in to_delete:
            try:
                photo.unlink()
                print(f"[PhotoStore] Deleted: {photo.name}")
            except Exception as e:
                print(f"[PhotoStore] Delete failed: {e}")