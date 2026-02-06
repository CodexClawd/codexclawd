# WhatsApp Setup for OpenClaw (Output Only)

## Installation

```bash
# Option 1: Using Baileys (recommended, no puppeteer)
npm install @openclaw/whatsapp-baileys

# Option 2: Using whatsapp-web.js (requires puppeteer/chrome)
npm install @openclaw/whatsapp-wwebjs
```

## Configuration

Add to `/home/boss/.openclaw/openclaw.json`:

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      ...
    },
    "whatsapp": {
      "enabled": true,
      "mode": "baileys",
      "outputOnly": true,
      "sessionPath": "/home/boss/.openclaw/whatsapp-session",
      "defaultTarget": "your-phone-number@c.us"
    }
  }
}
```

## First Run (Authentication)

```bash
# Start WhatsApp auth flow
openclaw whatsapp auth

# Or run the setup wizard
openclaw gateway config
# Then select: Add Channel → WhatsApp → Baileys
```

You'll get a QR code. Scan it with WhatsApp on your phone:
1. Open WhatsApp → Settings → Linked Devices
2. Tap "Link a Device"
3. Scan the QR code shown in terminal

## Usage for Reminders

Once connected, cron jobs can send to WhatsApp:

```bash
openclaw cron add \
  --at "2026-02-06T15:00:00Z" \
  --message "💰 Reminder: Get tip for driver" \
  --channel whatsapp
```

Or from task handler, specify channel:
```python
# In reminder_bridge.py
send_whatsapp_message(to="your-number", text=message)
```

## Phone Number Format

Use international format without +:
- German number: `4915112345678@c.us`
- Your number: get from Flo

## Notes

- Baileys stores session in `sessionPath` (no QR scan needed after first time)
- `outputOnly: true` means BRUTUS can send but won't receive WhatsApp messages
- For 2-way (receive messages), set `outputOnly: false`
- Keep phone connected to internet for WhatsApp Web to work
