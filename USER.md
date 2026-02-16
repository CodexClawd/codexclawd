# USER.md - About Your Human

- **Name:** Flo (Boss)
- **What to call them:** Flo or Boss — he answers to both
- **Pronouns:** *(optional)*
- **Timezone:** CET (Europe/Berlin, UTC+1) — convert all times to this
- **Notes:** 
  - Direct, honest communication with loose Gen Z slang
  - ADHD — structure doesn't stick, needs external scaffolding
  - Night owl — sharpest from 4pm onward
  - Gets triggered by repetition (timezone, colors, etc.) — remember once!
  - Interests: projects, automation, AI, tech, F1, geopolitics, chess

---

## Infrastructure Preferences

### Server Naming Convention
| Server | Color | Role |
|--------|-------|------|
| clawd-16gb | 🩷 Pink | Main OpenClaw gateway |
| brutus-8gb | 💛 Yellow | Coding workstation |
| plutos-32gb | ❤️ Red🎳 | Inference beast (32GB RAM) |
| Servitro-001 | 🖤 Gray | Security/VPN hub |

### Active Integrations
- **Fastmail:** `clawd@fastmail.com` — SMTP configured
- **Telegram:** Primary chat channel
- **Gmail:** Planned (separate account for Brutus)
- **Polymarket:** Manual tracking (no API for 2026 markets)
- **RSS/Crypto:** NewsClawd hourly updates

### Cron Jobs Active
- Mesh health check — hourly at :00
- NewsClawd crypto update — hourly at :00
- Daily crypto ping — 15:30 CET

### Friction Points
- Hates repeating myself (told you X 20 times!)
- Wants immediate, actionable commands
- Prefers "do this" over long explanations
- Loses patience with step-by-step hand-holding

### Current Projects
- Building Clawd/Brutus system (this)
- Trading on Polymarket (US-Iran markets)
- Job hunting (6 month runway pressure)
- Learning AI/ML, Linux, programming

### Security Notes
- WiredGuard mesh between VPS nodes
- SSH key auth clawd ↔ brutus via mesh (10.0.0.x)
- Fastmail app password: stored securely
- No sudo on clawd for safety

---

_Last updated: 2026-02-09_