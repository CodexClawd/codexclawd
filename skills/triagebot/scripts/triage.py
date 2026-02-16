#!/usr/bin/env python3
"""TriageBot - Sorts Flo's requests before they hit Kimi"""
import requests
import json
import sys

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder:3b"

def classify_task(text):
    """Use tinyllama to tag incoming requests"""
    prompt = f"""You are TriageBot. Tag this user request with EXACTLY ONE category:
- [URGENT] - needs immediate action, broken, security issue
- [DEEP_THINK] - complex, requires research/analysis, not simple
- [QUICK_ANSWER] - factual, 1-2 sentences, no heavy lifting  
- [FYI] - just info, no response needed
- [AUTOMATION] - can be scripted/coded

Only respond with the tag and one sentence why.

Request: {text}

Tag:"""
    
    try:
        r = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1}
        }, timeout=10)
        
        result = r.json()["response"].strip()
        
        # Extract tag (with or without brackets)
        tag_map = {
            "[URGENT]": "[URGENT]", "URGENT": "[URGENT]",
            "[DEEP_THINK]": "[DEEP_THINK]", "DEEP_THINK": "[DEEP_THINK]",
            "[QUICK_ANSWER]": "[QUICK_ANSWER]", "QUICK_ANSWER": "[QUICK_ANSWER]",
            "[FYI]": "[FYI]", "FYI": "[FYI]",
            "[AUTOMATION]": "[AUTOMATION]", "AUTOMATION": "[AUTOMATION]"
        }
        
        for key, val in tag_map.items():
            if key in result.upper():
                return val, result
        
        return "[DEEP_THINK]", result  # default to escalation
        
    except Exception as e:
        return "[DEEP_THINK]", f"Triage failed: {e}"

def route_decision(tag, original_text):
    """Decide what to do based on tag"""
    routing = {
        "[URGENT]": "ESCALATE_TO_KIMI",
        "[DEEP_THINK]": "ESCALATE_TO_KIMI", 
        "[QUICK_ANSWER]": "HANDLE_LOCALLY",
        "[FYI]": "LOG_ONLY",
        "[AUTOMATION]": "SPAWN_CODER_SUBAGENT"
    }
    
    action = routing.get(tag, "ESCALATE_TO_KIMI")
    
    return {
        "tag": tag,
        "action": action,
        "original": original_text,
        "reasoning": f"TriageBot classified as {tag}"
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: triage.py 'your request here'")
        sys.exit(1)
    
    text = sys.argv[1]
    tag, raw = classify_task(text)
    decision = route_decision(tag, text)
    
    print(f"🎯 {tag}")
    print(f"📤 Action: {decision['action']}")
    print(f"🧠 Raw: {raw}")

if __name__ == "__main__":
    main()
