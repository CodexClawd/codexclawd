#!/bin/bash

# Kimi-k2.5 via NVIDIA API
API_KEY="${NVIDIA_API_KEY:-YOUR_KEY_HERE}"
PROMPT="${1:-Hello}"

if [ "$API_KEY" = "YOUR_KEY_HERE" ]; then
    echo "Error: Set NVIDIA_API_KEY environment variable or edit this script"
    exit 1
fi

curl -s https://integrate.api.nvidia.com/v1/chat/completions \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "model": "moonshotai/kimi-k2.5",
    "messages": [{"role":"user","content":"'"$PROMPT"'"}],
    "max_tokens": 16384,
    "temperature": 1.00,
    "stream": false
  }' | jq -r '.choices[0].message.content'
