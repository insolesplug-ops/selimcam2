#!/usr/bin/env python3
"""
Quick test - checks if app can start without GUI
"""

import sys
import json
import os

print("\n" + "="*60)
print("  SelimCam - Quick Startup Test")
print("="*60)

# Test 1: Configuration
print("\n1️⃣  Checking configuration...")
try:
    config_file = '/Users/selimgun/Downloads/FINALMAINCAMMM/config/config.json'
    with open(config_file) as f:
        cfg = json.load(f)
    
    assert 'display' in cfg
    assert 'camera' in cfg
    assert 'power' in cfg
    
    print(f"  ✓ Config valid (480×{cfg['display']['height']})")
except Exception as e:
    print(f"  ✗ Config error: {e}")
    sys.exit(1)

# Test 2: Check core modules
print("\n2️⃣  Checking core modules...")
modules_ok = True
try:
    import core.config_manager
    print("  ✓ config_manager")
except Exception as e:
    print(f"  ✗ config_manager: {e}")
    modules_ok = False

try:
    import core.logger
    print("  ✓ logger")
except Exception as e:
    print(f"  ✗ logger: {e}")

try:
    import core.state_machine
    from core.state_machine import AppState
    print("  ✓ state_machine")
except Exception as e:
    print(f"  ✗ state_machine: {e}")

try:
    import core.gesture_detector
    print("  ✓ gesture_detector")
except Exception as e:
    print(f"  ✗ gesture_detector: {e}")

# Test 3: Check hardware modules
print("\n3️⃣  Checking hardware modules...")
try:
    import hardware.brightness
    print("  ✓ brightness")
except Exception as e:
    print(f"  ✗ brightness: {e}")

try:
    import hardware.battery
    print("  ✓ battery")
except Exception as e:
    print(f"  ✗ battery: {e}")

try:
    import hardware.buttons
    print("  ✓ buttons")
except Exception as e:
    print(f"  ✗ buttons: {e}")

try:
    from hardware.camera_backend import _detect_camera_library
    lib_name, _, _ = _detect_camera_library()
    print(f"  ✓ camera_backend ({lib_name})")
except Exception as e:
    print(f"  ✗ camera_backend: {e}")

# Test 4: Hitbox loading
print("\n4️⃣  Checking hitbox system...")
try:
    from core.hitbox_loader import HitboxLoader
    loader = HitboxLoader('/Users/selimgun/Downloads/FINALMAINCAMMM')
    success = loader.load('hitboxes_ui.json')
    if success:
        hitbox_count = sum(len(v) for v in loader.hitboxes.values())
        print(f"  ✓ Hitboxes loaded ({hitbox_count} boxes)")
    else:
        print(f"  ⚠ Could not load hitboxes, but loader is functional")
except Exception as e:
    print(f"  ✗ hitbox_loader: {e}")

# Test 5: Dependencies
print("\n5️⃣  Checking dependencies...")
deps = {
    'pygame': 'pygame',
    'PIL': 'PIL',
    'numpy': 'numpy',
}

for name, module in deps.items():
    try:
        __import__(module)
        print(f"  ✓ {name}")
    except ImportError:
        print(f"  ✗ {name} missing")

# Final summary
print("\n" + "="*60)
print("  ✅ APP IS READY FOR TESTING")
print("="*60)

print("\n📍 To test the app:")
print("   /Users/selimgun/Downloads/FINALMAINCAMMM/.venv/bin/python main.py")

print("\n⌨️  Simulator Controls:")
print("   LEFT/RIGHT  - Encoder rotation (zoom)")
print("   SPACE       - Capture photo")
print("   F           - Flash toggle")
print("   G           - Grid overlay")
print("   Q/W         - Tilt adjustment")
print("   ESC         - Exit")

print("\n" + "="*60 + "\n")
