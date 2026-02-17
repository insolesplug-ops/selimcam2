# Kamera-Einstellungen Anleitung

Diese Datei erklärt wie du die Kamera-Helligkeit und andere Parameter im Code einstellen kannst.

## 1. PREVIEW-FPS (Smoothness)

**Datei:** `config/config.json`

```json
"camera": {
  "preview_fps": 24    // Erhöhe auf 30 für flüssiger, senke auf 10 für sparsamer
}
```

- 10 FPS = sehr sparsam, abgehackt
- 24 FPS = Standard (aktuell)
- 30 FPS = flüssig aber mehr CPU/Battery

## 2. HELLIGKEIT (Brightness)

**Datei:** `config/config.json`

```json
"display": {
  "brightness_mode": "auto",      // "auto", "dark", "medium", "bright"
  "brightness_dark": 40,          // 0-255 (dunkle Einstellung)
  "brightness_medium": 120,       // 0-255 (normale Einstellung)
  "brightness_bright": 220        // 0-255 (helle Einstellung)
}
```

Werte:
- 0-50 = sehr dunkel (Akku spart)
- 100-150 = normal
- 200-255 = sehr hell (verschlingt Akku)

## 3. FILTER (Live-Preview)

**Datei:** `config/config.json`

```json
"filter": {
  "active": "none",     // "none", "bw", "sepia", "cool", "warm", "vivid"
  "iso_fake": 400       // Fake ISO Simulation (100-1600)
}
```

Im **Settings Menu** (auf der App) kannst du mitPoint-and-Drag einen Filter wählen:
- `none` = kein Filter
- `bw` = Schwarz-Weiß
- `sepia` = Sepia/Braun Ton
- `cool` = blauer/kalter Ton
- `warm` = oranger/warmer Ton
- `vivid` = lebendiger/gesättigter

Die Änderungen sind **SOFORT live** im Preview!

## 4. KAMERA AUFLÖSUNG

**Datei:** `config/config.json`

```json
"camera": {
  "preview_width": 640,       // Preview Resolution (640x480 native libcamera)
  "preview_height": 480,
  "capture_width": 2592,      // Foto-Auflösung (max 8MP)
  "capture_height": 1944,
  "capture_quality": 92       // 0-100 (JPEG quality)
}
```

Hints:
- Preview ist immer 640x480 für Performance
- Fotos können bis 2592x1944 sein (8MP)
- Quality 92 = sehr gut, 85 = gut, 75 = ok

## 5. ZOOM

**Datei:** `config/config.json`

```json
"zoom": {
  "current": 1.0,      // Start zoom level (1.0 = kein Zoom)
  "min": 1.0,          // Minimum Zoom
  "max": 2.5,          // Maximum Zoom (2.5x = 2.5fach)
  "step": 0.05,        // Schrittgröße pro Drehung
  "smooth_factor": 0.25  // Smoothness (0.0-1.0, höher = smoother)
}
```

## 6. FLASH-EINSTELLUNG

**Datei:** `config/config.json`

```json
"flash": {
  "mode": "off",              // "off", "on", "auto"
  "auto_threshold_lux": 60,   // Lux-Level für Auto-Flash
  "pulse_duration_ms": 120    // Flash-Dauer in Millisekunden
}
```

- `off` = Flash aus
- `on` = Flash immer an
- `auto` = Flash nur wenn dunkel (< 60 Lux)

## 7. BATTERY + POWER

**Datei:** `config/config.json`

```json
"power": {
  "standby_timeout_s": 10,      // Standby nach 10 Sekunden Inaktivität
  "shutdown_long_press_s": 1.8  // Long-Press für Shutdown (1.8s)
}
```

## 8. HAPTIC FEEDBACK

**Datei:** `config/config.json`

```json
"haptic": {
  "enabled": true,   // true/false
  "tick": 1,         // Normales Tap (0-100)
  "confirm": 10,     // Bestätigung (0-100)
  "capture": 47,     // Foto-Feedback (0-100)
  "error": 14        // Fehler-Feedback (0-100)
}
```

Setze auf 0 um zu disablen, höher = stärker.

## 9. FOTO-SPEICHER

**Datei:** `config/config.json`

```json
"storage": {
  "photos_dir": "camera_app_data/photos",  // Speicherort
  "max_photos": 500   // Max Fotos bevor älteste gelöscht werden
}
```

## 10. OVERLAY & UI

**Datei:** `config/config.json`

```json
"ui": {
  "grid_enabled": false,        // true = Gitter-Overlay anzeigen
  "level_enabled": false,       // true = Wasserwaage anzeigen
  "info_display": "minimal",    // "off", "minimal", "extended"
  "freeze_duration_ms": 700,    // Freeze Frame nach Foto (ms)
  "touch_debug_overlay": true   // true = roten Punkt zeigen beim Touch
}
```

## BEISPIEL: PERFEKT CALIBRIERTE EINSTELLUNGEN

```json
{
  "camera": {
    "preview_width": 640,
    "preview_height": 480,
    "preview_fps": 24,
    "capture_width": 2592,
    "capture_height": 1944,
    "capture_quality": 92,
    "rotation_test": 0
  },
  "display": {
    "width": 480,
    "height": 800,
    "brightness_mode": "auto",
    "brightness_dark": 60,
    "brightness_medium": 140,
    "brightness_bright": 230
  },
  "filter": {
    "active": "none",
    "iso_fake": 400
  },
  "flash": {
    "mode": "auto",
    "auto_threshold_lux": 80,
    "pulse_duration_ms": 150
  },
  "ui": {
    "grid_enabled": false,
    "level_enabled": false,
    "info_display": "minimal",
    "freeze_duration_ms": 500,
    "touch_debug_overlay": false
  },
  "zoom": {
    "current": 1.0,
    "min": 1.0,
    "max": 2.5,
    "step": 0.1,
    "smooth_factor": 0.3
  }
}
```

## PERFORMANCE TIPPS

1. **Weniger FPS = besser für Battery**: `preview_fps: 15` statt 24
2. **Dimmer Screen = weniger Power**: `brightness_medium: 80` statt 120
3. **Keine UI-Overlays**: `grid_enabled: false`, `level_enabled: false`
4. **Zoom begrenzen**: `max: 2.0` statt 2.5

## DEBUGGING

Schau in die Logfiles um Performance zu analysieren:

```bash
# Live logs sehen:
sudo journalctl -u selimcam -f

# Letzte 100 Zeilen:
sudo journalctl -u selimcam -n 100
```

Suche nach:
- `FPS: X` = aktuelle FPS
- `Frame: Xms` = Frame-Zeit
- `Mem: XMB` = RAM-Usage
