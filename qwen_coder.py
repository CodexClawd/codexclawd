#!/usr/bin/env python3
"""
Qwen Coder Assistant - Python script for brutus-8gb
Integrates with local Ollama Qwen 2.5 Coder model for code generation
"""

import requests
import json
import sys
import argparse
from datetime import datetime

OLLAMA_HOST = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5-coder:7b"


def query_ollama(prompt, model=DEFAULT_MODEL, temperature=0.7):
    """Send prompt to local Ollama instance"""
    url = f"{OLLAMA_HOST}/api/generate"
    
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_ctx": 4096
        }
    }
    
    try:
        response = requests.post(url, json=data, timeout=120)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Ollama not running. Start with: ollama serve"}
    except Exception as e:
        return {"error": str(e)}


def code_assistant(task, language="python", explain=True):
    """Generate code with optional explanation"""
    
    if explain:
        prompt = f"""Write {language} code for this task:

Task: {task}

Provide:
1. Clean, well-commented code
2. Brief explanation of how it works
3. Example usage

Code:"""
    else:
        prompt = f"Write {language} code for: {task}\n\nCode only, no explanation:"
    
    result = query_ollama(prompt)
    
    if "error" in result:
        return f"Error: {result['error']}"
    
    return result.get('response', 'No response received')


def explain_code(code_snippet, language="python"):
    """Explain what code does"""
    
    prompt = f"""Explain this {language} code in simple terms:

```
{code_snippet}
```

Explain what it does, any potential issues, and how to improve it:"""
    
    result = query_ollama(prompt)
    
    if "error" in result:
        return f"Error: {result['error']}"
    
    return result.get('response', 'No response received')


def fix_code(code_snippet, error_message=""):
    """Debug/fix code with errors"""
    
    if error_message:
        prompt = f"""Fix this code that has this error:

Error: {error_message}

Code:
```
{code_snippet}
```

Fixed code:"""
    else:
        prompt = f"""Review and improve this code:

```
{code_snippet}
```

Improved version:"""
    
    result = query_ollama(prompt)
    
    if "error" in result:
        return f"Error: {result['error']}"
    
    return result.get('response', 'No response received')


def shell_command(task):
    """Generate bash/shell commands"""
    
    prompt = f"""Write a bash command or script for this task:

Task: {task}

Provide the command and a brief explanation of what each part does.

Command:"""
    
    result = query_ollama(prompt)
    
    if "error" in result:
        return f"Error: {result['error']}"
    
    return result.get('response', 'No response received')


def save_to_file(content, filename):
    """Save generated code to file"""
    try:
        with open(filename, 'w') as f:
            f.write(content)
        return f"✅ Saved to {filename}"
    except Exception as e:
        return f"❌ Error saving: {e}"


def main():
    parser = argparse.ArgumentParser(
        description='Qwen Coder Assistant - AI coding help on your VPS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s code "monitor RAM usage and alert if above 80%" --save monitor.py
  %(prog)s explain "$(cat script.py)"  
  %(prog)s fix "$(cat broken.py)" --error "ModuleNotFoundError"
  %(prog)s shell "find all Python files modified in last 24 hours"
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Code generation
    code_parser = subparsers.add_parser('code', help='Generate code')
    code_parser.add_argument('task', help='What to code')
    code_parser.add_argument('--lang', default='python', help='Programming language')
    code_parser.add_argument('--no-explain', action='store_true', help='Code only, no explanation')
    code_parser.add_argument('--save', help='Save output to file')
    
    # Explain code
    explain_parser = subparsers.add_parser('explain', help='Explain what code does')
    explain_parser.add_argument('code', help='Code snippet to explain (or use stdin)')
    explain_parser.add_argument('--lang', default='python', help='Programming language')
    
    # Fix code
    fix_parser = subparsers.add_parser('fix', help='Fix/debug code')
    fix_parser.add_argument('code', help='Code with errors (or use stdin)')
    fix_parser.add_argument('--error', help='Error message')
    
    # Shell commands
    shell_parser = subparsers.add_parser('shell', help='Generate shell commands')
    shell_parser.add_argument('task', help='What to do')
    
    # Quick mode (just ask)
    parser.add_argument('-q', '--quick', help='Quick question mode')
    
    args = parser.parse_args()
    
    print(f"🦞 Qwen Coder on {DEFAULT_MODEL}\n")
    
    if args.quick:
        result = query_ollama(args.quick)
        print(result.get('response', result.get('error', 'No response')))
        return
    
    if args.command == 'code':
        result = code_assistant(args.task, args.lang, not args.no_explain)
        print(result)
        if args.save:
            print(f"\n{save_to_file(result, args.save)}")
    
    elif args.command == 'explain':
        code = args.code if not sys.stdin.isatty() else input("Paste code (Ctrl+D when done):\n")
        result = explain_code(code, args.lang)
        print(result)
    
    elif args.command == 'fix':
        code = args.code if not sys.stdin.isatty() else input("Paste code (Ctrl+D when done):\n")
        result = fix_code(code, args.error)
        print(result)
    
    elif args.command == 'shell':
        result = shell_command(args.task)
        print(result)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
