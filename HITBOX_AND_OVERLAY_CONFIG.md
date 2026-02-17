# Hitbox & Overlay Configuration Guide

## Overview
The SelimCam app uses a hitbox system for touch-based UI interactions and PNG overlays for the visual UI. This guide explains where to manually configure both.

---

## ⚙️ Hitbox Configuration

### Main Location: `hitboxes_ui.json` (Root Directory)

The hitbox system is configured in [hitboxes_ui.json](hitboxes_ui.json) at the project root. This file defines interactive areas for each scene.

### File Structure

```json
{
  "main": {
    "screen_size": [480, 800],
    "overlay": "flash off.png",
    "hitboxes": [
      {
        "id": "settings",
        "x": 80,
        "y": 720,
        "w": 110,
        "h": 80,
        "action": "go_to_settings"
      },
      {
        "id": "flash",
        "x": 205,
        "y": 720,
        "w": 110,
        "h": 80,
        "action": "cycle_flash"
      },
      {
        "id": "gallery",
        "x": 330,
        "y": 720,
        "w": 110,
        "h": 80,
        "action": "go_to_gallery"
      }
    ]
  },
  "settings": { ... },
  "gallery": { ... }
}
```

### Key Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `id` | Unique identifier for the hitbox | `"settings"`, `"flash"`, `"gallery"` |
| `x` | X position (left edge) in pixels | `80` |
| `y` | Y position (top edge) in pixels | `720` |
| `w` | Width of hitbox | `110` |
| `h` | Height of hitbox | `80` |
| `action` | Action to execute on click | `"go_to_settings"`, `"cycle_flash"`, `"go_to_gallery"` |

### Available Actions

- `go_to_settings` - Navigate to settings scene
- `go_to_gallery` - Navigate to gallery scene
- `go_to_main` - Return to main camera scene
- `cycle_flash` - Cycle flash mode (off → on → auto → off)

### Screen Dimensions

The app runs at **480 × 800 pixels** (portrait orientation):
- Width: 480px (horizontal)
- Height: 800px (vertical)
- Bottom button row: y=720 to y=800 (80px tall)
- Three buttons: 80-190px, 195-305px, 310-420px (110px each, with spacing)

### How to Modify Hitboxes

1. Open [hitboxes_ui.json](hitboxes_ui.json)
2. Find the scene you want to modify (`"main"`, `"settings"`, or `"gallery"`)
3. Adjust the `x`, `y`, `w`, `h` values to match your desired button positions
4. Save the file - changes take effect immediately on next app restart

#### Visual Example:
```
480px width
├─ x=80     x=205     x=330
│  ┌─────────────────────────────┐
│  │ Settings │ Flash │ Gallery  │
│  │ (80-190) │(195-305)│(310-420)│
│  └─────────────────────────────┘
   y=720 to y=800 (80px height)
```

### Debug Tips

- Use the simulator controls to test:
  - `MOUSE`: Click and drag to test hitboxes
  - Press buttons at y=720-800 to test bottom buttons
- Check the console for "Hitbox hit" messages when testing
- Hitbox coordinates are **strict**: `x <= mx < x+w AND y <= my < y+h`

---

## 🎨 Overlay Configuration

### Overlay Files Location: `assets/ui/` Directory

UI overlays are stored in [assets/ui/](assets/ui/):
- `flash off.png` - Bottom UI bar when flash is OFF
- `flash on.png` - Bottom UI bar when flash is ON
- `flash automatically.png` - Bottom UI bar when flash is AUTO
- `settings.png` - Settings scene overlay
- `gallery.png` - Gallery scene overlay
- `boot_logo.png` - Boot screen logo

### Overlay Properties

- **Size**: 480 × 800 pixels (full screen)
- **Format**: PNG with transparency (RGBA)
- **Color**: Dark background with transparent areas for camera preview
- **Positioning**: Rendered with `pygame.BLEND_ALPHA_SDL2` for proper transparency blending

### How to Replace or Create Overlays

1. **Locate the overlay files** in [assets/ui/](assets/ui/)
2. **Create replacement PNG file** with:
   - Dimensions: **480 × 800 pixels**
   - Format: PNG with alpha channel (transparency)
   - Dark UI elements (typically dark buttons/bars)
   - Transparent areas where the camera preview shows through
3. **Replace the file** (e.g., `flash off.png`) with your new version
4. **Restart the app** - new overlay will be used immediately

