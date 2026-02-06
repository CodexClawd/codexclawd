#!/bin/bash
# Simple coder agent launcher - add this to your ~/.bashrc

# Make sure your OPENAI_API_KEY is exported first!
# export OPENAI_API_KEY='sk-...'

coder() {
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "❌ Set OPENAI_API_KEY first: export OPENAI_API_KEY='sk-...'"
        return 1
    fi
    
    local task="$1"
    if [ -z "$task" ]; then
        echo "Usage: coder 'your coding task here'"
        return 1
    fi
    
    # Spawn a coding session with gpt-4o
    openclaw sessions_spawn \
        --model="openai/gpt-4o" \
        --task="$task" \
        --label="coder-$(date +%s)"
}

# Optional: alias for quick access
alias code='coder'
