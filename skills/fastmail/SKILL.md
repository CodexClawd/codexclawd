---
name: fastmail
description: Send emails via Fastmail SMTP. Requires app password setup.
---

# Fastmail Integration

Send emails through Fastmail using SMTP.

## Setup

1. Get Fastmail app password: Settings → Privacy & Security → App Passwords → New
2. Store credentials:
   ```bash
   mkdir -p ~/.config/fastmail
   echo 'you@fastmail.com:xxxx-app-password-xxxx' > ~/.config/fastmail/creds
   chmod 600 ~/.config/fastmail/creds
   ```

## Usage

Send email:
```bash
python3 /home/boss/.openclaw/workspace/skills/fastmail/scripts/send.py \
  --to recipient@example.com \
  --subject "Hello" \
  --body "Email body here"
```

HTML email:
```bash
python3 /home/boss/.openclaw/workspace/skills/fastmail/scripts/send.py \
  --to recipient@example.com \
  --subject "Hello" \
  --body "<h1>HTML</h1><p>Content</p>" \
  --html
```
