# SelimCam Shutdown Button Setup Guide

## Overview

The SelimCam Settings menu now includes a **"Shutdown Device"** button that gracefully shuts down the Raspberry Pi from the app UI.

When tapped:
1. Shows "Shutting down..." message with haptic feedback
2. Stops all background threads safely
3. Saves all configuration
4. Executes `sudo shutdown -h now`
5. Adafruit Power Switch GPIO 4 kernel overlay cuts power

**This requires a one-time sudoers configuration on your Pi.**

---

## Prerequisites

- Raspberry Pi 3A+ (or compatible)
- SelimCam v2.0 app running
- User: `pi` (standard Raspberry Pi user)
- Sudo access to run setup script

---

## Installation Steps

### Step 1: Copy the Setup Script

The `setup_shutdown_sudo.sh` file was created in the SelimCam root directory. On your Pi:

```bash
# If pulled from GitHub:
cd /home/pi/selimcam2
git pull  # Gets latest code with setup script

# Verify script exists:
ls -la setup_shutdown_sudo.sh
```

### Step 2: Run the Setup Script

Run this command **ONCE** on your Pi to configure passwordless sudo for shutdown:

```bash
sudo bash /home/pi/selimcam2/setup_shutdown_sudo.sh
```

**Expected Output:**
```
==================================================
SelimCam Shutdown Sudo Setup
==================================================

Creating sudoers configuration at: /etc/sudoers.d/selimcam-shutdown
Content: pi ALL=(ALL) NOPASSWD: /sbin/shutdown

✓ Sudoers file created successfully
✓ Sudoers file syntax is valid

==================================================
Setup Complete!
==================================================
The 'pi' user can now run: sudo shutdown -h now
without being prompted for a password.

The SelimCam 'Shutdown Device' button will now work.
==================================================
```

### Step 3: Verify Configuration

Check that the sudoers file was created correctly:

```bash
sudo cat /etc/sudoers.d/selimcam-shutdown
```

**Expected Output:**
```
pi ALL=(ALL) NOPASSWD: /sbin/shutdown
```

Check file permissions:
```bash
ls -l /etc/sudoers.d/selimcam-shutdown
```

**Expected Output:**
```
-r--r-----  1 root root 47 [date] /etc/sudoers.d/selimcam-shutdown
```

---

## Usage

### On the SelimCam App

1. Open **Settings** menu (tap Settings button)
2. Scroll down to see **"Shutdown Device"** option
3. Tap the option
4. App shows "Shutting down..." message
5. Haptic feedback plays (if available)
6. Pi shuts down gracefully
7. Adafruit Power Switch cuts power automatically (GPIO 4 kernel overlay)

### From Command Line (Testing)

Test the shutdown command works without password:

```bash
# This should execute without prompting for password
sudo shutdown -h now
```

If it prompts for a password, the setup script didn't work. Try running it again:

```bash
sudo bash /home/pi/selimcam2/setup_shutdown_sudo.sh
```

---

## How It Works

### App Flow

**Settings Menu → "Shutdown Device" Tap:**
```
SettingsScene._activate_setting()
  └── Detects type='action' and action='shutdown'
      └── Calls self.app.request_shutdown()
          └── App.request_shutdown()
              └── PowerManager.request_shutdown()
                  └── Sets state to STATE_SHUTDOWN

Main Loop (every frame):
  └── Checks if PowerManager.is_shutdown()
      └── Calls _execute_shutdown()
          ├── Fills screen black
          ├── Renders "Shutting down..." text
          ├── Plays haptic feedback
          ├── Waits 1.5 seconds
          ├── Stops sensor thread
          ├── Saves config
          ├── Executes: subprocess.call(["sudo", "shutdown", "-h", "now"])
          └── Exits main loop and cleanup
```

### Sudoers Configuration

The `setup_shutdown_sudo.sh` script creates `/etc/sudoers.d/selimcam-shutdown` with:

```
pi ALL=(ALL) NOPASSWD: /sbin/shutdown
```

This allows the `pi` user to run `/sbin/shutdown` with `sudo` **without** being prompted for a password.

**Security Notes:**
- Only allows the `shutdown` command (not full sudo without password)
- Specific to `/sbin/shutdown` (only path that can run this)
- Can be revoked by deleting `/etc/sudoers.d/selimcam-shutdown`

### Hardware Power Cut

The Adafruit Push-button Power Switch is wired:
- **GPIO 4**: Connected to power switch
- **Kernel Overlay**: `gpio-poweroff` configured to cut power when Pi shuts down

This ensures power is completely cut after the OS (systemd) shutdown sequence.

---

## Troubleshooting

### "Permission denied" When Tapping Shutdown

**Problem:** Tap shows no effect or error

**Solution:** Verify sudoers configuration:
```bash
sudo cat /etc/sudoers.d/selimcam-shutdown
```

If empty or missing, re-run setup:
```bash
sudo bash /home/pi/selimcam2/setup_shutdown_sudo.sh
```

### Script Says "sudoers file has syntax errors"

**Problem:** Setup script fails with syntax error

