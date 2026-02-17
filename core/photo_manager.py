"""Photo storage and retrieval manager."""

import os
from datetime import datetime
from pathlib import Path
from typing import List


class PhotoManager:
    """
    Manages photo storage, naming, and retrieval.
    Handles photo limits and cleanup.
    """
    
    def __init__(self, photos_dir: str = None):
        """
        Initialize photo manager.
        
        Args:
            photos_dir: Directory for photo storage (auto-detected if None)
        """
        if photos_dir is None:
            # Auto-detect based on platform
            if os.path.exists('/home/pi'):
                photos_dir = "/home/pi/camera_app_data/photos"
            else:
                photos_dir = "camera_app_data/photos"
        
        self.photos_dir = Path(photos_dir)
        self.photos_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[PhotoManager] Storage: {self.photos_dir}")
    
    def generate_filename(self, extension: str = "jpg") -> str:
        """
        Generate unique filename with timestamp.
        
        Format: photo_YYYYMMDD_HHMMSS.jpg
        Handles collisions with _01, _02, etc.
        
        Args:
            extension: File extension (jpg, png)
        
        Returns:
            Full filepath
        """
        now = datetime.now()
        base_name = now.strftime("photo_%Y%m%d_%H%M%S")
        
        counter = 0
        while True:
            if counter == 0:
                filename = f"{base_name}.{extension}"
            else:
                filename = f"{base_name}_{counter:02d}.{extension}"
            
            filepath = self.photos_dir / filename
            
            if not filepath.exists():
                return str(filepath)
            
            counter += 1
            
            if counter > 99:
                raise RuntimeError("Too many photos in same second")
    
    def list_photos(self, extension: str = "jpg") -> List[Path]:
        """
        List all photos sorted by timestamp (newest first).
        
        Args:
            extension: File extension to filter
        
        Returns:
            List of photo paths
        """
        photos = sorted(
            self.photos_dir.glob(f"*.{extension}"),
            reverse=True  # Newest first
        )
        
        return photos
    
    def get_photo_count(self, extension: str = "jpg") -> int:
        """
        Get total number of photos.
        
        Args:
            extension: File extension to filter
        
        Returns:
            Photo count
        """
        return len(self.list_photos(extension))
    
    def enforce_limit(self, max_photos: int, extension: str = "jpg") -> int:
        """
        Delete oldest photos if limit exceeded.
        
        Args:
            max_photos: Maximum number of photos to keep
            extension: File extension
        
        Returns:
            Number of photos deleted
        """
        photos = self.list_photos(extension)
        deleted_count = 0
        
        while len(photos) > max_photos:
            # Delete oldest (last in list due to reverse sort)
            oldest = photos[-1]
            
            try:
                oldest.unlink()
                print(f"[PhotoManager] Deleted old photo: {oldest.name}")
                deleted_count += 1
                photos.pop()
            except Exception as e:
                print(f"[PhotoManager] Failed to delete {oldest}: {e}")
                break
        
        return deleted_count
    
    def get_storage_info(self) -> dict:
        """
        Get storage statistics.
        
        Returns:
            Dict with photo count, total size, etc.
        """
        photos = self.list_photos()
        
        total_size = 0
        for photo in photos:
            try:
                total_size += photo.stat().st_size
            except:
                pass
        
        return {
            "count": len(photos),
            "total_size_mb": total_size / (1024 * 1024),
            "directory": str(self.photos_dir)
        }