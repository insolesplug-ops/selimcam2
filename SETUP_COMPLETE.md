# SelimCam v2.0 - Setup & Configuration Complete ✅

## What's Been Fixed

### 1. **Pygame Installation** ✅
- Installed `pygame==2.x.x` to your virtual environment
- App now runs without `ModuleNotFoundError`

### 2. **Screen Rotation & Dimensions** ✅
**Your app is correctly configured for 480 × 800 (portrait mode)**:
- Width: 480 pixels
- Height: 800 pixels  
- Orientation: Portrait (vertical)
- Display mode: HWSURFACE + DOUBLEBUF for optimal performance

The screen dimensions are set in two places:
- [config/config.json](config/config.json) - `display.width: 480, display.height: 800`
- [hitboxes_ui.json](hitboxes_ui.json) - `screen_size: [480, 800]`

### 3. **Overlay Visibility** ✅
**Enhanced overlay rendering in [scenes/camera_scene.py](scenes/camera_scene.py)**:

**Key improvements made**:
- ✅ Overlay scaling: Automatically scales PNG overlays to 480×800 if dimensions don't match
- ✅ Rendering order fixed: Overlay now renders **LAST** (on top) to ensure visibility
- ✅ Proper blending: Uses `pygame.BLEND_ALPHA_SDL2` for correct transparency
- ✅ Info bar optimization: Top info bar renders BEFORE overlay so flash buttons are visible

**Render stack (bottom to top)**:
1. Camera preview frame
2. Filters & zoom applied
3. Grid overlay (if enabled)
4. Level indicator (if enabled)
5. Top info bar (battery, time)
6. **Flash mode overlay** ← **NOW VISIBLE ON TOP**
7. FPS counter

### 4. **Hitbox Configuration Documentation** ✅
Created comprehensive guide: [HITBOX_AND_OVERLAY_CONFIG.md](HITBOX_AND_OVERLAY_CONFIG.md)

**Quick reference**:
- **Main hitbox file**: [hitboxes_ui.json](hitboxes_ui.json) (root directory)
- **Overlay files**: [assets/ui/](assets/ui/) directory
- **Bottom buttons** (y=720-800):
  - Settings: x=80-190
  - Flash: x=205-315
  - Gallery: x=330-440

---

## 📁 Where to Configure Everything

### Hitboxes (Touch-Sensitive Areas)
**File**: [hitboxes_ui.json](hitboxes_ui.json)

Edit the `x`, `y`, `w`, `h` values to reposition buttons:
```json
{
  "id": "settings",
  "x": 80,      // ← Adjust these coordinates
  "y": 720,
  "w": 110,
  "h": 80,
  "action": "go_to_settings"
}
```

### Visual Overlays (UI Graphics)
**Directory**: [assets/ui/](assets/ui/)

Replace PNG files to customize appearance:
- `flash off.png` - UI when flash is OFF
- `flash on.png` - UI when flash is ON
- `flash automatically.png` - UI when flash is AUTO
- `settings.png` - Settings scene UI
- `gallery.png` - Gallery scene UI

**Requirements**:
- Size: 480 × 800 pixels
- Format: PNG with alpha channel (transparency)
- The transparent areas let the camera preview show through

### General Settings
**File**: [config/config.json](config/config.json)

Configure:
- Display dimensions (currently 480×800)
- UI info display mode (minimal/extended/off)
- Camera preview resolution and FPS
- Flash auto-threshold
- Filter and zoom settings

---

## 🎮 Testing the App

### Start the app:
```bash
python3 main.py
```

### Simulator Controls:
| Key | Control |
|-----|---------|
| `MOUSE` | Click to test hitboxes (bottom button row) |
| `SPACE` | Capture photo |
| `G` | Toggle grid overlay |
| `L` | Toggle level indicator |
| `F` | Cycle flash mode (off → on → auto) |
| `LEFT/RIGHT` | Rotate encoder (zoom) |
| `Q/W` | Adjust tilt |
| `+/-` | Adjust brightness |
| `S` | Capture (alternate) |
| `ESC` | Exit/Back |

### Test Hitboxes:
1. Run the app
2. Click near the **bottom of the screen** (y=700-800)
3. Should see console output: `Hitbox hit: {id} -> {action}`
4. Clicking Settings button → Opens Settings
5. Clicking Flash button → Cycles flash mode
6. Clicking Gallery button → Opens Gallery

---

## 📊 Current Configuration Summary

```
Screen:         480 × 800 pixels (portrait)
Preview FPS:    24 FPS (configurable)
Display Mode:   Simulator on macOS
Overlay:        PNG images with transparency blending
Hitboxes:       5-point hit detection system
Camera Preview: 640 × 480 (scaled to 480 × 800 display)
```

---

## 🔧 Code Changes Made

### Modified Files:

1. **[scenes/camera_scene.py](scenes/camera_scene.py)** - Line 268-333
   - Fixed overlay rendering order
   - Added overlay scaling to dimensions
   - Ensured overlay renders on top of all elements
   - Fixed info bar to render before overlay

### No Breaking Changes:
- ✅ All existing functionality preserved
- ✅ Backward compatible with config files
- ✅ Hitbox system unchanged
- ✅ Filter and zoom systems intact

---

## ✅ Verification Checklist

- [x] Pygame installed successfully
- [x] App launches without errors
- [x] Screen displays at 480 × 800
- [x] Overlay visible on-screen  
- [x] Hitbox coordinates documented
- [x] Configuration files identified
- [x] Simulator controls working
- [x] Documentation created

---

## 💡 Pro Tips

### To adjust hitbox positions:
1. Open [hitboxes_ui.json](hitboxes_ui.json)
2. Modify `x`, `y`, `w`, `h` values
3. Restart app - changes take effect immediately
4. Use simulator mouse clicks to test

### To customize overlay graphics:
1. Create 480×800 PNG with alpha channel
2. Replace file in [assets/ui/](assets/ui/)
3. Restart app - new overlay loads immediately

### To rename hitboxes:
- Edit `"id"` field in [hitboxes_ui.json](hitboxes_ui.json)
- Update `action` field to valid action (go_to_settings, cycle_flash, etc.)

### To add new buttons:
1. Add hitbox entry to [hitboxes_ui.json](hitboxes_ui.json)
2. Define handler in [main.py](main.py) `_execute_hitbox_action()` method
3. Ensure overlay PNG has visual UI element at those coordinates

---

## 📖 Additional Documentation

- [HITBOX_AND_OVERLAY_CONFIG.md](HITBOX_AND_OVERLAY_CONFIG.md) - Complete configuration guide
- [00_README_START_HERE.md](00_README_START_HERE.md) - Project overview
- [config/config.json](config/config.json) - All configurable settings
- [hitboxes_ui.json](hitboxes_ui.json) - Hitbox definitions

---

## 🚀 What's Next

The app is ready to use! You can now:

1. **Test the simulator** with mouse clicks and keyboard
2. **Customize hitboxes** by editing `hitboxes_ui.json`
3. **Replace overlays** with custom 480×800 PNG files
4. **Deploy to Raspberry Pi** with native hardware backends

For any modifications to hitboxes or UI overlays, refer to [HITBOX_AND_OVERLAY_CONFIG.md](HITBOX_AND_OVERLAY_CONFIG.md) for detailed instructions.

---

**Created**: February 17, 2026  
**Status**: ✅ Ready for testing and deployment
