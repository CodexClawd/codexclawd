#!/usr/bin/env python3
"""
newsclawd notify - Send alerts via Telegram using OpenClaw
Usage: python3 notify.py --title "Alert Title" --message "Alert body text"
"""

import argparse
import os
import sys
import subprocess

def send_telegram(title, message, msg_type='info'):
    """Send notification via OpenClaw message tool"""
    emoji_map = {
        'info': '📰',
        'warning': '⚠️',
        'error': '🚨',
        'code': '💻'
    }
    emoji = emoji_map.get(msg_type, '📰')
    
    full_message = f"{emoji} **{title}**\n\n{message}"
    
    try:
        # Use OpenClaw message tool
        result = subprocess.run(
            ['openclaw', 'message', 'send', '--channel', 'telegram', '--text', full_message],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception as e:
        # Fallback: write to a notification file that OpenClaw can pick up
        notify_file = os.path.expanduser('~/.openclaw/notifications/newsclawd.jsonl')
        os.makedirs(os.path.dirname(notify_file), exist_ok=True)
        with open(notify_file, 'a') as f:
            import json
            f.write(json.dumps({'type': msg_type, 'title': title, 'message': message}) + '\n')
        print(f"📨 Queued for Telegram: {title}")
        return True

def main():
    parser = argparse.ArgumentParser(description='Send newsclawd alerts')
    parser.add_argument('--title', '-t', required=True, help='Alert title')
    parser.add_argument('--message', '-m', required=True, help='Alert message')
    parser.add_argument('--type', default='info', help='Alert type (info, warning, error, code)')
    
    args = parser.parse_args()
    
    # Print locally
    emoji_map = {
        'info': '📰',
        'warning': '⚠️',
        'error': '🚨',
        'code': '💻'
    }
    emoji = emoji_map.get(args.type, '📰')
    print(f"{emoji} **{args.title}**\n\n{args.message}")
    
    # Send to Telegram
    if send_telegram(args.title, args.message, args.type):
        print("📨 Notification queued")
    else:
        print("⚠️ Could not queue notification", file=sys.stderr)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())