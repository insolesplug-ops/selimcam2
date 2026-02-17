# 🎮 SelimCam - Testing Guide

## Quick Start Test

### Test 1: GUI Simulator (macOS/Linux)

```bash
cd /Users/selimgun/Downloads/FINALMAINCAMMM
./.venv/bin/python main.py
```

**Simulator Controls:**
- `SPACE` / `S` → Foto machen (Shutter)
- `F` → Blitz umschalten
- `G` → Grid Overlay
- `L` → Level Indicator  
- `LEFT` / `RIGHT` → Encoder drehen (Zoom)
- `RETURN` → Encoder Button (Menu)
- `Q` / `W` → Neigung anpassen
- `+` / `-` → Helligkeit simulieren
- `MOUSE click+drag` → Touch simulieren
- `ESC` → Zurück / App beenden

---

## Test 2: Configuration Verify

```bash
# Check if config is valid JSON and contains required keys
cd /Users/selimgun/Downloads/FINALMAINCAMMM
python3 -c "
import json
with open('config/config.json') as f:
    cfg = json.load(f)
print('✓ Display:', cfg['display']['width'], 'x', cfg['display']['height'])
print('✓ Camera:', cfg['camera']['preview_width'], 'x', cfg['camera']['preview_height'])
print('✓ Standby:', cfg['power']['standby_timeout_s'], 'seconds')
print('✓ Config is valid!')
"
```

---

## Test 3: Check Files

```bash
ls -la /Users/selimgun/Downloads/FINALMAINCAMMM/config/

# Should show:
# config.json ← Main configuration
# hitboxes_ui.json ← Button layout
# hitboxes_main.json ← Additional hitboxes
# hitboxes_gallery.json ← Gallery hitboxes
# hitboxes_settings.json ← Settings hitboxes
```

---

## Test 4: Verify Python Environment

```bash
cd /Users/selimgun/Downloads/FINALMAINCAMMM

# Check Python
./.venv/bin/python --version
# Should show: Python 3.9.6

# Check packages
./.venv/bin/python -c "import pygame, numpy, PIL; print('✓ All packages OK')"
```

---

## Test 5: On Raspberry Pi 3 A+

### Setup
```bash
# Copy code to Pi
scp -r /Users/selimgun/Downloads/FINALMAINCAMMM pi@raspberrypi.local:~/

# SSH into Pi
ssh pi@raspberrypi.local

# Install environment
cd ~/FINALMAINCAMMM
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Enable camera
sudo raspi-config
# → Interface Options → Camera → Enable → Reboot

# Run
python3 main.py
```

### Expected Behavior
- ✅ Boot animation shows briefly
- ✅ Camera preview appears  
- ✅ Encoder/touch controls work
- ✅ Photos save to `camera_app_data/photos/`
- ✅ After 30s idle: screen goes OFF (brightness=0)
- ✅ Any button/touch wakes device
- ✅ Grid/Level overlays toggle
- ✅ Flash mode cycles through: off, on, auto

### Performance Targets
- **FPS**: 20-24 fps in preview
- **CPU (active)**: 40-50%
- **CPU (standby)**: 5-10% (much lower than before!)
- **Memory**: ~150-200 MB
- **Battery**: 12-16 hours (with standby mode)

---

## Troubleshooting

### App won't start
```bash
# Check if pygame is installed
./.venv/bin/python -c "import pygame; print('✓ pygame OK')"

# Check if numpy is installed  
./.venv/bin/python -c "import numpy; print('✓ numpy OK')"
```

### Camera not working on Pi
```bash
# Run diagnostic
python3 camera_diagnostic.py
```

### Can't wake from standby
```bash
# Check brightness control
cat /sys/class/backlight/*/brightness
# Should be 0 when in standby, >0 when awake
```

### High CPU usage
```bash
# Check with top command
top -bn1 | grep python
# In standby should be <10% CPU
```

---

## Documentation Files

- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick answers
- **[SESSION_SUMMARY.md](SESSION_SUMMARY.md)** - What was done
- **[CHECKUP_REPORT.md](CHECKUP_REPORT.md)** - Bug fixes applied  
- **[BUGFIXES_AND_IMPROVEMENTS.md](BUGFIXES_AND_IMPROVEMENTS.md)** - Detailed fixes
- **[HITBOX_AND_OVERLAY_CONFIG.md](HITBOX_AND_OVERLAY_CONFIG.md)** - UI configuration
- **[CAMERA_SETUP_PI3.md](CAMERA_SETUP_PI3.md)** - Camera setup guide

---

## Ready to Test?

Start with the simulator:
```bash
/Users/selimgun/Downloads/FINALMAINCAMMM/.venv/bin/python /Users/selimgun/Downloads/FINALMAINCAMMM/main.py
```

**Good luck! 🚀**
