#!/bin/bash
# Fix Brutus mesh packet loss by restarting WireGuard
# Run THIS ON BRUTUS (10.0.0.3) as a user with sudo privileges

set -e

echo "🔧 Fixing Brutus WireGuard tunnel..."

# 1. Check current wg0 status
echo "Current wg0 status:"
sudo wg show wg0 status 2>/dev/null || echo "wg0 interface may be down or not exist"

# 2. Restart the wg-quick service
echo "Restarting wg-quick@wg0..."
sudo systemctl restart wg-quick@wg0

# 3. Wait for handshake
sleep 3

# 4. Verify
echo "Verifying wg0:"
ip link show wg0
echo "Latest handshakes:"
sudo wg show wg0 latest-handshakes
echo "Transfer stats:"
sudo wg show wg0 transfer

# 5. Test connectivity to other nodes
for node in 10.0.0.1 10.0.0.2 10.0.0.4; do
  echo -n "Ping $node: "
  ping -c 3 -W 2 $node | grep -E "packet loss|time" | tail -1
done

echo "✅ Brutus WireGuard should be healthy now."