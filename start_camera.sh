#!/bin/bash
# SelimCam - Automatic startup script for Raspberry Pi
# Place in /home/pi/ or set as systemd service
# chmod +x to make executable

# Enable quiet mode (no console spam)
export SELIMCAM_QUIET=true

# Ensure camera is enabled
# (You can check: cat /boot/config.txt | grep camera_enabled)

# Set working directory
cd /home/pi/FINALMAINCAMMM

# Activate virtual environment
source .venv/bin/activate

# Run the application
python3 main.py

# If app crashes, wait before restart
sleep 5
echo "App exited with status $?"