### Overlay Rendering Order

Overlays are rendered **on top** of the camera preview in this order:
1. Camera preview frame (with applied filters and zoom)
2. Grid overlay (if enabled with `G` key)
3. Level indicator (if enabled with `L` key)
4. Top info bar (battery, time, optional debug info)
5. **Flash mode overlay** ← **LAST** (on top of everything)
6. FPS counter (debug, if fps > 0)

### Screen Dimensions Reference

```
    0 ─────────────────────────────────── 480
    │                                      │
    │                                      │
    │         Camera Preview Area          │
    │         Shows live feed from         │
    │         camera with filters          │
    │                                      │
  720 ────────────────────────────────────│
    │  [Settings]  [Flash]  [Gallery]      │
    │                                      │
  800 ────────────────────────────────────│
```

---

## 🔧 Related Configuration Files

### `config/config.json`
Controls general app settings:
- Display dimensions: `display.width` (480), `display.height` (800)
- UI settings: `ui.info_display` (minimal/extended/off)
- Camera settings: preview resolution, FPS, capture settings
- Flash settings: auto threshold, pulse duration
- Filter and zoom settings

### `config/hitboxes_main.json`
Alternative hitbox file (legacy, currently uses `hitboxes_ui.json`).

---

## 🎮 Simulator Controls

For testing on macOS:

| Key | Action |
|-----|--------|
| `MOUSE` | Touch simulation (click to test hitboxes) |
| `SPACE` | Shutter/capture photo |
| `G` | Toggle grid overlay |
| `L` | Toggle level indicator |
| `F` | Cycle flash mode (off → on → auto) |
| `LEFT/RIGHT` | Rotate encoder (zoom) |
| `Q/W` | Adjust tilt |
| `+/-` | Adjust brightness/lux |
| `ESC` | Exit/Back |

---

## 📱 Hitbox Example: Bottom Button Row

Current configuration in `hitboxes_ui.json`:

```json
{
  "id": "settings",
  "x": 80,
  "y": 720,
  "w": 110,
  "h": 80,
  "action": "go_to_settings"
},
{
  "id": "flash",
  "x": 205,
  "y": 720,
  "w": 110,
  "h": 80,
  "action": "cycle_flash"
},
{
  "id": "gallery",
  "x": 330,
  "y": 720,
  "w": 110,
  "h": 80,
  "action": "go_to_gallery"
}
```

**Visual Layout**:
- Left button (Settings): x=80-190, y=720-800
- Center button (Flash): x=205-315, y=720-800
- Right button (Gallery): x=330-440, y=720-800
- Total width: 480px, spacing: ~15px between buttons

---

## 🐛 Troubleshooting

### Hitboxes not responding
- Ensure coordinates are within screen bounds (0-480 width, 0-800 height)
- Check that `action` value is valid (see Available Actions above)
- Restart the app after modifying `hitboxes_ui.json`
- Use simulator mouse click to test precise coordinates

### Overlay not visible
- Ensure PNG file exists in [assets/ui/](assets/ui/)
- Check file size is 480×800 pixels
- Confirm PNG has alpha channel (transparency)
- Verify flash mode is set correctly (`off`, `on`, or `auto`)

### Text misalignment
- Top info bar positioning is in [scenes/camera_scene.py](scenes/camera_scene.py) line 370+
- Modify pixel offsets in `_render_info_bar()` method if needed

---

## 📝 Code References

### Loading Hitboxes (main.py)
```python
hitboxes_data = load_hitboxes()  # Loads from hitboxes_ui.json
self.hitbox_engine = HitboxEngine(hitboxes_data)
```

### Handling Hitbox Clicks (main.py)
```python
result = self.hitbox_engine.hit_test(scene_name, mx, my)
if result:
    hitbox_id, action = result
    self._execute_hitbox_action(action)
```

### Rendering Overlays (camera_scene.py)
```python
flash_overlay = self.flash_overlays.get(flash_mode)
if flash_overlay:
    screen.blit(flash_overlay, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
```

---

## ✅ Quick Start Checklist

- [ ] 480 × 800 screen size set correctly
- [ ] Bottom hitboxes positioned at y=720-800
- [ ] All hitbox action names are valid
- [ ] Overlay PNGs are 480×800 with transparency
- [ ] `hitboxes_ui.json` is in root directory
- [ ] `assets/ui/` contains all overlay PNG files
- [ ] Tested with simulator mouse clicks
