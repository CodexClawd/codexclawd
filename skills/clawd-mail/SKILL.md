---
name: Clawd:Mail
description: Email sending + real-time inbox monitoring for OpenClaw agents. Send via Fastmail SMTP, receive instant Telegram notifications for new emails.
emoji: 📧
---

# Clawd:Mail 📧

Internal email dispatch system for the Brutus mesh.

## Quick Send

```bash
# Simple text email
clawd-mail send to@example.com "Subject" "Body text"

# HTML email
clawd-mail send to@example.com "Subject" "<h1>HTML</h1>" --html

# Direct script usage (auto-CCs flo.schoedl@gmail.com by default)
python3 /home/boss/.openclaw/workspace/skills/clawd-mail/scripts/send.py \
  --to to@example.com \
  --subject "Hello" \
  --body "Message here"

# Without CC
python3 /home/boss/.openclaw/workspace/skills/clawd-mail/scripts/send.py \
  --to to@example.com \
  --subject "Hello" \
  --body "Message here" \
  --cc ""

# With custom CC
python3 /home/boss/.openclaw/workspace/skills/clawd-mail/scripts/send.py \
  --to to@example.com \
  --subject "Hello" \
  --body "Message here" \
  --cc "other@example.com"
```

## Python API

```python
import sys
sys.path.insert(0, '/home/boss/.openclaw/workspace/skills/clawd-mail/scripts')
from send import send_mail

send_mail(
    to="recipient@example.com",
    subject="Subject",
    body="Body",
    html=False,
    cc="flo.schoedl@gmail.com"  # Optional CC
)
```

## Configuration

Creds stored at `~/.config/fastmail/creds`:
```
clawd@fastmail.com:APP_PASSWORD
```

To update credentials:
```bash
chmod 600 ~/.config/fastmail/creds
```

## Scripts

| Script | Purpose |
|--------|---------|
| `send.py` | Core SMTP sender |
| `imap_monitor.py` | Real-time inbox monitor with Telegram notifications |

## IMAP Inbox Monitor (Real-time)

Get instant Telegram notifications when new emails arrive in your Fastmail inbox.

### Setup

**1. Configure Telegram bot:**
```bash
mkdir -p ~/.config/fastmail
cp /home/boss/.openclaw/workspace/skills/clawd-mail/imap_monitor_config.example.json \
   ~/.config/fastmail/monitor_config.json

# Edit config and add your bot token + chat ID
nano ~/.config/fastmail/monitor_config.json
```

**Get your Telegram credentials:**
- Bot token: Message @BotFather → /newbot
- Chat ID: Message @userinfobot

**2. Start the monitor:**
```bash
# Run in foreground (for testing)
python3 /home/boss/.openclaw/workspace/skills/clawd-mail/scripts/imap_monitor.py

# Run in background (production)
nohup python3 /home/boss/.openclaw/workspace/skills/clawd-mail/scripts/imap_monitor.py > /tmp/imap_monitor.log 2>&1 &

# Or with systemd (recommended for auto-start)
sudo systemctl enable --now clawd-mail-monitor
```

### How It Works

- **IMAP IDLE mode**: Stays connected, gets instant push notifications
- **Auto-summarizes**: Extracts sender + subject + body preview
- **Telegram delivery**: Sends formatted message with who sent it and what's about
- **Deduplication**: Tracks seen emails, won't spam you with repeats
- **Auto-reconnect**: Handles network issues gracefully

### Notification Format

```
📧 New Email Received

From: Amazon <orders@amazon.de>
Subject: Your order has shipped

Preview:
Your package is on its way! Track it here: ...

---
Message ID: 12345
```

### Configuration Options

```json
{
  "telegram_bot_token": "123456:ABC...",
  "telegram_chat_id": "123456789",
  "fastmail_imap_server": "imap.fastmail.com",
  "check_interval": 1,        // IDLE timeout in minutes
  "max_summary_length": 500,  // Characters in summary
  "ignore_spam": true,        // Skip spam folder
  "ignore_read": true,        // Skip already-read emails
  "notification_cooldown": 30 // Seconds between notifications
}
```

## Status

✅ Fastmail integration active
📧 Sender: clawd@fastmail.com
