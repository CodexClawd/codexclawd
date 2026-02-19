#!/usr/bin/env bash
# Sentinel Mesh Health Check

set -euo pipefail

WORKSPACE="/home/boss/.openclaw/workspace"
JSON_PATH="$WORKSPACE/memory/neurosec/mesh_status_latest.json"

# Ensure directory exists
mkdir -p "$(dirname "$JSON_PATH")"

# Create timestamp
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Initialize JSON
cat > "$JSON_PATH.tmp" << EOF
{
  "timestamp": "$TIMESTAMP",
  "mesh_nodes": {
    "10.0.0.1": {"ping": null, "ollama": null},
    "10.0.0.2": {"ping": null, "ollama": null},
    "10.0.0.3": {"ping": null, "ollama": null},
    "10.0.0.4": {"ping": null, "ollama": null}
  }
}
EOF

# Function to ping a node (2 packets, 1s timeout)
ping_node() {
  local ip=$1
  if ping -c 2 -W 1 "$ip" &>/dev/null; then
    echo "ok"
  else
    echo "unreachable"
  fi
}

# Function to check Ollama API (2s timeout)
check_ollama() {
  local ip=$1
  local response
  response=$(curl -s --max-time 2 "http://$ip:11434/api/tags" 2>&1) || true
  if echo "$response" | grep -q '"models"'; then
    echo "responsive"
  elif echo "$response" | grep -q "connection refused\|failed to connect\|timeout"; then
    echo "down"
  else
    echo "unknown"
  fi
}

# Check all nodes
PING_NEXUS=$(ping_node 10.0.0.1)
PING_CLAWD=$(ping_node 10.0.0.2)
PING_BRUTUS=$(ping_node 10.0.0.3)
PING_PLUTOS=$(ping_node 10.0.0.4)

OLLAMA_CLAWD=$(check_ollama 10.0.0.2)
OLLAMA_BRUTUS=$(check_ollama 10.0.0.3)
OLLAMA_PLUTOS=$(check_ollama 10.0.0.4)

# Update JSON (requires jq)
jq --arg ping_nexus "$PING_NEXUS" \
   --arg ping_clawd "$PING_CLAWD" \
   --arg ping_brutus "$PING_BRUTUS" \
   --arg ping_plutos "$PING_PLUTOS" \
   --arg ollama_clawd "$OLLAMA_CLAWD" \
   --arg ollama_brutus "$OLLAMA_BRUTUS" \
   --arg ollama_plutos "$OLLAMA_PLUTOS" \
   '.mesh_nodes["10.0.0.1"].ping = $ping_nexus
    | .mesh_nodes["10.0.0.2"].ping = $ping_clawd
    | .mesh_nodes["10.0.0.2"].ollama = $ollama_clawd
    | .mesh_nodes["10.0.0.3"].ping = $ping_brutus
    | .mesh_nodes["10.0.0.3"].ollama = $ollama_brutus
    | .mesh_nodes["10.0.0.4"].ping = $ping_plutos
    | .mesh_nodes["10.0.0.4"].ollama = $ollama_plutos' \
   "$JSON_PATH.tmp" > "$JSON_PATH.new" && mv "$JSON_PATH.new" "$JSON_PATH" && rm "$JSON_PATH.tmp"

# Generate summary
SUMMARY=$(cat << EOF
=== MESH STATUS $(date -u +%Y-%m-%d\ %H:%M\ UTC) ===

Node Connectivity:
- Nexus (10.0.0.1): $PING_NEXUS
- Clawd (10.0.0.2): $PING_CLAWD
- Brutus (10.0.0.3): $PING_BRUTUS
- Plutos (10.0.0.4): $PING_PLUTOS

Ollama API Status (Inference Nodes):
- Clawd (10.0.0.2): $OLLAMA_CLAWD
- Brutus (10.0.0.3): $OLLAMA_BRUTUS
- Plutos (10.0.0.4): $OLLAMA_PLUTOS
EOF
)

echo "$SUMMARY"

# Critical failures?
CRITICAL_COUNT=0
if [ "$PING_NEXUS" = "unreachable" ] || [ "$PING_CLAWD" = "unreachable" ] || [ "$PING_BRUTUS" = "unreachable" ] || [ "$PING_PLUTOS" = "unreachable" ]; then
  CRITICAL_COUNT=$((CRITICAL_COUNT + 1))
fi
if [ "$OLLAMA_CLAWD" = "down" ] || [ "$OLLAMA_BRUTUS" = "down" ] || [ "$OLLAMA_PLUTOS" = "down" ]; then
  CRITICAL_COUNT=$((CRITICAL_COUNT + 1))
fi

if [ $CRITICAL_COUNT -gt 0 ]; then
  echo ""
  echo "CRITICAL FAILURES DETECTED: $CRITICAL_COUNT category(ies)"
  echo "Alert file would be generated."
fi

exit 0
