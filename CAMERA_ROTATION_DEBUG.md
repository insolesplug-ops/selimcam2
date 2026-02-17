# Camera Frame Rotation Debugging

## Problem
Camera frame displays in wrong orientation on 480x800 portrait display.

## Status
- Frame from IMX219 camera: **(480, 640, 3) - landscape**
- Display target: **480x800 - portrait**
- Need to find correct rotation to match orientation

## Architecture
```
[IMX219 Camera]
    ↓
    (480, 640, 3) - landscape from sensor
    ↓
[Frame Rotation Pipeline]
    ↓ (try all 4 modes)
    ↓
[pygame surface creation]
    ↓
[Scale to 480x800]
    ↓
[Display at portrait]
```

## Testing Guide

### Method 1: Test Each Rotation Mode

Edit `/home/pi/selimcam2/config/config.json` and add:

```json
{
  "camera": {
    "rotation_test": 0
  }
}
```

Valid values:
- **`0`** (default): 90° CW - `np.rot90(frame, k=-1)`
- **`1`**: 90° CCW - `np.rot90(frame, k=1)`
- **`2`**: 180° - `np.rot90(frame, k=2)`
- **`3`**: No rotation - `frame` (unchanged)

### Testing Steps

```bash
# 1. Pull latest code
cd ~/selimcam2
git pull origin main

# 2. Edit config to test rotation_test=0 first
nano config/config.json
# Add: "camera": {"rotation_test": 0},

# 3. Restart app
sudo systemctl restart selimcam

# 4. Watch logs with rotation debug output
sudo journalctl -u selimcam -f | grep -E '\[FRAME\]|\[RENDER\]|\[CAMERA\]'

# Look for:
# [FRAME] Rotation mode 0 (90° CW): (480, 640, 3) → (640, 480, 3)
# [FRAME] After swapaxes: (480, 640, 3)
# [FRAME] pygame surface: (480, 640)
# [FRAME] Scaling (480, 640) → (480, 800)
# [FRAME] ✓ Surface ready: (480, 800)

# 5. Check visual result on Pi display - is camera correct orientation?

# 6. If NOT correct, try next value:
# rotation_test=1, restart, check again
# rotation_test=2, restart, check again
# rotation_test=3, restart, check again

# 7. When CORRECT, confirm which value worked
```

## Log Output Format

```
[CAMERA] get_preview_frame() → shape=(480, 640, 3), dtype=uint8
[RENDER] Camera preview: surface=False, frame=True
[RENDER] Converting numpy frame to surface
[FRAME] Rotation mode 0 (90° CW): (480, 640, 3) → (640, 480, 3)
[FRAME] After swapaxes: (480, 640, 3)
[FRAME] pygame surface: (480, 640)
[FRAME] Scaling (480, 640) → (480, 800)
[FRAME] ✓ Surface ready: (480, 800)
[RENDER] ✓ Blitting frame surface (480, 800) to screen
```

## Expected Behavior

When you find the correct rotation:
1. Camera image appears upright (not sideways or upside-down)
2. Objects in camera view match what you see in the real world
3. No stretching or compression artifacts

## Potential Issues

### Issue: Frame appears sideways (rotated 90°)
- Try next rotation mode (0→1, 1→2, 2→3, 3→0)

### Issue: Frame appears upside-down (rotated 180°)
- Check if rotation_test=2 gives correct orientation
- If so, the sensor might need a different setup

### Issue: Frame appears backwards/mirrored
- Not a rotation issue - may need horizontal flip
- Check config for any mirror settings

### Issue: Frame is blank or black
- Camera may not be started
- Check: `sudo vcgencmd get_camera` should show "supported=1 detected=1"
- Check earlier logs for camera initialization errors

## KMS Rotation Context

The display uses:
- `SDL_VIDEO_KMSDRM_ROTATION="1"` (90° CW at kernel level)
- This rotates the entire SDL 480x800 surface to 800x480 for the 800x480 physical display

Camera frame rotation is **separate** and only affects the camera image pixels.

## Hardware Details

- **Camera**: IMX219 CSI (8MP)
- **Configuration**: 640×480 landscape preview via Picamera2
- **Display**: Waveshare 4.3" DSI (800×480 native landscape)
- **App**: 480×800 portrait target via KMS 90° CW

## Success Criteria

Once you're confident which rotation works, report back:
- ✅ rotation_test value that works: **`X`**
- ✅ Camera image appears correct
- ✅ No artifacts or stretching

Then we'll make that the permanent default.
