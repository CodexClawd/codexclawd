#!/bin/bash
# Ollama coding agent wrapper
# Usage: ./ollama_coder.sh "write a python script to..."

PROMPT="$1"
MODEL="${2:-codellama}"

if [ -z "$PROMPT" ]; then
    echo "Usage: ./ollama_coder.sh 'write a python function to...' [model]"
    exit 1
fi

echo "🦞 Asking Codellama..."
echo ""

curl -s http://localhost:11434/api/generate -d "{
  \"model\": \"$MODEL\",
  \"prompt\": \"$PROMPT\",
  \"stream\": false
}" | jq -r '.response' 2>/dev/null || echo "Error: Ollama not responding"
