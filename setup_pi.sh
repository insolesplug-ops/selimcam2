#!/bin/bash
# SelimCam Auto-Setup Wrapper
# Usage: bash setup_pi.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

chmod +x "$SCRIPT_DIR/deploy.sh"
exec "$SCRIPT_DIR/deploy.sh"
