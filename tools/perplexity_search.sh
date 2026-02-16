#!/usr/bin/env bash
# Perplexity web search tool for OpenClaw
# Usage: perplexity_search.sh "query" [recency]
# recency: day|week|month|year (default: month)

set -euo pipefail

API_KEY="${PERPLEXITY_API_KEY:-}"
if [[ -z "$API_KEY" ]]; then
  echo "Error: PERPLEXITY_API_KEY not set" >&2
  exit 1
fi

QUERY="$1"
RECENCY="${2:-month}"
MODEL="${PERPLEXITY_MODEL:-sonar}"

read -r -d '' PAYLOAD <<EOF
{
  "model": "$MODEL",
  "messages": [
    {"role": "system", "content": "Be precise and concise."},
    {"role": "user", "content": "$QUERY"}
  ],
  "max_tokens": 1024,
  "temperature": 0.2,
  "top_p": 0.9,
  "return_images": false,
  "return_related_questions": false,
  "search_recency_filter": "$RECENCY",
  "top_k": 0,
  "stream": false,
  "presence_penalty": 0,
  "frequency_penalty": 1,
  "return_citations": true,
  "search_context_size": "medium"
}
EOF

RESPONSE=$(curl -s -X POST https://api.perplexity.ai/chat/completions \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

# Extract content
echo "$RESPONSE" | python3 -c "
import sys, json
try:
  data = json.load(sys.stdin)
  content = data['choices'][0]['message']['content']
  if 'citations' in data:
    citations = '\n'.join(f'[{i+1}] {url}' for i, url in enumerate(data['citations']))
    content += '\n\nCitations:\n' + citations
  print(content)
except Exception as e:
  print('Error parsing response:', file=sys.stderr)
  print(e, file=sys.stderr)
  sys.exit(1)
" 2>/dev/null || echo "$RESPONSE"
