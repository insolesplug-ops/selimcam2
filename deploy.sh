#!/bin/bash
# SelimCam Deploy Script - laeuft auf dem Pi nach git pull
set -e

echo "=== SelimCam Deploy ==="

# 1. Service File deployen
sudo cp selimcam.service /etc/systemd/system/selimcam.service
sudo systemctl daemon-reload
sudo systemctl enable selimcam
echo "Service deployed"

# 2. Benutzergruppen (einmalig wichtig)
sudo usermod -a -G video,render,input,gpio,i2c,spi pi
echo "Groups set"

# 3. Libraries sicherstellen
sudo apt install -y python3-picamera2 python3-pygame python3-numpy \
    python3-pil python3-psutil i2c-tools 2>/dev/null | tail -3

# 4. Syntax check
python3 -c "import ast; ast.parse(open('main.py').read()); print('main.py: OK')"
python3 -c "import ast; ast.parse(open('hardware/camera_backend.py').read()); print('camera_backend.py: OK')"

# 5. Boot: Kein Terminal-Text
CMDLINE=$(cat /boot/firmware/cmdline.txt)
if ! echo "$CMDLINE" | grep -q "quiet"; then
    PARTUUID=$(echo "$CMDLINE" | grep -o 'PARTUUID=[^ ]*' | head -1)
    echo "console=serial0,115200 console=tty3 root=$PARTUUID rootfstype=ext4 fsck.mode=force fsck.repair=yes elevator=deadline quiet splash loglevel=0 logo.nologo vt.global_cursor_default=0" | sudo tee /boot/firmware/cmdline.txt > /dev/null
    echo "Boot: silent mode set"
else
    echo "Boot: already silent"
fi

# 6. Auto-Updates deaktivieren
sudo systemctl disable apt-daily.timer 2>/dev/null || true
sudo systemctl disable apt-daily-upgrade.timer 2>/dev/null || true

# 7. App neu starten
sudo systemctl restart selimcam
sleep 3
echo ""
echo "=== Status ==="
sudo journalctl -u selimcam -n 20 --no-pager
echo ""
echo "=== Kamera ==="
vcgencmd get_camera
echo ""
echo "=== Spannung ==="
vcgencmd measure_volts
vcgencmd get_throttled
echo ""
echo "Deploy fertig! Reboot fuer silent boot: sudo reboot"