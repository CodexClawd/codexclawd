#!/bin/bash
# Sentinel Mesh Health Check
# Checks all mesh nodes and Ollama API on inference nodes

MESH_NODES=("10.0.0.1" "10.0.0.2" "10.0.0.3" "10.0.0.4")
INFERENCE_NODES=("10.0.0.2" "10.0.0.3" "10.0.0.4")
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
JSON_FILE="memory/neurosec/mesh_status_latest.json"
ALERT_DIR="memory/neurosec/alerts"
mkdir -p "$ALERT_DIR"

# Initialize result structure
declare -A results
for node in "${MESH_NODES[@]}"; do
    results["$node"]='{"ping":false,"ollama":null}'
done

CRITICAL_ALERTS=()

# Phase 1: Ping all mesh nodes
echo "Pinging mesh nodes..."
for node in "${MESH_NODES[@]}"; do
    if ping -c 3 -W 2 "$node" &>/dev/null; then
        results["$node"]='{"ping":true,"ollama":null}'
        echo "✓ $node reachable"
    else
        results["$node"]='{"ping":false,"ollama":null}'
        echo "✗ $node unreachable"
        # CRITICAL: Node down in mesh
        CRITICAL_ALERTS+=("$node ping failed")
    fi
done

# Phase 2: Check Ollama API on inference nodes only
echo "Checking Ollama API on inference nodes..."
for node in "${INFERENCE_NODES[@]}"; do
    if [[ ${results["$node"]} == *'"ping":true'* ]]; then
        if curl -s --max-time 5 "http://$node:11434/api/tags" &>/dev/null; then
            # Mark ollama as true
            current='{"ping":true,"ollama":null}'
            results["$node"]='{"ping":true,"ollama":true}'
            echo "✓ $node:11434 Ollama responding"
        else
            results["$node"]='{"ping":true,"ollama":false}'
            echo "✗ $node:11434 Ollama not responding"
            # CRITICAL: Ollama down on inference node
            CRITICAL_ALERTS+=("$node Ollama API failed")
        fi
    else
        # Node unreachable, can't check Ollama
        results["$node"]='{"ping":false,"ollama":null}'
    fi
done

# Generate JSON output
JSON="{
  \"timestamp\": \"$TIMESTAMP\",
  \"nodes\": {"
FIRST=true
for node in "${MESH_NODES[@]}"; do
    if [ "$FIRST" = false ]; then
        JSON="$JSON,"
    fi
    FIRST=false
    JSON="$JSON\n    \"$node\": ${results["$node"]}"
done
JSON="$JSON\n  },\n  \"critical\": ${#CRITICAL_ALERTS[@]} > 0
}"

echo "$JSON" > "$JSON_FILE"
echo "Log written to $JSON_FILE"

# Handle CRITICAL alerts
echo ""
if [ ${#CRITICAL_ALERTS[@]} -gt 0 ]; then
    echo "CRITICAL ALERTS:"
    for alert in "${CRITICAL_ALERTS[@]}"; do
        echo "  - $alert"
    done
    
    # Create alert file
    ALERT_FILE="$ALERT_DIR/CRITICAL-MESH-${TIMESTAMP//[:T-]/_}.md"
    cat > "$ALERT_FILE" <<EOF
# CRITICAL MESH ALERT

**Timestamp:** $TIMESTAMP
**Severity:** CRITICAL

## Failures
$(for a in "${CRITICAL_ALERTS[@]}"; do echo "- $a"; done)

## Impact
Mesh connectivity or inference capability compromised. Immediate investigation required.

## Recommendation
1. Verify node status and network routing
2. Check WireGuard tunnel integrity
3. Restart affected services (Ollama if applicable)
EOF
    echo "Alert saved to $ALERT_FILE"
else
    echo "No CRITICAL failures detected."
fi
