#!/usr/bin/env python3
"""
Camera diagnostic tool for SelimCam.
Run this on your Raspberry Pi to check camera configuration and compatibility.

Usage:
    python3 camera_diagnostic.py
"""

import sys
import os
import platform
import subprocess
from pathlib import Path

def print_header(text):
    """Print formatted header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_success(text):
    """Print success message."""
    print(f"  ✓ {text}")

def print_error(text):
    """Print error message."""
    print(f"  ✗ {text}")

def print_warning(text):
    """Print warning message."""
    print(f"  ⚠ {text}")

def print_info(text):
    """Print info message."""
    print(f"  ℹ {text}")

def run_command(cmd, silent=False):
    """Run shell command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        if not silent and result.returncode != 0:
            print(result.stderr)
        return result.stdout.strip()
    except Exception as e:
        return str(e)

def check_platform():
    """Check if running on Raspberry Pi."""
    print_header("1. Platform Detection")
    
    # Check OS
    if platform.system() == "Linux":
        print_success(f"Linux detected: {platform.release()}")
    else:
        print_error(f"Non-Linux OS: {platform.system()}")
        return False
    
    # Check Raspberry Pi
    is_pi = False
    if os.path.exists('/sys/firmware/devicetree/base/model'):
        try:
            with open('/sys/firmware/devicetree/base/model', 'r') as f:
                model = f.read().strip()
                if 'Raspberry Pi' in model:
                    print_success(f"Raspberry Pi detected: {model}")
                    is_pi = True
                else:
                    print_error(f"Not a Raspberry Pi: {model}")
        except (IOError, OSError, UnicodeDecodeError) as e:
            print_warning(f"Could not read device model: {e}")
    
    if not is_pi:
        print_error("Could not detect Raspberry Pi")
    
    return is_pi

def check_camera_enable():
    """Check if camera is enabled in firmware."""
    print_header("2. Camera Interface Status")
    
    enabled = False
    
    for boot_file in ['/boot/firmware/config.txt', '/boot/config.txt']:
        if os.path.exists(boot_file):
            try:
                with open(boot_file, 'r') as f:
                    content = f.read()
                    if 'camera_enabled=1' in content:
                        print_success(f"Camera enabled in {boot_file}")
                        enabled = True
                        break
                    elif 'camera_enabled=0' in content:
                        print_error(f"Camera DISABLED in {boot_file}")
                        print_warning("Fix: sudo raspi-config → Interface → Camera → Enable → Reboot")
                        break
                    elif '#camera' in content or 'start_x' not in content:
                        print_warning(f"Camera status unclear in {boot_file}")
            except (IOError, OSError, UnicodeDecodeError) as e:
                print_warning(f"Could not read {boot_file}: {e}")
    
    if not enabled:
        print_warning("Could not verify camera enablement via /boot/config.txt")
        print_info("Run: sudo raspi-config → Interface Options → Camera → Enable")
    
    return enabled

def check_device_files():
    """Check /dev/video* files."""
    print_header("3. Device Files")
    
    video_files = list(Path('/dev').glob('video*'))
    
    if video_files:
        print_success(f"Found {len(video_files)} video device(s):")
        for vf in sorted(video_files):
            size = os.path.getsize(vf) if vf.exists() else 0
            print_info(f"{vf.name}")
    else:
        print_error("No /dev/video* files found!")
        print_warning("Camera may not be properly connected or detected")
    
    return len(video_files) > 0

def check_gpu_memory():
    """Check GPU memory allocation."""
    print_header("4. GPU Memory Allocation")
    
    try:
        gpu_mem = run_command("vcgencmd get_config gpu_mem")
        if gpu_mem:
            print_success(f"GPU Memory: {gpu_mem}")
            if "64" in gpu_mem:
                print_warning("GPU memory is 64MB - consider increasing to 256MB for better camera performance")
                print_info("sudo raspi-config → Performance Options → GPU Memory")
        else:
            print_warning("Could not read GPU memory")
    except (OSError, subprocess.TimeoutExpired) as e:
        print_warning(f"vcgencmd not available: {e}")
    
    return True

def check_temperature():
    """Check CPU temperature."""
    print_header("5. System Health")
    
    try:
        temp_output = run_command("vcgencmd measure_temp")
        if temp_output:
            print_success(f"CPU Temp: {temp_output}")
            if "90" in temp_output or "8[0-9]" in temp_output:
                print_warning("High temperature detected! Add heatsink or improve airflow")
    except (OSError, subprocess.TimeoutExpired) as e:
        print_warning(f"vcgencmd not available: {e}")
    
    try:
        freq_output = run_command("vcgencmd measure_clock arm")
        if freq_output:
            print_info(f"ARM Clock: {freq_output}")
    except (OSError, subprocess.TimeoutExpired) as e:
        print_info(f"Could not read ARM clock: {e}")

