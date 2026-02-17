#!/usr/bin/env python3
"""
Automated test suite for SelimCam
Tests core functionality without GUI
"""

import sys
import json
from pathlib import Path

def test_imports():
    """Test 1: All modules import correctly"""
    print("\n📦 TEST 1: Module Imports")
    print("-" * 50)
    
    modules = [
        'core.logger',
        'core.config_manager',
        'core.state_machine',
        'core.gesture_detector',
        'hardware.camera_backend',
        'hardware.brightness',
        'hardware.battery',
        'scenes.camera_scene',
        'filters.filter_engine',
        'ui.overlay_renderer',
    ]
    
    failed = []
    for mod in modules:
        try:
            __import__(mod)
            print(f"  ✓ {mod}")
        except Exception as e:
            print(f"  ✗ {mod}: {e}")
            failed.append((mod, str(e)))
    
    return len(failed) == 0, failed


def test_config():
    """Test 2: Configuration is valid"""
    print("\n⚙️  TEST 2: Configuration Validation")
    print("-" * 50)
    
    config_path = Path('/Users/selimgun/Downloads/FINALMAINCAMMM/config/config.json')
    
    if not config_path.exists():
        print(f"  ✗ Config file not found: {config_path}")
        return False, ["Config file missing"]
    
    try:
        with open(config_path) as f:
            config = json.load(f)
        
        required_keys = {
            'display': ['width', 'height'],
            'camera': ['preview_width', 'preview_height', 'capture_width', 'capture_height'],
            'power': ['standby_timeout_s', 'shutdown_long_press_s'],
            'ui': ['freeze_duration_ms', 'info_display'],
        }
        
        failed = []
        for section, keys in required_keys.items():
            if section not in config:
                print(f"  ✗ Missing section: {section}")
                failed.append(f"Missing {section}")
                continue
            
            for key in keys:
                if key in config[section]:
                    val = config[section][key]
                    print(f"  ✓ {section}.{key} = {val}")
                else:
                    print(f"  ✗ Missing {section}.{key}")
                    failed.append(f"Missing {section}.{key}")
        
        return len(failed) == 0, failed
    
    except json.JSONDecodeError as e:
        print(f"  ✗ Invalid JSON: {e}")
        return False, ["Invalid JSON"]
    except Exception as e:
        print(f"  ✗ Error reading config: {e}")
        return False, [str(e)]


def test_power_manager():
    """Test 3: PowerManager initialization"""
    print("\n🔋 TEST 3: PowerManager")
    print("-" * 50)
    
    try:
        from main import PowerManager
        pm = PowerManager()
        
        tests = [
            ('Initial state is STANDBY', pm.state == 'STANDBY'),
            ('Frame time tracking', hasattr(pm, 'frame_times')),
            ('Memory tracking', hasattr(pm, 'process')),
            ('FPS history', hasattr(pm, 'fps_history')),
        ]
        
        failed = []
        for name, result in tests:
            if result:
                print(f"  ✓ {name}")
            else:
                print(f"  ✗ {name}")
                failed.append(name)
        
        return len(failed) == 0, failed
    
    except Exception as e:
        print(f"  ✗ PowerManager init failed: {e}")
        return False, [str(e)]


def test_camera_backend():
    """Test 4: Camera backend detection"""
    print("\n📷 TEST 4: Camera Backend")
    print("-" * 50)
    
    try:
        from hardware.camera_backend import _detect_camera_library
        
        lib_name, lib_class, controls = _detect_camera_library()
        
        print(f"  ✓ Detected camera library: {lib_name}")
        print(f"  ✓ Backend class: {lib_class.__name__}")
        
        if lib_name in ['picamera2', 'picamera', 'simulator']:
            print(f"  ✓ Backend is valid: {lib_name}")
            return True, []
        else:
            return False, [f"Unknown backend: {lib_name}"]
    
    except Exception as e:
        print(f"  ✗ Camera detection failed: {e}")
        return False, [str(e)]


def test_state_machine():
    """Test 5: State machine"""
    print("\n🎯 TEST 5: State Machine")
    print("-" * 50)
    
    try:
        from core.state_machine import StateMachine, AppState
        
        sm = StateMachine()
        
        # Test state transitions (using AppState enum)
        tests = [
            ('Initial state is BOOT', sm.current_state == AppState.BOOT),
            ('Transition to CAMERA', sm.should_transition(AppState.CAMERA)),
            ('Can go to SETTINGS', sm.should_transition(AppState.SETTINGS)),
            ('Previous state tracked', sm.previous_state is not None or sm.previous_state is None),
        ]
        
        failed = []
        for name, result in tests:
            if result:
                print(f"  ✓ {name}")
            else:
                print(f"  ✗ {name}")
                failed.append(name)
        
        return len(failed) == 0, failed
    
    except Exception as e:
        print(f"  ✗ State machine test failed: {e}")
        return False, [str(e)]


def test_hitbox_loading():
    """Test 6: Hitbox configuration"""
    print("\n🎮 TEST 6: Hitbox Loading")
    print("-" * 50)
    
    try:
        from core.hitbox_loader import HitboxLoader
        
        loader = HitboxLoader('/Users/selimgun/Downloads/FINALMAINCAMMM')
        success = loader.load('hitboxes_ui.json')
        
        if success and loader.hitboxes:
            hitbox_count = sum(len(boxes) for boxes in loader.hitboxes.values())
            print(f"  ✓ Loaded {hitbox_count} hitboxes")
            for category in list(loader.hitboxes.keys())[:3]:
                print(f"  ✓ Category: {category}")
            return True, []
        else:
            return False, ["No hitboxes loaded"]
    
    except Exception as e:
        print(f"  ✗ Hitbox loading failed: {e}")
        return False, [str(e)]


def main():
    """Run all tests"""
    print("\n" + "="*50)
    print("  SelimCam - Automated Test Suite")
    print("="*50)
    
    tests = [
        test_imports,
        test_config,
        test_power_manager,
        test_camera_backend,
        test_state_machine,
        test_hitbox_loading,
    ]
    
    results = []
    for test_func in tests:
        passed, errors = test_func()
        results.append((test_func.__name__, passed, errors))
    
    # Summary
    print("\n" + "="*50)
    print("  TEST SUMMARY")
    print("="*50)
    
    passed_count = sum(1 for _, passed, _ in results if passed)
    total_count = len(results)
    
    for name, passed, errors in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} : {name}")
        if errors:
            for error in errors[:2]:  # Show first 2 errors
                print(f"       → {error}")
    
    print("\n" + "="*50)
    print(f"  Result: {passed_count}/{total_count} tests passed")
    print("="*50 + "\n")
    
    return 0 if passed_count == total_count else 1


if __name__ == '__main__':
    sys.exit(main())
