#!/bin/bash
# Auto-Push to GitHub - Einfach ausführen und fertig!

cd "$(dirname "$0")"

echo "📤 Uploading to GitHub..."

# Add, commit, push
git add .
git commit -m "Auto-update: $(date '+%Y-%m-%d %H:%M')" 2>/dev/null || echo "Nothing to commit"
git push origin main

echo "✅ Done! Check: https://github.com/insolesplug-ops/selimcam2"
