#!/usr/bin/env bash
# Auto-clear resolved alerts from memory/neurosec/alerts/
# Keeps only recent alerts (last 24h) when mesh is healthy

set -euo pipefail

WORKSPACE="/home/boss/.openclaw/workspace"
ALERTS_DIR="$WORKSPACE/memory/neurosec/alerts"
STATUS_JSON="$WORKSPACE/memory/neurosec/mesh_status_latest.json"
RETENTION_HOURS=24

if [[ ! -d "$ALERTS_DIR" ]]; then
    echo "No alerts directory: $ALERTS_DIR"
    exit 0
fi

# Check current mesh health
if [[ -f "$STATUS_JSON" ]]; then
    CRITICAL_COUNT=$(jq -r '.critical_alerts | length // 0' "$STATUS_JSON" 2>/dev/null || echo "0")
else
    CRITICAL_COUNT=0
fi

# If mesh is healthy (no active criticals), purge old alerts
if [[ "$CRITICAL_COUNT" -eq 0 ]]; then
    CUTOFF_EPOCH=$(date -d "$RETENTION_HOURS hours ago" +%s)
    PURGED=0

    # Find alert files
    while IFS= read -r file; do
        FILE_MTIME=$(stat -c %Y "$file" 2>/dev/null || echo "0")
        if [[ "$FILE_MTIME" -lt "$CUTOFF_EPOCH" ]]; then
            rm -f "$file"
            PURGED=$((PURGED + 1))
        fi
    done < <(find "$ALERTS_DIR" -type f -name "*.md" 2>/dev/null || true)

    echo "✅ Mesh healthy. Purged $PURGED old alert file(s) (older than ${RETENTION_HOURS}h)."
else
    echo "⚠️ $CRITICAL_COUNT critical alert(s) active — keeping all alerts for review."
fi
