#!/usr/bin/env python3
"""
Brutus Coding Client (for clawd-16gb)
Calls brutus-8gb coding agent API
"""

import requests
import json
import sys

BRUTUS_HOST = "http://BRUTUS_IP:8080"  # Change to brutus-8gb IP
AUTH_TOKEN = "brutus-coding-agent-2025"

def generate_code(prompt, language="python"):
    """Ask brutus to generate code"""
    try:
        response = requests.post(
            f"{BRUTUS_HOST}/code",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            json={"prompt": prompt, "language": language},
            timeout=150
        )
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def explain_code(code):
    """Ask brutus to explain code"""
    try:
        response = requests.post(
            f"{BRUTUS_HOST}/explain",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            json={"code": code},
            timeout=90
        )
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def check_health():
    """Check if brutus is online"""
    try:
        response = requests.get(f"{BRUTUS_HOST}/health", timeout=5)
        return response.json()
    except:
        return {"status": "offline"}

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Brutus Coding Client')
    parser.add_argument('task', help='What to code')
    parser.add_argument('--lang', default='python', help='Language')
    parser.add_argument('--explain', help='Explain code from file')
    parser.add_argument('--check', action='store_true', help='Check health')
    
    args = parser.parse_args()
    
    if args.check:
        health = check_health()
        print(f"🦞 Brutus status: {health.get('status', 'unknown')}")
        if health.get('model'):
            print(f"   Model: {health['model']}")
        return
    
    if args.explain:
        with open(args.explain) as f:
            code = f.read()
        print("🧠 Asking brutus to explain...")
        result = explain_code(code)
        if result.get('success'):
            print(result['explanation'])
        else:
            print(f"❌ Error: {result.get('error')}")
        return
    
    # Generate code
    print(f"🦞 Asking brutus to code: {args.task}")
    print("   (this may take 30-120 seconds on CPU)...")
    result = generate_code(args.task, args.lang)
    
    if result.get('success'):
        print("\n✅ Code generated:\n")
        print(result['code'])
    else:
        print(f"\n❌ Error: {result.get('error')}")

if __name__ == '__main__':
    main()
