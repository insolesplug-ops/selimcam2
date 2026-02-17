#!/usr/bin/env python3
"""Minimal test - no module imports"""

import json
import os

print("\n✅ SELIMCAM APP READY FOR TESTING\n")

# Test config
config_path = '/Users/selimgun/Downloads/FINALMAINCAMMM/config/config.json'
with open(config_path) as f:
    cfg = json.load(f)

print(f"📊 Configuration:")
print(f"   Display: {cfg['display']['width']}×{cfg['display']['height']}")
print(f"   Camera: {cfg['camera']['preview_width']}×{cfg['camera']['preview_height']} @ {cfg['camera']['preview_fps']}fps")
print(f"   Standby: {cfg['power']['standby_timeout_s']}s")

# Check files exist
print(f"\n📁 Files check:")
files = [
    'main.py',
    'config/config.json',
    'config/hitboxes_ui.json',
    'config/hitboxes_main.json',
]

for f in files:
    full_path = f'/Users/selimgun/Downloads/FINALMAINCAMMM/{f}'
    exists = os.path.exists(full_path)
    status = "✓" if exists else "✗"
    print(f"   {status} {f}")

print(f"\n🎮 TO TEST:")
print(f"   /Users/selimgun/Downloads/FINALMAINCAMMM/.venv/bin/python main.py")

print(f"\n⌨️  CONTROLS:")
print(f"   SPACE       - Capture photo")
print(f"   F           - Flash")
print(f"   G           - Grid")
print(f"   LEFT/RIGHT  - Zoom")
print(f"   ESC         - Exit\n")
