"""
SelimCam Setup Script
Automated installation and verification.
"""

import os
import sys
import subprocess

def run_command(cmd, description):
    """Run command and handle errors."""
    print(f"\n[SETUP] {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"[SETUP] OK {description} successful")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[SETUP] ERROR {description} failed:")
        print(e.stderr)
        return False

def check_file(path, description):
    """Check if file exists."""
    if os.path.exists(path):
        print(f"[SETUP] OK {description} found")
        return True
    else:
        print(f"[SETUP] ERROR {description} missing")
        return False

def create_directory(path):
    """Create directory if not exists."""
    os.makedirs(path, exist_ok=True)
    print(f"[SETUP] OK Created {path}")

print("="*70)
print(" SELIMCAM v2.0 - AUTOMATED SETUP")
print("="*70)

# Step 1: Create directories
print("\n[STEP 1] Creating directory structure...")
dirs = [
    "core", "hardware", "filters", "ui", "scenes",
    "assets/ui", "assets/fonts",
    "camera_app_data/photos"
]
for d in dirs:
    create_directory(d)

# Step 2: Create __init__.py files
print("\n[STEP 2] Creating __init__.py files...")
init_dirs = ["core", "hardware", "filters", "ui", "scenes"]
for d in init_dirs:
    init_file = os.path.join(d, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write(f'"""{d.capitalize()} module."""\n')
        print(f"[SETUP] OK Created {init_file}")

# Step 3: Install dependencies
print("\n[STEP 3] Installing Python dependencies...")
run_command("pip install pygame Pillow numpy psutil", "Dependency installation")

# Step 4: Generate placeholder assets
print("\n[STEP 4] Generating placeholder assets...")
if os.path.exists("generate_placeholders.py"):
    run_command("python generate_placeholders.py", "Placeholder generation")
else:
    print("[SETUP] WARN generate_placeholders.py not found")

# Step 5: Verify files
print("\n[STEP 5] Verifying file structure...")
required_files = {
    "main.py": "Main application",
    "core/config_manager.py": "Config manager",
    "core/state_machine.py": "State machine",
    "hardware/simulator.py": "Simulator backends",
    "scenes/camera_scene.py": "Camera scene",
    "filters/filter_engine.py": "Filter engine",
}

all_ok = True
for file, desc in required_files.items():
    if not check_file(file, desc):
        all_ok = False

# Step 6: Check fonts
print("\n[STEP 6] Checking fonts...")
font_regular = "assets/fonts/Inter_regular.ttf"
font_bold = "assets/fonts/inter_bold.ttf"

if not os.path.exists(font_regular) or not os.path.exists(font_bold):
    print("[SETUP] WARN Fonts missing - app will use system fonts")
    print("To add custom fonts:")
    print("  1. Download from: https://fonts.google.com/specimen/Inter")
    print(f"  2. Copy Inter-Regular.ttf → {font_regular}")
    print(f"  3. Copy Inter-Bold.ttf → {font_bold}")

# Final report
print("\n" + "="*70)
if all_ok:
    print(" OK SETUP COMPLETE - READY TO RUN")
    print("="*70)
    print("\nRun the app with:")
    print("  python main.py")
else:
    print(" WARN SETUP INCOMPLETE - MISSING FILES")
    print("="*70)
    print("\nSome files are missing. Please ensure all code files are present.")

print()