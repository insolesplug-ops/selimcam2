# SelimCam Shutdown Button - Deployment Checklist for Raspberry Pi

## Quick Start - 3 Steps

### Step 1: Update Code
```bash
cd /home/pi/selimcam2
git pull
```

### Step 2: Run Setup Script (ONCE)
```bash
sudo bash setup_shutdown_sudo.sh
```

### Step 3: Restart App and Test
```bash
sudo systemctl restart selimcam
# OR manually restart the app

# Then in the app:
# - Open Settings menu
# - Scroll to "Shutdown Device"
# - Tap to test shutdown
```

---

## What Changed

**Recent Commits:**
- ✅ **9896eff** - Add Shutdown Device button to Settings menu  
- ✅ **9f6709f** - Make button overlays MUCH LARGER (75x75px)  
- ✅ **fcda1d1** - Invert touch mapping & center buttons  
- ✅ **a0f2079** - Hide debug overlays (FPS/ROTATION text)  

**New Files:**
- `setup_shutdown_sudo.sh` - Run once to enable passwordless sudo
- `SHUTDOWN_SETUP.md` - Complete setup guide with troubleshooting

**Modified Files:**
- `main.py` - Added `request_shutdown()`, improved `_execute_shutdown()`
- `scenes/settings_scene.py` - Added shutdown button to settings menu

---

## Expected Behavior

When you tap "Shutdown Device" in Settings:

1. Screen goes black with white "Shutting down..." text
2. Haptic feedback plays (buzz/vibration)
3. After 1.5 seconds, Pi executes shutdown
4. Adafruit Power Switch cuts power automatically

---

## Verify It Works

**Test 1: Sudoers Configuration**
```bash
sudo cat /etc/sudoers.d/selimcam-shutdown
# Should show: pi ALL=(ALL) NOPASSWD: /sbin/shutdown
```

**Test 2: Manual Shutdown (use with caution!)** 
```bash
# This will shutdown in 60 seconds
# Cancel with: shutdown -c
sudo shutdown -h +1
```

**Test 3: App Settings Menu**
1. Restart app: `sudo systemctl restart selimcam`
2. Tap Settings button in camera view
3. Scroll down - should see "Shutdown Device" at bottom
4. Proceed with caution (will actually shutdown!)

---

## Important Notes

⚠️ **CRITICAL:**
- Must run setup script ONCE before shutdown works: `sudo bash setup_shutdown_sudo.sh`
- Shutdown button will power down the Pi immediately when tapped
- No confirmation dialog - tap only when ready to shut down
- After shutdown, power is cut but you won't see the Adafruit switch do anything

🔧 **If shutdown button doesn't appear:**
1. Pull latest code: `git pull`
2. Restart app with: `sudo systemctl restart selimcam`

🔧 **If tapping does nothing:**
1. Run setup script: `sudo bash setup_shutdown_sudo.sh`
2. Restart app: `sudo systemctl restart selimcam`
3. Try again

🔧 **If power doesn't cut after shutdown:**
- This is normal on some setups
- Adafruit switch should cut power automatically via GPIO 4
- If it doesn't, check kernel overlay is active: `sudo grep gpio-poweroff /boot/firmware/config.txt`

---

## Production Readiness Checklist

- [x] Code syntax validated  
- [x] Error handling for shutdown failures  
- [x] Graceful cleanup (threads, config)  
- [x] User feedback ("Shutting down..." message)  
- [x] Haptic feedback (if available)  
- [x] Setup script for sudo config  
- [x] Complete documentation  
- [x] Git commits and push  

## Ready for Testing on Pi! ✅

**Next Steps:**
1. Pull code on Pi: `git pull`
2. Run: `sudo bash setup_shutdown_sudo.sh`
3. Test in app: Settings → Shutdown Device

---

**Version: SelimCam v2.0**  
**Last Updated:** 2024
