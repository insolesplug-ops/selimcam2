#!/bin/bash

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

export PYTHONUNBUFFERED=1
export SELIMCAM_QUIET=true
export SDL_VIDEODRIVER="kmsdrm"
export SDL_VIDEO_KMSDRM_ROTATION="270"
export SDL_FBDEV_ROTATION="270"

if [[ -f ".venv/bin/activate" ]]; then
	# shellcheck disable=SC1091
	source ".venv/bin/activate"
fi

if ! python3 -c "import pygame, numpy, PIL" >/dev/null 2>&1; then
	python3 -m pip install --no-cache-dir -r requirements.txt || true
fi

if ! python3 -c "from picamera2 import Picamera2" >/dev/null 2>&1; then
	echo "[SelimCam] ERROR: picamera2 import failed. Install system package: sudo apt install python3-picamera2" >&2
	exit 1
fi

if command -v vcgencmd >/dev/null 2>&1; then
	CAM_STATE="$(vcgencmd get_camera || true)"
	echo "[SelimCam] ${CAM_STATE}"
fi

exec python3 main.py
