#!/bin/bash
# ============================================================
# SETUP PASSWORDLESS SUDO FOR SHUTDOWN COMMAND
# ============================================================
# This script configures the 'pi' user to run 'shutdown' 
# without a password prompt, required for the SelimCam 
# shutdown button in the Settings menu.
#
# RUN ON RASPBERRY PI:
#   sudo bash setup_shutdown_sudo.sh
#
# This adds the line:
#   pi ALL=(ALL) NOPASSWD: /sbin/shutdown
# to /etc/sudoers.d/selimcam-shutdown
#
# ============================================================

set -e  # Exit on error

echo "=================================================="
echo "SelimCam Shutdown Sudo Setup"
echo "=================================================="

if [[ $EUID -ne 0 ]]; then
   echo "ERROR: This script must be run as root (use: sudo bash setup_shutdown_sudo.sh)"
   exit 1
fi

# Create sudoers.d entry for SelimCam shutdown
SUDOERS_FILE="/etc/sudoers.d/selimcam-shutdown"
SUDOERS_CONTENT="pi ALL=(ALL) NOPASSWD: /sbin/shutdown"

echo ""
echo "Creating sudoers configuration at: $SUDOERS_FILE"
echo "Content: $SUDOERS_CONTENT"
echo ""

# Create the file with correct permissions
echo "$SUDOERS_CONTENT" > "$SUDOERS_FILE"

# Set correct permissions (must be 0440)
chmod 0440 "$SUDOERS_FILE"

# Verify the file was created
if [ -f "$SUDOERS_FILE" ]; then
    echo "✓ Sudoers file created successfully"
else
    echo "✗ Failed to create sudoers file"
    exit 1
fi

# Verify with visudo
echo ""
echo "Verifying sudoers syntax..."
if visudo -c -f "$SUDOERS_FILE" > /dev/null 2>&1; then
    echo "✓ Sudoers file syntax is valid"
else
    echo "✗ Sudoers file has syntax errors"
    rm -f "$SUDOERS_FILE"
    exit 1
fi

echo ""
echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo "The 'pi' user can now run: sudo shutdown -h now"
echo "without being prompted for a password."
echo ""
echo "The SelimCam 'Shutdown Device' button will now work."
echo "=================================================="
