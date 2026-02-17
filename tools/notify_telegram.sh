#!/usr/bin/env bash
# Send Telegram notification via Bot API
# Source: /home/boss/.config/telegram_backup.conf (or set env vars)

set -euo pipefail

CONFIG_FILE="${TELEGRAM_BACKUP_CONFIG:-/home/boss/.config/telegram_backup.conf}"
if [[ -f "$CONFIG_FILE" ]]; then
    source "$CONFIG_FILE"
fi

: "${TELEGRAM_BOT_TOKEN:?Need TELEGRAM_BOT_TOKEN or config file}"
: "${TELEGRAM_CHAT_ID:?Need TELEGRAM_CHAT_ID or config file}"

MESSAGE="${1:-}"
if [[ -z "$MESSAGE" ]]; then
    echo "Usage: $0 <message>"
    exit 1
fi

curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d chat_id="${TELEGRAM_CHAT_ID}" \
    -d text="$MESSAGE" \
    -d parse_mode="Markdown" \
    >/dev/null
