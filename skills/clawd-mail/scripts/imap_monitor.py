#!/usr/bin/env python3
"""Fastmail IMAP IDLE Monitor - Real-time email notifications to Telegram"""
import imaplib
import email
import time
import json
import os
import threading
from email.header import decode_header
import requests

CREDS_PATH = os.path.expanduser('~/.config/fastmail/creds')
STATE_PATH = os.path.expanduser('~/.config/fastmail/imap_state.json')
CONFIG_PATH = os.path.expanduser('~/.config/fastmail/monitor_config.json')

# Telegram bot config (read from config file)
DEFAULT_CONFIG = {
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    "fastmail_imap_server": "imap.fastmail.com",
    "check_interval": 1,  # IDLE timeout in minutes
    "max_summary_length": 500,
    "ignore_spam": True,
    "ignore_read": True,
    "notification_cooldown": 30  # seconds between notifications
}

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    return DEFAULT_CONFIG

def load_creds():
    if not os.path.exists(CREDS_PATH):
        print(f"❌ Credentials not found at {CREDS_PATH}", file=sys.stderr)
        sys.exit(1)
    with open(CREDS_PATH) as f:
        line = f.read().strip()
        email_addr, password = line.split(':', 1)
        return email_addr, password

def load_seen_uids():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return set(json.load(f))
    return set()

def save_seen_uids(uids):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, 'w') as f:
        json.dump(list(uids), f)

def decode_email_header(header):
    """Decode email header to string"""
    if not header:
        return ""
    decoded_parts = []
    for part, charset in decode_header(header):
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(charset or 'utf-8', errors='replace'))
        else:
            decoded_parts.append(part)
    return ' '.join(decoded_parts)

def get_email_body(msg):
    """Extract FULL text body from email"""
    import re
    body = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = part.get('Content-Disposition', '')
            
            # Skip attachments
            if 'attachment' in content_disposition:
                continue
                
            if content_type == "text/plain":
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode('utf-8', errors='replace')
                        break
                except:
                    continue
            elif content_type == "text/html" and not body:
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        html = payload.decode('utf-8', errors='replace')
                        # Strip HTML tags
                        body = re.sub('<[^<]+?>', ' ', html)
                        # Clean up extra whitespace
                        body = re.sub(r'\s+', ' ', body).strip()
                except:
                    continue
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode('utf-8', errors='replace')
        except:
            body = str(msg.get_payload())
    
    return body  # Return full body, no truncation

def summarize_email(sender, subject, body):
    """Create a comprehensive summary of the full email"""
    import re
    
    # Clean up body text
    clean_body = body.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.strip() for line in clean_body.split('\n') if line.strip()]
    full_text = ' '.join(lines)
    
    # Extract key info
    word_count = len(full_text.split())
    
    # Detect email purpose/type
    purpose = "General message"
    lower_text = full_text.lower()
    lower_subject = subject.lower()
    
    if any(word in lower_subject for word in ['invoice', 'payment', 'order', 'receipt', 'bill']):
        purpose = "Financial/Transaction"
    elif any(word in lower_subject for word in ['meeting', 'calendar', 'appointment', 'schedule']):
        purpose = "Meeting/Scheduling"
    elif any(word in lower_subject for word in ['alert', 'notification', 'warning', 'important']):
        purpose = "Alert/Notification"
    elif any(word in lower_text for word in ['confirm', 'verification', 'code', 'otp', '2fa']):
        purpose = "Verification/Security"
    elif any(word in lower_text for word in ['ship', 'delivery', 'tracking', 'package']):
        purpose = "Shipping/Delivery"
    
    # Extract key content (first substantial paragraph)
    summary_text = ""
    for line in lines[:10]:  # Check first 10 non-empty lines
        if len(line) > 20 and not line.startswith(('http', 'www', 'From:', 'To:', 'Subject:')):
            summary_text = line[:500]
            break
    
    if not summary_text:
        summary_text = full_text[:400] if full_text else "(No text content)"
    
    # Look for action items
    action_items = []
    action_keywords = ['please', 'required', 'action needed', 'click here', 'verify', 'confirm', 'deadline', 'by tomorrow', 'asap']
    for keyword in action_keywords:
        if keyword in lower_text:
            action_items.append(keyword)
    
    # Build formatted summary (user requested format)
    summary_parts = []
    summary_parts.append(f"📋 Type detected: email from: {sender}")
    summary_parts.append(f"• 📝 Subject: {subject}")
    summary_parts.append(f"• 📄 Full content: \"{summary_text}\"")
    
    return '\n'.join(summary_parts)

