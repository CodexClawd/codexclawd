#!/usr/bin/env bash
set -uuo pipefail

WORKSPACE="/home/boss/.openclaw/workspace"
LOG_DIR="$WORKSPACE/logs"
LOG_FILE="$LOG_DIR/backup.log"
NOTIFY_SCRIPT="$WORKSPACE/tools/notify_telegram.sh"

mkdir -p "$LOG_DIR"

TS="$(date -Iseconds)"
{
    echo "[$TS] Starting daily backup…"

    cd "$WORKSPACE"

    if git status --porcelain | grep -q .; then
        git add -A
        COMMIT_MSG="daily backup $TS"
        git commit -m "$COMMIT_MSG" || true

        # Push to both remotes (track exit status)
        git push origin main
        git push backup main

        echo "[$TS] Backup complete."
        STATUS="success"
        SHORT_HASH="$(git rev-parse --short HEAD)"
    else
        echo "[$TS] No changes to backup."
        STATUS="nochanges"
    fi
} 2>&1 | tee -a "$LOG_FILE"

# Send Telegram notification based on STATUS
if [[ -x "$NOTIFY_SCRIPT" ]]; then
    case "${STATUS:-error}" in
        success)
            "$NOTIFY_SCRIPT" "✅ Brutus backup success: $SHORT_HASH pushed to origin & backup."
            ;;
        nochanges)
            "$NOTIFY_SCRIPT" "ℹ️ Brutus backup: no changes."
            ;;
        *)
            "$NOTIFY_SCRIPT" "❌ Brutus backup FAILED. Check logs: $LOG_FILE"
            ;;
    esac
fi
