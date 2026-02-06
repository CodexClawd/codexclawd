#!/bin/bash
# /coding_agent_spawn - Spawn a coding agent with gpt-4o
# Usage: /coding_agent_spawn "your task here"

if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Set OPENAI_API_KEY first:"
    echo "   export OPENAI_API_KEY='sk-...'"
    exit 1
fi

TASK="$1"
if [ -z "$TASK" ]; then
    echo "Usage: /coding_agent_spawn 'build me a crypto tracker'"
    exit 1
fi

echo "🚀 Spawning coding agent..."
echo "   Task: $TASK"
echo "   Model: gpt-4o"
echo ""

# Create a temporary script that the user can run
# This will communicate with the gateway
curl -s -X POST http://localhost:18789/api/v1/sessions/spawn \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${OPENCLAW_TOKEN:-}" \
    -d "{
        \"model\": \"openai/gpt-4o\",
        \"task\": \"$TASK\",
        \"thinking\": \"medium\"
    }" 2>/dev/null || echo "⚠️  Gateway API call failed. Ask Brutus to spawn it instead."
