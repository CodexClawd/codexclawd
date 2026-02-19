#!/bin/bash
# Sentinel Mesh Check - ping nodes and verify Ollama API

MESH_NODES=(
  "Nexus|10.0.0.1|false"
  "Clawd|10.0.0.2|true"
  "Brutus|10.0.0.3|true"
  "Plutos|10.0.0.4|true"
)

RESULT_FILE="memory/neurosec/mesh_status_latest.json"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

cat > "$RESULT_FILE" <<EOF
{
  "timestamp": "$TIMESTAMP",
  "mesh_nodes": []
}
EOF

for node_info in "${MESH_NODES[@]}"; do
  IFS='|' read -r name ip check_ollama <<< "$node_info"

  # Ping check
  if ping -c 2 -W 1 "$ip" > /dev/null 2>&1; then
    ping_status="up"
  else
    ping_status="down"
  fi

  # Ollama API check (only for inference nodes)
  ollama_status="skipped"
  if [[ "$check_ollama" == "true" && "$ping_status" == "up" ]]; then
    if curl -s --max-time 3 "http://${ip}:11434/api/tags" > /dev/null 2>&1; then
      ollama_status="responsive"
    else
      ollama_status="down"
    fi
  fi

  # Determine node severity
  severity="info"
  if [[ "$ping_status" == "down" ]]; then
    severity="critical"
  elif [[ "$check_ollama" == "true" && "$ollama_status" != "responsive" ]]; then
    severity="critical"
  fi

  jq --arg name "$name" \
     --arg ip "$ip" \
     --arg ping_status "$ping_status" \
     --arg ollama_status "$ollama_status" \
     --arg severity "$severity" \
     '.mesh_nodes += [{"name": $name, "ip": $ip, "ping": $ping_status, "ollama": $ollama_status, "severity": $severity}]' \
     "$RESULT_FILE" > "${RESULT_FILE}.tmp" && mv "${RESULT_FILE}.tmp" "$RESULT_FILE"
done

# Output summary
echo "=== Sentinel Mesh Check Summary ==="
echo "Timestamp: $TIMESTAMP"
echo ""
jq -r '.mesh_nodes[] | "\(.name) (\(.ip)): ping=\(.ping), ollama=\(.ollama), severity=\(.severity)"' "$RESULT_FILE"
echo ""
echo "Full results saved to: $RESULT_FILE"

# Check for critical failures
CRITICAL_COUNT=$(jq '[.mesh_nodes[] | select(.severity=="critical")] | length' "$RESULT_FILE")
if [[ "$CRITICAL_COUNT" -gt 0 ]]; then
  echo ""
  echo "⚠️  CRITICAL: $CRITICAL_COUNT node(s) have failures requiring attention"
  exit 1
fi