#!/usr/bin/env python3
"""
Semantic Recall Hook
Automatically retrieves and injects relevant past context before each prompt.
Designed to integrate with OpenClaw's agent pre-processing.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/home/boss/.openclaw/workspace")
VECTOR_DIR = WORKSPACE / "memory" / "vector"
sys.path.insert(0, str(WORKSPACE / "components"))

def recall(query, k=5):
    """Perform semantic search against vector memory"""
    try:
        from vector_memory import VectorMemory
        vm = VectorMemory()
        results = vm.search(query, k=k)
        return results
    except Exception as e:
        return [{"error": str(e)}]

def format_recall(results):
    if not results or "error" in results[0]:
        return ""
    lines = ["## Relevant Past Context (auto-retrieved)"]
    for i, r in enumerate(results, 1):
        score = r.get('distance', 0)
        similarity = max(0, 1 - score)
        lines.append(f"{i}. [{r['source']}] similarity={similarity:.2f}")
        snippet = r['text'][:250]
        if len(r['text']) > 250:
            snippet += "..."
        lines.append(f"   {snippet}")
        lines.append("")
    return "\n".join(lines)

def main():
    # Read incoming prompt from stdin (OpenClaw pre-hook)
    prompt = sys.stdin.read().strip()
    if not prompt:
        print("")
        return

    # Also include compaction injector output
    inject_path = Path("/home/boss/.openclaw/workspace/memory/.compaction_inject.txt")
    injection = ""
    if inject_path.exists():
        injection = inject_path.read_text().strip()
        injection += "\n\n"

    # Recall relevant memory
    results = recall(prompt, k=5)
    recalled = format_recall(results)

    # Construct enhanced prompt
    if recalled:
        enhanced = f"{injection}{recalled}\n\nCurrent User Input:\n{prompt}"
    else:
        enhanced = f"{injection}No relevant past context found.\n\nCurrent User Input:\n{prompt}"

    print(enhanced)

if __name__ == "__main__":
    main()
