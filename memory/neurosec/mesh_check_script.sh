#!/bin/bash
# Sentinel mesh health check — 2026-02-18 07:30 UTC

WIREGUARD_IPS="10.0.0.1 10.0.0.2 10.0.0.3 10.0.0.4"
INFERENCE_NODES="10.0.0.2 10.0.0.3 10.0.0.4"
OLLAMA_PORT=11434
SNAPSHOT_FILE="memory/neurosec/mesh_status_latest.json"
ALERT_DIR="alerts"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

declare -A ping_status
declare -A ollama_status
declare -A ip_of

# Map friendly names to IPs
ip_of[nexus]=10.0.0.1
ip_of[clawd]=10.0.0.2
ip_of[brutus]=10.0.0.3
ip_of[plutos]=10.0.0.4

# Perform checks
for node in nexus clawd brutus plutos; do
  ip="${ip_of[$node]}"
  if ping -c 2 -W 1 "$ip" &>/dev/null; then
    ping_status[$node]=ok
  else
    ping_status[$node]=fail
  fi

  if echo "$INFERENCE_NODES" | grep -qw "$ip"; then
    if curl -s --max-time 2 "http://$ip:$OLLAMA_PORT/api/tags" | grep -q '"models"'; then
      ollama_status[$node]=ok
    else
      ollama_status[$node]=fail
    fi
  else
    ollama_status[$node]=skipped
  fi
done

# Build snapshot JSON
cat > "$SNAPSHOT_FILE" <<EOF
{
  "timestamp": "$TIMESTAMP",
  "mesh_nodes": {
    "nexus": { "ip": "${ip_of[nexus]}", "ping": "${ping_status[nexus]}", "ollama": "${ollama_status[nexus]}" },
    "clawd": { "ip": "${ip_of[clawd]}", "ping": "${ping_status[clawd]}", "ollama": "${ollama_status[clawd]}" },
    "brutus": { "ip": "${ip_of[brutus]}", "ping": "${ping_status[brutus]}", "ollama": "${ollama_status[brutus]}" },
    "plutos": { "ip": "${ip_of[plutos]}", "ping": "${ping_status[plutos]}", "ollama": "${ollama_status[plutos]}" }
  }
}
EOF

# Critical alerts
CRITICAL=0
for node in nexus clawd brutus plutos; do
  if [ "${ping_status[$node]}" = "fail" ]; then
    CRITICAL=1
    mkdir -p "$ALERT_DIR"
    ALERT="$ALERT_DIR/CRITICAL-NETWORK-$node-${TIMESTAMP}.md"
    cat > "$ALERT" <<EOM
[CRITICAL] Mesh node unreachable: $node (IP: ${ip_of[$node]})
IMPACT: Communication failure in mesh; node isolated.
EVIDENCE: Ping timeout to ${ip_of[$node]} (2 packets, 1s timeout).
LOCATION: ${ip_of[$node]}
RECOMMENDATION: Check WG tunnel status, firewall, host availability. Isolate if persistent.
CERTAINTY: High
EOM
  fi
done

for node in clawd brutus plutos; do
  if [ "${ollama_status[$node]}" = "fail" ]; then
    CRITICAL=1
    mkdir -p "$ALERT_DIR"
    ALERT="$ALERT_DIR/CRITICAL-OLLAMA-$node-${TIMESTAMP}.md"
    cat > "$ALERT" <<EOM
[CRITICAL] Inference node Ollama API down: $node (IP: ${ip_of[$node]})
IMPACT: Inference service interrupted; dependent agents cannot run local models.
EVIDENCE: HTTP 200 with valid JSON expected from http://${ip_of[$node]}:$OLLAMA_PORT/api/tags; got timeout/bad response.
LOCATION: ${ip_of[$node]}
RECOMMENDATION: Restart ollama service on the node. Check disk/memory pressure.
CERTAINTY: High
EOM
  fi
done

exit $CRITICAL