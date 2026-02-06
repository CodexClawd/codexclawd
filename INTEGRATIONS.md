# INTEGRATIONS.md — Platform Connections & Data Flows

**Version:** 1.0  
**Created:** 2026-02-06  
**Status:** Partial — Pending Account Setup

---

## Integration Map

```
┌─────────────────────────────────────────────────────────────┐
│                      BRUTUS CORE                            │
│                    (VPS Server)                             │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
    ┌──────────┴──────────┐      ┌───────────┴──────────┐
    │   COMMUNICATION     │      │   PRODUCTIVITY       │
    │                     │      │                      │
    │ • Telegram ←ACTIVE  │      │ • Gmail ←PENDING     │
    │ • WhatsApp ←LATER   │      │ • Calendar ←PENDING  │
    │                     │      │ • Tasks ←PENDING     │
    └──────────┬──────────┘      │ • Proton ←NO         │
               │                 │ • Notes ←CONSIDER    │
               │                 └───────────┬──────────┘
               │                             │
    ┌──────────┴──────────┐      ┌───────────┴──────────┐
    │   FINANCE/TRADING   │      │   RESEARCH/AI        │
    │                     │      │                      │
    │ • Polymarket ←PLAN  │      │ • Perplexity ←MANUAL │
    │ • Banking ←MANUAL   │      │ • Various LLMs ←MANUAL│
    │ • Excel ←MANUAL     │      │                      │
    └─────────────────────┘      └──────────────────────┘
```

---

## Active Integrations

### Telegram (Active)
**Status:** ✅ Connected  
**Purpose:** Primary interface with Brutus  
**Permissions:**
- Read: All messages in chat
- Send: Messages, files, reminders
- React: Emojis for quick acknowledgment

**Data Flow:**
- You → Telegram → Brutus → Action
- Brutus → Telegram → You

**Security:**
- Bot token stored encrypted
- No message retention beyond session context
- Commands require explicit invocation

---

## Pending Integrations

### Gmail (Pending Setup)
**Status:** 🟡 Waiting for account creation  
**Planned Account:** Dedicated Brutus Gmail (separate from your personal)  
**Purpose:**
- Autonomous email sending on your command
- Draft replies for your approval
- Email alerts and summaries

**Permissions Needed:**
- Read/Search emails
- Compose drafts
- Send emails (on explicit command)
- Label/filter management

**Security Boundary:**
- Never send without your explicit "send it"
- Draft only until confirmed
- No financial/legal emails without double-check

**Setup Steps:**
1. Create new Gmail account (suggested: brutus.flo.assistant@gmail.com)
2. Share credentials securely with Brutus
3. Test send/draft functions
4. Configure alert rules

### Google Calendar (Pending Setup)
**Status:** 🟡 Waiting for account creation  
**Planned Account:** Linked to Brutus Gmail  
**Purpose:**
- Create/modify events
- Remind you before appointments
- Daily/weekly schedule summaries

**Permissions Needed:**
- Read all events
- Create events
- Modify events (on command)
- Delete events (on command)

**Security Boundary:**
- Create freely for your requests
- Modify with confirmation for existing events
- Never delete without explicit "yes delete"

**Setup Steps:**
1. Enable Calendar API on Brutus Gmail
2. Share calendar with your personal calendar (view-only or edit)
3. Configure default reminders
4. Test create/modify/delete

### Google Tasks (Pending Setup)
**Status:** 🟡 Waiting for account creation  
**Planned Account:** Linked to Brutus Gmail  
**Purpose:**
- Capture "I should do that later" before it evaporates
- Manage task lists
- Create tasks from messages
- Daily task summaries

**Permissions Needed:**
- Read all task lists
- Create tasks
- Modify/complete tasks
- Create new task lists

**Security Boundary:**
- Create freely
- Mark complete with confirmation
- Never delete tasks without approval

**Setup Steps:**
1. Enable Tasks API on Brutus Gmail
2. Create default task lists
3. Test create/modify/complete
4. Configure daily task reminders

---

## Planned Integrations

### Polymarket
**Status:** 🔵 Planned  
**Purpose:**
- Track your positions
- Alert on significant moves
- Market opportunity notifications
- Position summaries

**Data Needed:**
- Your wallet address OR
- API access (if available)

**Alert Triggers:**
- Position ±10% change
- New relevant markets
- Settlement approaching
- Liquidation risk

**Security:**
- Read-only monitoring
- Never execute trades
- Alerts only, not trading advice

### X/Twitter
**Status:** 🔵 Planned  
**Purpose:**
- Monitor accounts of interest (geopolitics, trading)
- Track keywords/hashtags
- Draft posts for your approval
- Summarize trends

**Data Needed:**
- Your account (optional for posting)
- List of accounts to monitor
- Keywords to track

**Capabilities:**
- Read timeline
- Draft posts
- Search/summarize
- Track sentiment

**Security:**
- Never post without explicit approval
- Respect rate limits
- No DM access

---

## No Integration (Manual Only)

### Proton Mail
**Status:** 🔴 No integration planned  
**Reason:** Privacy-focused, keep separate  
**Usage:** Manual only

### WhatsApp
**Status:** 🔴 Later  
**Reason:** Complex integration, lower priority  
**Future:** Possible for sending messages on your behalf

### Excel
**Status:** 🔴 Manual  
**Reason:** File-based, complex sync  
**Usage:** Manual upload/download

### Banking/Finance Apps
**Status:** 🔴 Manual  
**Reason:** Too sensitive, never automate  
**Security:** Hard boundary

---

## Data Flow Rules

### What Syncs Automatically
- Calendar events (Brutus calendar → reminders)
- Task list changes
- Polymarket positions (alerts only)
- X/Twitter mentions (optional)

### What Requires Command
- Sending emails
- Creating calendar events
- Marking tasks complete
- Posting to X/Twitter
- Any financial action

### What Never Syncs
- Proton Mail contents
- Banking data
- WhatsApp messages
- Personal documents (unless uploaded)

---

## Integration Priority Queue

| Priority | Integration | Status | ETA |
|----------|-------------|--------|-----|
| 1 | Gmail | 🟡 Pending | This week |
| 2 | Calendar | 🟡 Pending | This week |
| 3 | Tasks | 🟡 Pending | This week |
| 4 | Polymarket | 🔵 Planned | Next week |
| 5 | X/Twitter | 🔵 Planned | Next week |
| 6 | WhatsApp | 🔴 Later | Maybe |

---

## Setup Commands

Once accounts are created:

```
/brutus setup gmail
/brutus setup calendar  
/brutus setup tasks
/brutus setup polymarket
/brutus setup twitter
```

Or natural language:
- "Connect my new Brutus Gmail"
- "Set up calendar integration"
- "Enable Polymarket tracking"

---

**Next Action:** Create dedicated Gmail account for Brutus and share credentials.
