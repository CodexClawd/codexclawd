#!/bin/bash
# Fix SSH config to listen on all interfaces and set Port 22
set -euo pipefail

SSHD_CONF="/etc/ssh/sshd_config"

# Backup original
cp "$SSHD_CONF" "${SSHD_CONF}.brutus-backup-$(date +%s)"

# Ensure ListenAddress is 0.0.0.0 (comment out any others)
sed -i '/^ListenAddress/s/^/#/' "$SSHD_CONF"
echo 'ListenAddress 0.0.0.0' >> "$SSHD_CONF"

# Ensure Port is 22 (or keep existing if already 22)
if ! grep -qE '^Port 22(\s|$)' "$SSHD_CONF"; then
    # If there's a Port line, replace; else append
    if grep -q '^Port ' "$SSHD_CONF"; then
        sed -i 's/^Port .*/Port 22/' "$SSHD_CONF"
    else
        echo 'Port 22' >> "$SSHD_CONF"
    fi
fi

# Restart SSH
systemctl restart ssh

# Report status
ss -tuln | grep ':22' || echo "Port 22 not listening!"
