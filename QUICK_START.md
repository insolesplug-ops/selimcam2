# ⚡ QUICK START - SelimCam v2.0

## SETUP AUF PI (5 Minuten)

```bash
# 1. SSH in die Pi
ssh pi@raspberrypi.local

# 2. Code pullen
cd /home/pi/selimcam2
git pull origin main

# 3. Restart service
sudo systemctl restart selimcam

# 4. Logs anschauen
sudo journalctl -u selimcam -f
```

## TESTEN AUF PI (30 Sekunden)

1. **Touch test**: Tippen Sie oben-links im Screen → roter Punkt sollte direkt unter Finger sein ✅
2. **Camera orientierung**: Bild sollte richtig orientiert sein (nicht upside-down) ✅
3. **UI-Buttons unten**:
   - **Links**: Settings Button
   - **Mitte**: Flash (an/aus/auto)
   - **Rechts**: Galerie
4. **Klicke Settings** → Sollte Settings Menu öffnen mit echte Optionen
5. **Filter wählen** (z.B. "VIVID") → Live Preview sollte Filter zeigen
6. **Helligkeit ändern** → Screen wird direkt heller/dunkler
7. **Back gehen** → Zurück zu Camera

## WAS IST JETZT FUNKTIONAL ✅

- ✅ **Korrekte Rotation** (480×800 Portrait mit +90° final transform)
- ✅ **Touch-Mapping** (red dot unter Finger)
- ✅ **UI-Buttons** mit echten PNG (Settings/Flash/Gallery)
- ✅ **Settings Scene** voll funktional mit Touch
- ✅ **Live Filter Preview** (Filter ändern = sofort sichtbar)
- ✅ **Helligkeit Control** (dark/medium/bright/auto)
- ✅ **Clean UI** (kein Simulator-Text mehr)

## WAS MACHT JEDER BUTTON

### Settings Button 🔧
Öffnet Settings wo du einstellen kannst:
- **Helligkeit** (dark/medium/bright/auto)
- **Filter** (none/bw/sepia/cool/warm/vivid)
- **ISO Gain** (100-1600 Fake)
- **Flash Mode** (off/on/auto)
- **Grid/Level Overlay** (optional)
- **Info Display** (off/minimal/extended)

Tippe auf die Einstellung um zu ändern, tippe nochmal um zu speichern.

### Flash Button ⚡
Schaltet Flash-Mode um:
- **Off** = kein Blitz
- **On** = immer Blitz
- **Auto** = Blitz nur wenn dunkel

### Gallery Button 📸
Zeigt alle gespeicherten Fotos. Blättern mit Links/Rechts.

### Capture Button 📷
Großer Knopf in Mitte → Foto schießen!

## KONFIGURIEREN

### Via Editor (einfach)
```bash
nano /home/pi/selimcam2/config/config.json
```

Ändere z.B.:
```json
"brightness_mode": "bright",  // Helligkeit Standard
"preview_fps": 20,            // FPS anpassen
"capture_quality": 95         // Foto-Qualität
```

### Via Settings Menu (mit Touch)
1. Öffne Settings
2. Tippe auf die Einstellung
3. Tippe nochmal zum Speichern

Beide Methoden funktionieren!

## PERFORMANCE TIPPS

Wenn es laggt:
- Reduziere `preview_fps` auf 15-20
- Reduziere `brightness_medium` auf 80-100
- Deaktiviere `grid_enabled` und `level_enabled`

Wenn langsam beim Foto:
- Reduziere `capture_quality` auf 85-90
- Nutze `capture_width: 1920, capture_height: 1440` für schneller

## TROUBLESHOOTING

### Red Dot ist nicht unter Finger
→ Touch-Mapping Issue. Sag mir:
```
Wenn ich oben-links tippe wo ist der Dot?
```

### Camera ist immer noch falsch orientiert
→ rotation_test in config.json:
```json
"rotation_test": 0  // try 0, 1, 2, 3
```

### Laggy
→ Überprüfe Logs:
```bash
sudo journalctl -u selimcam -f | grep FPS
```

Sollte 20+ FPS zeigen.

### Fotos sind dunkel
→ Helligkeit in Settings erhöhen oder:
```json
"brightness_mode": "bright"
```

### Settings funktioniert nicht
→ Sag mir was du gemacht hast → ich zeichne es auf GitHub Issue

## NÄCHSTE SCHRITTE

1. **Testen und Bug-Report** → Alle Probleme sagen
2. **Fotos machen** → Teste Photo Quality
3. **Performance Check** → FPS-Counter schauen
4. **Einstellungen testen** → Filter, Helligkeit, etc.

Dann werden weitere Features implementiert! 🚀

---

**Schnelle Links:**
- [CAMERA_SETTINGS_GUIDE.md](CAMERA_SETTINGS_GUIDE.md) - Detaillierte Config-Erklärung
- [IMPROVEMENTS.md](IMPROVEMENTS.md) - Roadmap mit 20+ Features
- [GitHub Issues](https://github.com/insolesplug-ops/selimcam2/issues) - Bug-Reports
