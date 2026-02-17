#!/bin/bash
# Show boot screen before starting the app
# This script runs as ExecStartPre in systemd

# Create boot screen image if doesn't exist
SPLASH_IMG="/tmp/selimcam_splash.png"
if [ ! -f "$SPLASH_IMG" ]; then
    /home/pi/FINALMAINCAMMM/.venv/bin/python /home/pi/FINALMAINCAMMM/create_splash.py 2>/dev/null
fi

# Show splash on framebuffer for 2 seconds (optional - can use fbi or other framebuffer tools)
# This is a placeholder - on actual Pi you'd use:
# fbi -a -d /dev/fb0 $SPLASH_IMG 2>/dev/null &
# sleep 2
# pkill -f fbi

# If no framebuffer setup available, just wait 1 second
sleep 1

# All output redirected to dev/null - completely silent
exit 0
