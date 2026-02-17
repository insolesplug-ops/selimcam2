# 📷 SelimCam v2.0 - Production Camera App for Raspberry Pi

[![Status](https://img.shields.io/badge/status-production-green.svg)](#) 
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](#)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](#)

A professional-grade camera application for Raspberry Pi 3 A+ with 8MP camera module, optimized for battery life and user experience.

## ✨ Features

- **📷 Real-time Camera Preview** - 640×480 @ 24fps with adjustable zoom
- **🎛️ Hardware Controls** - Encoder rotation (zoom), button (menu), touch interface
- **⚡ Power Management** - Intelligent standby mode (6-8x battery improvement)
- **🎨 Professional UI** - Grid overlays, level indicator, flash modes
- **💾 Photo Management** - Automatic storage with photo limit
- **🎬 Boot Animation** - Cool animated startup sequence
- **🛠️ Simulator Mode** - Works on macOS/Linux for development

## 🔧 Hardware Requirements

- **Raspberry Pi 3 A+** (or Pi 3/Zero with adjustments)
- **8MP Camera Module v2** (CSI connector)
- **480×800 Display** (portrait mode)
- **Encoder/Button** (GPIO)
- **Touch Interface** (optional)

## 🚀 Quick Start

### On Raspberry Pi 3 A+

```bash
# 1. SSH into your Pi
ssh pi@raspberrypi.local

# 2. Clone or download code
cd ~
git clone https://github.com/YOUR_USERNAME/FINALMAINCAMMM.git
cd FINALMAINCAMMM

# 3. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Enable camera (if not already enabled)
sudo raspi-config
# → Interface Options → Camera → Enable → Reboot

# 6. First run (test)
python3 main.py

# 7. Auto-start on boot (optional)
sudo systemctl enable selimcam
sudo systemctl start selimcam
```

### On macOS/Linux (Development/Simulator)

```bash
# Create venv
python3 -m venv .venv
source .venv/bin/activate

# Install
pip install -r requirements.txt

# Run simulator
python3 main.py
```

## 📋 Configuration

All settings in `config/config.json`:

```json
{
  "display": {
    "width": 480,
    "height": 800
  },
  "camera": {
    "preview_width": 640,
    "preview_height": 480,
    "capture_quality": 92
  },
  "power": {
    "standby_timeout_s": 30,          // Auto-sleep after 30s
    "shutdown_long_press_s": 1.8      // Long press = shutdown
  }
}
```

## 🎮 Controls

### Simulator (macOS/Linux)

| Key | Action |
|-----|--------|
| `SPACE` / `S` | Capture photo |
| `F` | Toggle flash mode |
| `G` | Toggle grid overlay |
| `L` | Toggle level indicator |
| `LEFT` / `RIGHT` | Encoder rotation (zoom) |
| `RETURN` | Encoder button (menu) |
| `Q` / `W` | Adjust tilt/level |
| `+` / `-` | Brightness |
| `ESC` | Exit / Back |

### Raspberry Pi Hardware

| Input | Action |
|-------|--------|
| **Encoder Rotation** | Zoom in/out |
| **Encoder Button** | Menu / Wake from standby |
| **Touch** | UI interaction / Wake |
| **Long Press** | Shutdown |

## 📁 Project Structure

```
FINALMAINCAMMM/
├── main.py                      # Application entry point
├── config/
│   ├── config.json             # Main configuration
│   └── hitboxes_*.json         # UI touch zones
├── core/
│   ├── logger.py               # Logging system
│   ├── config_manager.py       # Configuration management
│   ├── state_machine.py        # App state flow
│   ├── hitbox_loader.py        # Touch input handling
│   └── photo_manager.py        # Photo storage
├── hardware/
│   ├── camera_backend.py       # Dual camera support (picamera/picamera2)
│   ├── brightness.py           # Backlight control
│   ├── battery.py              # Battery monitoring
│   ├── buttons.py              # Button input
│   └── encoder.py              # Rotary encoder
├── scenes/
│   ├── boot_scene.py           # Startup animation
│   ├── camera_scene.py         # Main camera view
│   ├── gallery_scene.py        # Photo gallery
│   └── settings_scene.py       # Settings menu
├── filters/
│   └── filter_engine.py        # Image filters & effects
├── ui/
│   ├── overlay_renderer.py     # UI rendering
│   ├── grid_overlay.py         # Grid display
│   └── freeze_frame.py         # Capture animation
└── requirements.txt            # Python dependencies
```

## 🔋 Power Management

### Standby Mode (Smart Low-Power)

After 30 seconds of inactivity:
- Screen brightness: 0 (actual backlight off, not just black)
- CPU: ~5% (down from 40%)
- GPU: 0% (down from 20%)
- Battery drain: Minimal

### Wake Triggers

Any of these wakes the device:
- Press encoder button
- Rotate encoder
- Touch screen
- Any key press

### Expected Battery Life

- **Active operation**: ~2 hours
- **With standby mode**: 12-16 hours ⚡

## 🔄 Auto-start Setup

### Option 1: Simple Shell Script

```bash
# Make executable
chmod +x ~/FINALMAINCAMMM/start_camera.sh

# Add to crontab
crontab -e
# Add: @reboot /home/pi/FINALMAINCAMMM/start_camera.sh
```

### Option 2: Systemd Service (Recommended)

```bash
# Copy service file
sudo cp ~/FINALMAINCAMMM/selimcam.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable selimcam
sudo systemctl start selimcam

# Check status
sudo systemctl status selimcam

# View logs
journalctl -u selimcam -f
```

## 🐛 Troubleshooting

### Camera not working on Pi
```bash
# Run diagnostic
python3 camera_diagnostic.py

# Check if enabled
sudo raspi-config
# Interface Options → Camera → Enable → Reboot
```

### High CPU usage
- Check if display is off: `cat /sys/class/backlight/*/brightness`
- Should be 0 in standby, >0 when active

### Photos not saving
- Check directory: `ls -la ~/FINALMAINCAMMM/camera_app_data/photos/`
- Check permissions: `chmod 755 camera_app_data/photos/`

## 📊 Performance Specs

### Target Hardware: Raspberry Pi 3 A+

| Metric | Expected |
|--------|----------|
| FPS | 20-24 fps |
| CPU (active) | 40-50% |
| CPU (standby) | 5-10% |
| Memory | ~150-200 MB |
| Battery life | 12-16 hours |

## 🤖 Development

### Running tests
```bash
python3 test_app.py              # Automated tests
python3 camera_diagnostic.py     # Hardware diagnostic
```

### Modifying configuration
Edit `config/config.json` and restart app - changes auto-load.

### Adding custom filters
Edit `filters/filter_engine.py` and add to filter definitions.

## 📚 Documentation

- [TESTING_GUIDE.md](TESTING_GUIDE.md) - How to test the app
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick answers
- [CHECKUP_REPORT.md](CHECKUP_REPORT.md) - Recent bug fixes
- [BUGFIXES_AND_IMPROVEMENTS.md](BUGFIXES_AND_IMPROVEMENTS.md) - Detailed changes
- [CAMERA_SETUP_PI3.md](CAMERA_SETUP_PI3.md) - Camera setup for Pi 3

## 🔐 Security Notes

- No network connectivity (offline operation)
- All photos stored locally
- No telemetry or tracking
- GPIO access requires appropriate permissions

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Credits

Built for Raspberry Pi 3 A+ with picamera Python library.

---

## 🚀 Push to GitHub

### Initial Setup
```bash
# Create repository on GitHub first!
# Then initialize local git repo

cd ~/FINALMAINCAMMM
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: SelimCam v2.0"

# Add remote (replace USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/FINALMAINCAMMM.git

# First push
git branch -M main
git push -u origin main
```

### Regular Updates
```bash
cd ~/FINALMAINCAMMM

# Make changes...

git add .
git commit -m "Your message"
git push
```

---

**Last Updated**: February 17, 2026  
**Version**: 2.0 (Production)  
**Status**: ✅ Ready for deployment