**Solution:**
1. Check if file was partially created:
   ```bash
   sudo ls -la /etc/sudoers.d/selimcam-shutdown
   ```

2. Delete it and try again:
   ```bash
   sudo rm -f /etc/sudoers.d/selimcam-shutdown
   sudo bash /home/pi/selimcam2/setup_shutdown_sudo.sh
   ```

### Shutdown Button Not Appearing in Settings

**Problem:** Settings menu doesn't show "Shutdown Device" option

**Solution:** Verify you have the latest code:
```bash
cd /home/pi/selimcam2
git pull
```

Restart the app:
```bash
sudo systemctl restart selimcam
```

### Haptic Feedback Doesn't Play During Shutdown

**Problem:** Shutdown works but no buzzer/vibration

**Solution:** This is normal if:
- Haptic hardware not available
- Haptic disabled in config
- Device doesn't have haptic

Check haptic availability in logs:
```bash
sudo journalctl -u selimcam -n 50 | grep -i haptic
```

### Power Doesn't Cut After Shutdown

**Problem:** Pi shuts down (terminal shows "Power down") but power doesn't cut

**Solution:** Verify Adafruit Power Switch setup:
```bash
# Check if kernel overlay is active
ls -la /sys/class/gpio/gpio4/

# Verify in /boot/firmware/config.txt:
sudo grep gpio-poweroff /boot/firmware/config.txt
```

Should show:
```
dtoverlay=gpio-poweroff,gpiopin=4
```

If missing, add and reboot:
```bash
echo "dtoverlay=gpio-poweroff,gpiopin=4" | sudo tee -a /boot/firmware/config.txt
sudo reboot
```

---

## Advanced: Manual Sudoers Setup (If Script Fails)

If the script fails for any reason, manually create the sudoers file:

```bash
# Edit sudoers safely
sudo visudo -f /etc/sudoers.d/selimcam-shutdown
```

Add this line:
```
pi ALL=(ALL) NOPASSWD: /sbin/shutdown
```

Save (`Ctrl+O`, Enter, `Ctrl+X` in nano).

Test:
```bash
sudo shutdown -h now
```

---

## Reverting/Disabling Shutdown Button

### Remove Passwordless Sudo Access

```bash
sudo rm /etc/sudoers.d/selimcam-shutdown
```

Shutdown button will still appear in Settings, but tapping it will either:
- Hang waiting for password (no terminal open)
- Fail with permission error (if stdin closed)

### Disable Shutdown from Settings Code

Edit `scenes/settings_scene.py` and remove or comment out the shutdown item in `_build_settings_list()`:

```python
# Removed:
# {
#     'label': 'Shutdown Device',
#     'type': 'action',
#     'action': 'shutdown',
#     'description': 'Gracefully shut down Pi'
# },
```

---

## Testing Checklist

- [ ] Ran setup script: `sudo bash setup_shutdown_sudo.sh`
- [ ] Verified sudoers file created: `sudo cat /etc/sudoers.d/selimcam-shutdown`
- [ ] Tested manual shutdown: `sudo shutdown -h now` (no password prompt)
- [ ] SelimCam Settings menu shows "Shutdown Device" option
- [ ] Tapped shutdown button in Settings
- [ ] "Shutting down..." message appeared
- [ ] Haptic feedback played (if available)
- [ ] Pi executed `shutdown` command
- [ ] Power was cut by Adafruit switch

---

## Code Changes Made

### Files Modified

1. **main.py**
   - Added `import subprocess`
   - Added `request_shutdown()` method to App class
   - Updated `_execute_shutdown()` to use `subprocess.call()` instead of `os.system()`
   - Better error handling during shutdown

2. **scenes/settings_scene.py**
   - Added "Shutdown Device" action item to settings list
   - Updated `_activate_setting()` to handle type='action'
   - Calls `self.app.request_shutdown()` when tapped

### Files Created

1. **setup_shutdown_sudo.sh**
   - Configures passwordless sudo for shutdown command
   - Creates `/etc/sudoers.d/selimcam-shutdown`
   - Validates sudoers syntax
   - Run once on Raspberry Pi

2. **SHUTDOWN_SETUP.md** (this file)
   - Complete setup guide
   - Troubleshooting
   - How it works
   - Hardware integration details

---

## Security Considerations

### What We Do Allow
- `sudo shutdown -h now` only (halt/power down)
- No other sudo commands
- Specific path: `/sbin/shutdown`

### What We Don't Allow
- Full sudo without password
- Other system commands
- Unlimited privilege escalation

### Best Practices
- Only run on trusted networks
- Keep SelimCam code updated
- Regularly audit sudoers: `sudo ls -la /etc/sudoers.d/`

---

## Support

If you encounter issues:

1. Check app logs:
   ```bash
   sudo journalctl -u selimcam -n 100 | grep -i shutdown
   ```

2. Run setup script again
3. Check sudoers syntax
4. Clear screen and restart app
5. Power cycle Pi and try again

---

**SelimCam v2.0 - Shutdown Button Ready!**

Last Updated: 2024
