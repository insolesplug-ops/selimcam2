#!/bin/bash
# SelimCam Auto-Setup Script für Raspberry Pi
# Run with: sudo bash setup_pi.sh

set -e

echo "======================================"
echo "SelimCam Pi Setup"
echo "======================================"

# 1. Update system
echo "[1/6] Updating system..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

# 2. Install dependencies
echo "[2/6] Installing dependencies..."
sudo apt-get install -y -qq \
    python3-venv \
    python3-dev \
    libatlas-base-dev \
    libjasper-dev \
    libtiff-dev \
    libjasper1 \
    libharfbuzz0b \
    libwebp6 \
    libtiff5 \
    libopenjp2-7 \
    libtiffxx5

# 3. Setup auto-start service
echo "[3/6] Setting up auto-start service..."
sudo cp selimcam.service /etc/systemd/system/
sudo cp show_boot_screen.sh /home/pi/FINALMAINCAMMM/
sudo chmod +x /home/pi/FINALMAINCAMMM/show_boot_screen.sh
sudo systemctl daemon-reload
sudo systemctl enable selimcam

# 4. Configure boot parameters (SILENT BOOT)
echo "[4/6] Configuring silent boot..."
# Backup original
sudo cp /boot/firmware/cmdline.txt /boot/firmware/cmdline.txt.bak

# Add quiet/splash parameters
sudo sed -i 's/^/quiet splash logo.nologo /' /boot/firmware/cmdline.txt

# 5. Disable login prompts
echo "[5/6] Disabling TTY login prompts..."
sudo systemctl disable getty@tty1.service
sudo systemctl mask getty@tty1.service

# 6. Disable console output
echo "[6/6] Disabling console output on HDMI/GPIO..."
# This will prevent all boot messages from showing
sudo sed -i '/^console=/d' /boot/firmware/cmdline.txt
echo >> /boot/firmware/cmdline.txt

echo ""
echo "======================================"
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Enable venv: source .venv/bin/activate"
echo "2. Install packages: pip install -r requirements.txt"
echo "3. Reboot: sudo reboot"
echo "4. App will start automatically with SILENT boot!"
echo "======================================"
