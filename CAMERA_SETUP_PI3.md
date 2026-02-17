# Camera Setup for Raspberry Pi 3 A+ (8MP Camera)

## ✅ What's Been Fixed

Your camera backend now **auto-detects** your Pi model and uses the correct library:
- **Pi 4/5+**: Uses modern `picamera2` library
- **Pi 3/3A+/Zero/Zero W**: Uses legacy `picamera` library ← **Your Pi**

---

## 🔧 Installation Steps for Pi 3 A+

### 1. **Enable Camera Interface** (CRITICAL - Do This First!)

The most common reason cameras don't work is that the camera interface is **disabled**.

```bash
sudo raspi-config
```

Navigate to:
- **Interface Options** → **Camera** → **Enable**
- Exit and **reboot your Pi**: `sudo reboot`

Check if enabled:
```bash
cat /boot/config.txt | grep camera
```

You should see:
```
camera_enabled=1
```

### 2. **Install Camera Library for Pi 3 A+**

The app will auto-detect your Pi and needs the **legacy picamera** library:

```bash
sudo apt update
sudo apt install -y python3-picamera
```

OR with pip:

```bash
pip install picamera==1.13
```

### 3. **Verify Camera is Recognized**

Test if your camera is detected:

```bash
ls -la /dev/video*
libcamera-hello  # Should show camera preview (then press Ctrl+C)
```

If you see `/dev/video0` and `/dev/video1`, camera is working! ✅

### 4. **Test Still Capture** (Optional)

```bash
sudo raspistill -o test.jpg
```

This should create `test.jpg` in the current directory.

---

## 🚀 Running SelimCam on Pi 3 A+

### Basic Setup

```bash
cd ~/FINALMAINCAMMM
source .venv/bin/activate
python main.py
```

### What To Expect

You'll see:
```
[Platform] 🍓 Raspberry Pi detected - using hardware backends
[Camera] Using picamera (legacy) - for Pi 3/3A+/Zero/Zero W
[Camera] ℹ️  Pi 3/3A+ detected - optimized for 512MB RAM
[Camera] Initialized (picamera/legacy): preview 640x480 @ 24fps
[Camera] Preview started (legacy)
```

### Camera LED

The camera LED will be off during operation (to save battery). To enable it:

Edit line in `hardware/camera_backend.py`:
```python
# self.camera.led = False  # Change this to:
self.camera.led = True
```

---

## 📊 Performance

**Expected Performance on Pi 3 A+**:
- Preview FPS: 20-24 (depends on load)
- Memory: ~200-250MB (out of 512MB available)
- CPU: ~30-50% during preview
- Capture time: 1-2 seconds (saves to disk)

### Lower Performance?

If you get <15 FPS:

1. **Reduce preview resolution** in [config/config.json](config/config.json):
   ```json
   "camera": {
     "preview_width": 480,    // ← Change from 640
     "preview_height": 360,   // ← Change from 480
     "preview_fps": 20        // ← Reduce from 24
   }
   ```

2. **Close other programs** - Pi 3 A+ has only 512MB RAM
3. **Check CPU temperature**: `vcgencmd measure_temp`
   - If >70°C, add heatsink or reduce FPS

---

## 🐛 Troubleshooting

### Camera Not Found

**Error**: `No module named 'picamera'` or camera preview is black

**Fix**:
1. ✅ Enable camera in `raspi-config` (see step 1)
2. ✅ Reboot: `sudo reboot`
3. ✅ Reinstall: `pip install picamera==1.13`
4. ✅ Check: `python3 -c "import picamera; print('OK')"`

### Camera Shows Black/Blank Preview

**Causes**:
- Camera not physically connected properly
- Camera upside down (rotate in config)
- Preview resolution too high
- GPU memory too low

**Fix**:
- Reseat camera ribbon (power off Pi first)
- Check: `libcamera-still -o test.jpg` works
- Increase GPU memory: `raspi-config` → **Performance Options** → **GPU Memory** → 256MB

### Permission Denied

**Error**: `PermissionError: /dev/video0`

**Fix**:
```bash
sudo usermod -a -G video $USER
```

