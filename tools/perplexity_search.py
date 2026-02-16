#!/usr/bin/env python3
"""
Perplexity web search tool for OpenClaw.
Usage: perplexity_search.py "query" [recency]
recency: day|week|month|year (default: month)
"""

import os
import sys
import json
import urllib.request
import urllib.error

API_KEY = os.getenv("PERPLEXITY_API_KEY")
if not API_KEY:
    print("Error: PERPLEXITY_API_KEY not set", file=sys.stderr)
    sys.exit(1)

def search(query: str, recency: str = "month") -> str:
    url = "https://api.perplexity.ai/chat/completions"
    model = os.getenv("PERPLEXITY_MODEL", "sonar")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Be precise and concise."},
            {"role": "user", "content": query}
        ],
        "max_tokens": 1024,
        "temperature": 0.2,
        "top_p": 0.9,
        "return_images": False,
        "return_related_questions": False,
        "search_recency_filter": recency,
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1,
        "return_citations": True,
        "search_context_size": "medium"
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status != 200:
                error = resp.read().decode()
                return f"Error {resp.status}: {error}"
            data = json.loads(resp.read().decode())
            content = data["choices"][0]["message"]["content"]
            if "citations" in data:
                citations = "\n".join(f"[{i+1}] {url}" for i, url in enumerate(data["citations"]))
                content += "\n\nCitations:\n" + citations
            return content
    except urllib.error.HTTPError as e:
        return f"HTTP Error {e.code}: {e.read().decode()}"
    except Exception as e:
        return f"Exception: {str(e)}"

def main():
    if len(sys.argv) < 2:
        print("Usage: perplexity_search.py \"query\" [recency]", file=sys.stderr)
        sys.exit(1)
    query = sys.argv[1]
    recency = sys.argv[2] if len(sys.argv) > 2 else "month"
    result = search(query, recency)
    print(result)

if __name__ == "__main__":
    main()
