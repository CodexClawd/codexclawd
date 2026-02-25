#!/usr/bin/env bash
set -euo pipefail

# Mesh node IPs
NEXUS="10.0.0.1"
CLAWD="10.0.0.2"
BRUTUS="10.0.0.3"
PLUTOS="10.0.0.4"

# Ollama API port (default)
OLLAMA_PORT="11434"
OLLAMA_ENDPOINT="/api/tags"

# Output file
OUTPUT_DIR="memory/neurosec"
OUTPUT_FILE="${OUTPUT_DIR}/mesh_status_latest.json"

# Ensure output directory exists
mkdir -p "${OUTPUT_DIR}"

# Timestamp
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

# Initialize JSON
JSON="{\"timestamp\":\"${TIMESTAMP}\",\"nodes\":{}}"

# Function to check ping
ping_check() {
    local ip="$1"
    local name="$2"
    if ping -c 2 -W 1 "${ip}" &>/dev/null; then
        echo "  ${name}: ping=up"
        JSON=$(echo "${JSON}" | jq --arg name "${name}" --arg status "up" '.nodes[$name].ping = $status')
    else
        echo "  ${name}: ping=down"
        JSON=$(echo "${JSON}" | jq --arg name "${name}" --arg status "down" '.nodes[$name].ping = $status')
    fi
}

# Function to check Ollama API
ollama_check() {
    local ip="$1"
    local name="$2"
    local url="http://${ip}:${OLLAMA_PORT}${OLLAMA_ENDPOINT}"
    if curl -s --max-time 3 "${url}" | jq -e '.models' &>/dev/null; then
        echo "  ${name}: ollama=up"
        JSON=$(echo "${JSON}" | jq --arg name "${name}" --arg status "up" '.nodes[$name].ollama = $status')
    else
        echo "  ${name}: ollama=down"
        JSON=$(echo "${JSON}" | jq --arg name "${name}" --arg status "down" '.nodes[$name].ollama = $status')
    fi
}

# Perform checks
echo "[${TIMESTAMP}] Starting Sentinel mesh check..."
echo "  Pinging all nodes..."
ping_check "${NEXUS}" "nexus"
ping_check "${CLAWD}" "clawd"
ping_check "${BRUTUS}" "brutus"
ping_check "${PLUTOS}" "plutos"

echo "  Checking Ollama API on inference nodes..."
ollama_check "${CLAWD}" "clawd"
ollama_check "${BRUTUS}" "brutus"
ollama_check "${PLUTOS}" "plutos"
# Nexus skipped (security hub)

# Write JSON output (pretty print)
echo "${JSON}" | jq '.' > "${OUTPUT_FILE}"
echo "Results saved to ${OUTPUT_FILE}"

# Check for CRITICAL failures and generate alerts
ALERTS_DIR="alerts"
mkdir -p "${ALERTS_DIR}"

CRITICAL=false

# Check each node for ping down
for node in nexus clawd brutus plutos; do
    ping_status=$(jq -r ".nodes[\"${node}\"].ping // \"unknown\"" "${OUTPUT_FILE}")
    if [[ "${ping_status}" == "down" ]]; then
        CRITICAL=true
        ALERT_FILE="${ALERTS_DIR}/CRITICAL-MESH-${TIMESTAMP}-${node}.md"
        cat > "${ALERT_FILE}" <<EOF
[CRITICAL] Mesh Node Offline: ${node}
IMPACT: Inference and security functions disrupted; potential isolation from mesh
EVIDENCE: Ping failed to 10.0.0.${NODE_SUFFIX}
LOCATION: Node ${node} (10.0.0.${NODE_SUFFIX})
RECOMMENDATION: Immediate network diagnostics and node restart
CERTAINTY: High
EOF
        echo "CRITICAL ALERT: ${node} is offline"
    fi
done

# Check inference nodes for Ollama down
for node in clawd brutus plutos; do
    ollama_status=$(jq -r ".nodes[\"${node}\"].ollama // \"unknown\"" "${OUTPUT_FILE}")
    if [[ "${ollama_status}" == "down" ]]; then
        CRITICAL=true
        ALERT_FILE="${ALERTS_DIR}/CRITICAL-OLLAMA-${TIMESTAMP}-${node}.md"
        cat > "${ALERT_FILE}" <<EOF
[CRITICAL] Ollama API Failure: ${node}
IMPACT: Inference capacity lost; AI processing halted
EVIDENCE: Ollama API unreachable on 10.0.0.${NODE_SUFFIX}:11434
LOCATION: Node ${node} (10.0.0.${NODE_SUFFIX})
RECOMMENDATION: Restart ollama service; check disk/memory
CERTAINTY: High
EOF
        echo "CRITICAL ALERT: Ollama down on ${node}"
    fi
done

if [[ "${CRITICAL}" == "false" ]]; then
    echo "All mesh nodes and Ollama APIs operational."
fi