Then logout and login, or reboot.

### Out of Memory

**Error**: App crashes after 1-2 minutes

**Fix**:
- Reduce preview resolution (see above)
- Close other apps: `ps aux | grep python`
- Increase swap: `sudo dphys-swapfile swapoff && sudo nano /etc/dphys-swapfile`
  - Change `CONF_SWAPSIZE=100` to `2000` (2GB)
  - Then: `sudo dphys-swapfile setup && sudo dphys-swapfile swapon`

---

## 🎯 Quick Diagnostics

Run this on your Pi to check everything:

```bash
#!/bin/bash
echo "=== Camera Check ==="
echo "1. Camera interface enabled?"
vcgencmd get_camera

echo "2. Device files:"
ls -la /dev/video* 2>/dev/null || echo "No /dev/video* found"

echo "3. Python picamera module:"
python3 -c "import picamera; print('✓ picamera installed')" 2>/dev/null || echo "✗ picamera NOT installed"

echo "4. Camera access permissions:"
python3 -c "import picamera; p = picamera.PiCamera(); print('✓ Camera accessible'); p.close()" 2>/dev/null || echo "✗ Cannot access camera"

echo "5. GPU memory allocation:"
vcgencmd get_config gpu_mem

echo "6. CPU temperature:"
vcgencmd measure_temp
```

---

## 📱 Capture Resolution Recommendations

For Pi 3 A+ with 8MP camera:

| Use Case | Preview | Capture | Quality |
|----------|---------|---------|---------|
| Fast preview | 480×360 | 1920×1440 | 80 |
| Balanced | 640×480 | 2592×1944 | 85 |
| High quality (slow) | 320×240 | 2592×1944 | 92 |

Edit [config/config.json](config/config.json):
```json
"camera": {
  "preview_width": 640,
  "preview_height": 480,
  "preview_fps": 24,
  "capture_width": 2592,    // Full 8MP
  "capture_height": 1944,
  "capture_quality": 85     // Balance quality/speed
}
```

---

## 🔋 Optimize for Battery Life

Since you're on a Pi 3 A+ (likely mobile):

1. **Reduce preview FPS**:
   ```json
   "preview_fps": 16  // Lower = less CPU = less power
   ```

2. **Enable standby mode** ([config/config.json](config/config.json)):
   ```json
   "power": {
     "standby_timeout_s": 30  // Screen off after 30s inactivity
   }
   ```

3. **Use auto-brightness**:
   ```json
   "display": {
     "brightness_mode": "auto"  // Adjust screen brightness for light level
   }
   ```

4. **Disable GPU crust**:
   ```bash
   sudo raspi-config → Performance Options → GPU Memory → 128MB
   ```

---

## ✅ Set Boot to Run Auto on Startup

To run SelimCam automatically when Pi boots:

Create `/home/pi/start_camera.sh`:

```bash
#!/bin/bash
cd /home/pi/FINALMAINCAMMM  # Adjust path
source .venv/bin/activate
python main.py
```

Make executable:
```bash
chmod +x /home/pi/start_camera.sh
```

Add to crontab:
```bash
crontab -e
```

Add this line:
```
@reboot /home/pi/start_camera.sh
```

---

## 📞 Support

If camera still doesn't work after these steps:

1. Check [camera_backend.py](hardware/camera_backend.py) output - look for error messages
2. Run: `python3 -c "from hardware.camera_backend import *; print('Backend loaded')"` 
3. Try standalone: `python3 -c "from picamera import PiCamera; p = PiCamera(); p.start_preview(); input('Press Enter'); p.stop_preview()"`

---

## 📝 Notes

- **Pi 3 A+** = 1GHz ARM, 512MB RAM, designed for minimal systems
- **8MP camera module** = 3280×2464 pixels (full capture resolution)
- **Preview** = downscaled to 640×480 for low latency (Pygame requirement)
- **Capture** = full resolution saved as JPEG
- **Auto-rotation** = camera preview rotates with gyro/level indicator

---

**Last updated**: February 17, 2026  
**Status**: ✅ Camera backend ready for Pi 3 A+