def check_python_modules():
    """Check available Python camera modules."""
    print_header("6. Python Camera Libraries")
    
    libraries_found = []
    
    # Check picamera2 (Pi 4+)
    try:
        import picamera2
        print_success("picamera2 (modern) found - for Pi 4/5+")
        libraries_found.append('picamera2')
    except ImportError:
        print_info("picamera2 not installed")
    
    # Check picamera (Pi 3/Zero)
    try:
        import picamera
        print_success("picamera (legacy) found - for Pi 3/3A+/Zero")
        libraries_found.append('picamera')
    except ImportError:
        print_warning("picamera not installed (required for Pi 3/3A+)")
        print_info("Install with: pip install picamera==1.13")
    
    if not libraries_found:
        print_error("NO CAMERA LIBRARIES FOUND!")
        print_info("Install one:")
        print_info("  Pi 4/5: pip install picamera2")
        print_info("  Pi 3/3A+: pip install picamera==1.13")
    
    return libraries_found

def check_camera_access():
    """Try to actually access the camera."""
    print_header("7. Camera Access Test")
    
    # Try picamera first (Pi 3 compatible)
    try:
        from picamera import PiCamera
        print_info("Attempting to access camera with picamera...")
        cam = PiCamera()
        print_success("✓ Camera accessible via picamera!")
        
        # Get camera info
        resolution = cam.resolution
        framerate = cam.framerate
        print_info(f"Resolution: {resolution}")
        print_info(f"Framerate: {framerate}")
        
        cam.close()
        return True
        
    except ImportError:
        print_warning("picamera module not installed")
    except Exception as e:
        print_error(f"Camera access failed: {e}")
        print_warning("Check:")
        print_info("  1. Camera physically connected")
        print_info("  2. Camera ribbon secure")
        print_info("  3. Camera enabled: sudo raspi-config")
        print_info("  4. GPU memory: >=128MB")
        return False
    
    # Try picamera2 (Pi 4+)
    try:
        from picamera2 import Picamera2
        print_info("Attempting to access camera with picamera2...")
        cam = Picamera2()
        print_success("✓ Camera accessible via picamera2!")
        cam.close()
        return True
        
    except ImportError:
        print_warning("picamera2 module not installed")
    except Exception as e:
        print_error(f"Camera access failed: {e}")
        return False
    
    print_error("Could not access camera with any library")
    return False

def check_filesystem():
    """Check if app files exist."""
    print_header("8. Application Files")
    
    files_to_check = [
        'main.py',
        'config/config.json',
        'hitboxes_ui.json',
        'hardware/camera_backend.py',
        'assets/ui/flash off.png',
    ]
    
    app_dir = Path('/home/pi/FINALMAINCAMMM') if Path('/home/pi/FINALMAINCAMMM').exists() else Path('.')
    
    all_exist = True
    for filename in files_to_check:
        filepath = app_dir / filename
        if filepath.exists():
            print_success(f"{filename}")
        else:
            print_error(f"{filename} - NOT FOUND")
            all_exist = False
    
    return all_exist

def main():
    """Run all diagnostics."""
    print("\n" + "="*60)
    print("  SelimCam Camera Diagnostic Tool")
    print("="*60)
    
    results = {
        'platform': check_platform(),
        'camera_enable': check_camera_enable(),
        'device_files': check_device_files(),
        'gpu_memory': check_gpu_memory(),
        'temperature': check_temperature(),
        'python_modules': check_python_modules(),
        'camera_access': check_camera_access(),
        'files': check_filesystem(),
    }
    
    # Summary
    print_header("Diagnostic Summary")
    
    critical = [
        ('Platform: Pi', results['platform']),
        ('Camera Enabled', results['camera_enable']),
        ('Device Files', results['device_files']),
        ('Python Libraries', len(results['python_modules']) > 0),
        ('Camera Access', results['camera_access']),
    ]
    
    passed = sum(1 for _, result in critical if result)
    total = len(critical)
    
    print(f"\nPassed: {passed}/{total}\n")
    
    for check, result in critical:
        if result:
            print_success(check)
        else:
            print_error(check)
    
    if passed == total:
        print_header("All Checks Passed! ✓")
        print("Your camera should work with SelimCam.")
        print("Run: python3 main.py")
    else:
        print_header("Some Checks Failed")
        print("Please fix the issues above before running SelimCam.")
        print("\nMost common fixes:")
        print("  1. Enable camera: sudo raspi-config → Interface → Camera")
        print("  2. Reboot: sudo reboot")
        print("  3. Install camera lib: pip install picamera==1.13")
        print("  4. Increase GPU memory: sudo raspi-config → Performance → GPU Mem: 256MB")
    
    print("\n" + "="*60 + "\n")

if __name__ == '__main__':
    main()
