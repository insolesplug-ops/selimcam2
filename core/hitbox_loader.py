"""
Hitbox loader for UI touch zones.
Loads from JSON files.
"""

import json
import os
from typing import Dict, List, Tuple, Optional


class HitboxLoader:
    """
    Loads and manages hitboxes from JSON files.
    """
    
    def __init__(self, base_dir: str = "."):
        """
        Initialize hitbox loader.
        
        Args:
            base_dir: Base directory to search for hitbox files
        """
        self.base_dir = base_dir
        self.hitboxes: Dict[str, List[Dict]] = {}
        
        print(f"[HitboxLoader] Base dir: {base_dir}")
    
    def load(self, filename: str) -> bool:
        """
        Load hitboxes from JSON file.
        
        Args:
            filename: Filename (e.g., 'hitboxes_main.json')
        
        Returns:
            True if loaded successfully
        """
        # Try multiple paths
        search_paths = [
            os.path.join(self.base_dir, filename),
            os.path.join(self.base_dir, "config", filename),
            os.path.join(self.base_dir, "assets", filename),
            filename
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        data = json.load(f)
                    
                    self.hitboxes[filename] = data.get('hitboxes', [])
                    print(f"[HitboxLoader] ✓ Loaded {filename}: {len(self.hitboxes[filename])} hitboxes")
                    return True
                except Exception as e:
                    print(f"[HitboxLoader] ✗ Failed to load {path}: {e}")
                    return False
        
        print(f"[HitboxLoader] ✗ File not found: {filename}")
        print(f"[HitboxLoader]   Searched: {search_paths}")
        return False
    
    def check_hit(self, filename: str, x: int, y: int) -> Optional[str]:
        """
        Check if coordinates hit any hitbox.
        
        Args:
            filename: Hitbox file to check
            x, y: Coordinates
        
        Returns:
            Hitbox ID or None
        """
        if filename not in self.hitboxes:
            return None
        
        for hitbox in self.hitboxes[filename]:
            hx = hitbox.get('x', 0)
            hy = hitbox.get('y', 0)
            hw = hitbox.get('width', 0)
            hh = hitbox.get('height', 0)
            
            if hx <= x < hx + hw and hy <= y < hy + hh:
                return hitbox.get('id', 'unknown')
        
        return None
    
    def get_hitbox(self, filename: str, hitbox_id: str) -> Optional[Dict]:
        """Get specific hitbox by ID."""
        if filename not in self.hitboxes:
            return None
        
        for hitbox in self.hitboxes[filename]:
            if hitbox.get('id') == hitbox_id:
                return hitbox
        
        return None