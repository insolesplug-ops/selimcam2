#!/bin/bash

set -euo pipefail

SERVICE_NAME="${SELIMCAM_SERVICE:-selimcam}"
HEALTH_FILE="${SELIMCAM_HEALTH_FILE:-/home/pi/camera_app_data/selimcam_health.json}"
STATE_FILE="${SELIMCAM_STATE_FILE:-/tmp/selimcam_health_failcount}"
MAX_STALE_S="${SELIMCAM_MAX_STALE_S:-25}"
MIN_FPS="${SELIMCAM_MIN_FPS:-12}"
MAX_MEM_MB="${SELIMCAM_MAX_MEM_MB:-380}"
MAX_FAILS="${SELIMCAM_MAX_FAILS:-3}"

fail_check() {
    local reason="$1"
    local fails=0
    if [[ -f "$STATE_FILE" ]]; then
        fails="$(cat "$STATE_FILE" 2>/dev/null || echo 0)"
    fi
    fails=$((fails + 1))
    echo "$fails" > "$STATE_FILE"
    echo "[Healthcheck] FAIL(${fails}/${MAX_FAILS}): ${reason}"
    if [[ "$fails" -ge "$MAX_FAILS" ]]; then
        echo "[Healthcheck] Restarting ${SERVICE_NAME} due to repeated failures"
        systemctl restart "$SERVICE_NAME"
        echo "0" > "$STATE_FILE"
    fi
    exit 1
}

pass_check() {
    echo "0" > "$STATE_FILE"
    echo "[Healthcheck] PASS"
    exit 0
}

if ! systemctl is-active --quiet "$SERVICE_NAME"; then
    fail_check "Service ${SERVICE_NAME} is not active"
fi

if [[ ! -f "$HEALTH_FILE" ]]; then
    fail_check "Missing health file: ${HEALTH_FILE}"
fi

if ! check_output=$(python3 - "$HEALTH_FILE" "$MAX_STALE_S" "$MIN_FPS" "$MAX_MEM_MB" <<'PY'
import json
import sys
import time

health_file = sys.argv[1]
max_stale_s = float(sys.argv[2])
min_fps = float(sys.argv[3])
max_mem_mb = float(sys.argv[4])

with open(health_file, "r", encoding="utf-8") as handle:
    data = json.load(handle)

timestamp = float(data.get("timestamp", 0.0))
age = time.time() - timestamp
fps = float(data.get("fps", 0.0))
mem = float(data.get("memory_mb", 0.0))
status = str(data.get("status", "unknown"))

if age > max_stale_s:
    print(f"stale heartbeat age={age:.1f}s")
    sys.exit(11)

if status == "running" and fps < min_fps:
    print(f"low fps fps={fps:.2f} < {min_fps:.2f}")
    sys.exit(12)

if mem > max_mem_mb:
    print(f"high memory mem={mem:.1f}MB > {max_mem_mb:.1f}MB")
    sys.exit(13)

print(f"ok age={age:.1f}s fps={fps:.2f} mem={mem:.1f}MB status={status}")
sys.exit(0)
PY
); then
    fail_check "Health metrics out of range (${check_output})"
fi

echo "[Healthcheck] ${check_output}"

pass_check