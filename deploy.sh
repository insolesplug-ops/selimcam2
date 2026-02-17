#!/bin/bash
# SelimCam One-Command Deploy for Raspberry Pi
# Usage: bash deploy.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="selimcam"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
HEALTH_SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}-health.service"
HEALTH_TIMER_FILE="/etc/systemd/system/${SERVICE_NAME}-health.timer"
CURRENT_USER="${SUDO_USER:-$USER}"
CURRENT_GROUP="$(id -gn "$CURRENT_USER")"
CMDLINE_FILE="/boot/firmware/cmdline.txt"

echo "=== SelimCam Auto Deploy ==="
echo "Project: ${PROJECT_DIR}"
echo "User: ${CURRENT_USER}:${CURRENT_GROUP}"

cd "$PROJECT_DIR"
chmod +x "$PROJECT_DIR/start_camera.sh"
chmod +x "$PROJECT_DIR/healthcheck.sh"

echo "[1/8] Installing system dependencies"
sudo apt-get update -y -qq
sudo apt-get install -y \
    python3-picamera2 python3-pygame python3-numpy python3-pil python3-psutil \
    python3-venv python3-full i2c-tools libatlas-base-dev

echo "[2/8] Ensuring user groups"
sudo usermod -a -G video,render,input,gpio,i2c,spi "$CURRENT_USER" || true

echo "[3/8] Preparing virtual environment"
if [[ ! -d "$PROJECT_DIR/.venv" ]]; then
    python3 -m venv "$PROJECT_DIR/.venv"
fi
"$PROJECT_DIR/.venv/bin/python" -m pip install --upgrade pip wheel
"$PROJECT_DIR/.venv/bin/python" -m pip install --no-cache-dir -r "$PROJECT_DIR/requirements.txt"

echo "[4/10] Writing systemd service"
sudo tee "$SERVICE_FILE" >/dev/null <<EOF
[Unit]
Description=SelimCam Camera App
After=multi-user.target
Wants=network.target

[Service]
Type=simple
User=${CURRENT_USER}
Group=${CURRENT_GROUP}
WorkingDirectory=${PROJECT_DIR}
Environment=PYTHONUNBUFFERED=1
Environment=SDL_VIDEODRIVER=kmsdrm
Environment=SDL_VIDEO_KMSDRM_ROTATION=270
Environment=SDL_FBDEV_ROTATION=270
ExecStart=/bin/bash ${PROJECT_DIR}/start_camera.sh
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo tee "$HEALTH_SERVICE_FILE" >/dev/null <<EOF
[Unit]
Description=SelimCam Health Check
After=${SERVICE_NAME}.service

[Service]
Type=oneshot
User=root
Group=root
Environment=SELIMCAM_SERVICE=${SERVICE_NAME}
ExecStart=/bin/bash ${PROJECT_DIR}/healthcheck.sh
EOF

sudo tee "$HEALTH_TIMER_FILE" >/dev/null <<EOF
[Unit]
Description=Run SelimCam health check every 30s

[Timer]
OnBootSec=60
OnUnitActiveSec=30
AccuracySec=1
Persistent=true
Unit=${SERVICE_NAME}-health.service

[Install]
WantedBy=timers.target
EOF

echo "[5/10] Validating Python syntax"
python3 - <<'PY'
import ast
ast.parse(open('main.py', 'r', encoding='utf-8').read())
ast.parse(open('hardware/camera_backend.py', 'r', encoding='utf-8').read())
print('Syntax OK')
PY

echo "[6/10] Enabling quiet boot (idempotent)"
if [[ -f "$CMDLINE_FILE" ]]; then
    sudo cp "$CMDLINE_FILE" "${CMDLINE_FILE}.bak" 2>/dev/null || true
    CMDLINE_CONTENT="$(cat "$CMDLINE_FILE")"
    for arg in quiet splash loglevel=0 logo.nologo vt.global_cursor_default=0; do
        if ! grep -q "\b${arg}\b" <<<"$CMDLINE_CONTENT"; then
            CMDLINE_CONTENT+=" ${arg}"
        fi
    done
    echo "$CMDLINE_CONTENT" | sudo tee "$CMDLINE_FILE" >/dev/null
fi

echo "[7/10] Activating service"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"
sleep 3

echo "[8/10] Activating watchdog timer"
sudo systemctl enable "${SERVICE_NAME}-health.timer"
sudo systemctl restart "${SERVICE_NAME}-health.timer"

echo "[9/10] Runtime checks"
sudo systemctl --no-pager --full status "$SERVICE_NAME" || true
sudo systemctl --no-pager --full status "${SERVICE_NAME}-health.timer" || true
sudo journalctl -u "$SERVICE_NAME" -n 50 --no-pager || true
sudo journalctl -u "${SERVICE_NAME}-health.service" -n 20 --no-pager || true

echo "[10/10] Hardware checks"

if command -v vcgencmd >/dev/null 2>&1; then
    echo "Camera state: $(vcgencmd get_camera || true)"
    echo "Throttled: $(vcgencmd get_throttled || true)"
fi

echo "Deploy complete. Reboot recommended: sudo reboot"