def send_telegram_notification(config, sender, subject, summary, message_id):
    """Send notification to Telegram with full email summary"""
    token = config.get('telegram_bot_token')
    chat_id = config.get('telegram_chat_id')
    
    if not token or not chat_id:
        print("⚠️ Telegram not configured, skipping notification")
        return False
    
    # Truncate summary if too long for Telegram (4096 char limit)
    max_len = 3500
    display_summary = summary
    if len(summary) > max_len:
        display_summary = summary[:max_len] + "\n\n... (truncated)"
    
    # Format message (simple format)
    text = f"""📧 New Email

{display_summary}

📨 ID: `{message_id}`"""
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"✅ Telegram notification sent")
            return True
        else:
            print(f"❌ Telegram error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Failed to send Telegram: {e}")
        return False

def check_new_emails(mail, config, seen_uids):
    """Check for new emails and notify"""
    mail.select('INBOX')
    
    # Search for all emails
    status, messages = mail.search(None, 'ALL')
    if status != 'OK':
        print("❌ Failed to search emails")
        return seen_uids
    
    email_ids = messages[0].split()
    new_uids = set()
    
    for e_id in email_ids:
        uid = e_id.decode()
        new_uids.add(uid)
        
        if uid not in seen_uids:
            # Fetch email
            status, msg_data = mail.fetch(e_id, '(RFC822)')
            if status != 'OK':
                continue
            
            # Parse email
            msg = email.message_from_bytes(msg_data[0][1])
            sender = decode_email_header(msg.get('From', 'Unknown'))
            subject = decode_email_header(msg.get('Subject', 'No Subject'))
            
            # Skip if from ourselves
            if 'clawd@fastmail.com' in sender:
                seen_uids.add(uid)
                continue
            
            # Get body and summarize
            body = get_email_body(msg)
            summary = summarize_email(sender, subject, body)
            
            print(f"📧 New email from {sender}: {subject}")
            
            # Send Telegram notification
            send_telegram_notification(config, sender, subject, summary, uid)
            
            seen_uids.add(uid)
    
    # Clean up old UIDs (keep last 1000)
    if len(seen_uids) > 1000:
        seen_uids = set(list(seen_uids)[-500:])
    
    save_seen_uids(seen_uids)
    return seen_uids

def idle_loop(mail, config, seen_uids):
    """Main IDLE loop"""
    last_check = time.time()
    
    while True:
        try:
            # IDLE for config['check_interval'] minutes
            timeout = config.get('check_interval', 1) * 60
            
            print(f"👁️  Entering IDLE mode for {timeout}s...")
            
            # Set up IDLE
            mail.select('INBOX')
            tag = mail._new_tag()
            mail.send(f"{tag} IDLE\r\n".encode())
            
            # Wait for notifications or timeout
            mail.sock.settimeout(timeout)
            
            try:
                while True:
                    try:
                        line = mail.readline()
                        if line.startswith(b'*'):
                            # Something happened!
                            print("📬 IDLE notification received!")
                            break
                    except imaplib.IMAP4.abort:
                        print("⚠️ IDLE timeout, checking manually")
                        break
            finally:
                # Done with IDLE
                try:
                    mail.send(b'DONE\r\n')
                    mail.readline()
                except:
                    pass
            
            # Check for new emails
            seen_uids = check_new_emails(mail, config, seen_uids)
            
        except Exception as e:
            print(f"❌ Error in IDLE loop: {e}")
            time.sleep(10)
            # Reconnect
            try:
                mail.logout()
            except:
                pass
            return False  # Signal to reconnect
    
    return True

def main():
    config = load_config()
    email_addr, password = load_creds()
    seen_uids = load_seen_uids()
    
    print(f"🦞 Fastmail IMAP Monitor starting...")
    print(f"📧 Monitoring: {email_addr}")
    print(f"📱 Telegram: {'Configured' if config.get('telegram_bot_token') else 'NOT CONFIGURED'}")
    print(f"⏱️  IDLE timeout: {config.get('check_interval', 1)} min")
    
    while True:
        try:
            # Connect to IMAP
            print("🔗 Connecting to Fastmail IMAP...")
            mail = imaplib.IMAP4_SSL(config.get('fastmail_imap_server', 'imap.fastmail.com'))
            mail.login(email_addr, password)
            print("✅ Connected to IMAP")
            
            # Initial check
            seen_uids = check_new_emails(mail, config, seen_uids)
            
            # Enter IDLE loop
            if not idle_loop(mail, config, seen_uids):
                continue  # Reconnect
                
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
            break
        except Exception as e:
            print(f"❌ Connection error: {e}")
            print("🔄 Reconnecting in 30s...")
            time.sleep(30)
    
    try:
        mail.logout()
    except:
        pass
    print("✅ Monitor stopped")

if __name__ == '__main__':
    import sys
    main()
