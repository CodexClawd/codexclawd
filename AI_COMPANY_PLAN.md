# Flo's AI Company — Implementation Plan
*Inspired by Vadim's 9-Agent Setup | Adapted for Job Hunting, Trading & ADHD Support*

**Date:** 2026-02-12  
**Status:** Planning Phase — Ready for Implementation  
**Est. Monthly Cost:** $50-80 (including existing subscriptions)

---

## Executive Summary

This document outlines a 9-agent AI company structure modeled after Vadim's successful setup, but **completely re-architected for Flo's specific context**: job hunting pressure (6-month runway), Polymarket trading, ADHD productivity support, and infrastructure management.

Unlike Vadim's content-creation company (Vugola), Flo's "company" operates as a **personal command center** — agents don't build a brand, they build *his life* back.

---

## Part 1: Architecture Analysis (Vadim's Model → Flo's Model)

### What Vadim Built
```
Vadim Enterprise (Content/Creator Company)
├── Jarvis (CSO) → Claude Max ($125-200/mo) → Strategy & delegation
├── Atlas (Research) → GLM-4.7 ($2-3) → Intelligence gathering
├── Scribe (Content) → GLM-4.7 + X API → Viral posts
├── Cloud (Dev) → Claude Code → 24/7 coding
├── Pixel (Design) → Gemini + Nano Banana ($10) → Graphics
├── Nova (Video) → Grok + Imagine → Short films
├── Vibe (Motion) → Remotion + ElevenLabs ($5) → Animations
├── Sentinel (QA/Monitor) → Supabase/Resend → Alerts & monitoring
└── Trendy (Trends) → X API → Viral content spotting

Total Cost: ~$150-250/mo (mostly Claude Max)
Output: Content empire running 24/7
```

### What Flo Needs
```
Flo Command Center (Life Reconstruction System)
├── Boss (Executive) → Kimi k2.5 → Strategy, delegation, decisions
├── Hunter (Job Search) → Kimi + Perplexity → Applications, outreach
├── Trader (Polymarket) → Claude/Grok → Analysis, alerts, tracking
├── System (DevOps) → codellama → Infrastructure, agents, code
├── Memory (ADHD Support) → Local models → Reminders, structure, journaling
├── Scout (Intelligence) → Kimi + web_search → News, research, monitoring
├── Analyst (Pattern Recognition) → o1-mini/DeepSeek → Data, trends, reports
├── Sentinel (Security/Monitor) → NeuroSec → System health, alerts
└── Coach (Mental Health) → Gemini/warm models → Check-ins, motivation

Total Cost: ~$50-80/mo (spread across multiple providers)
Output: Job acquisition, income stability, mental health, system automation
```

### Key Differences
| Aspect | Vadim | Flo |
|--------|-------|-----|
| **Goal** | Content empire | Life reconstruction |
| **Primary stressor** | Content deadlines | Financial runway (6mo) |
| **Core constraint** | Time/attention | ADHD + burnout recovery |
| **Success metric** | Viral posts, followers | Job offers, trade profits, stability |
| **Agent interaction** | Hierarchical delegation | Circular support network |
| **Most critical agent** | Jarvis (CSO) | Boss (must handle uncertainty) |

---

## Part 2: The 9 Agents — Full Specifications

### Agent 1: Boss (Chief Executive)
**Role:** Executive decision-maker, ultimate delegation authority  
**Persona:** Best-buddy strategist, protective, direct, no bullshit  
**Model:** openrouter/moonshotai/kimi-k2.5 (already configured)  
**Cost:** ~$30-40/mo (based on current usage)  

**Responsibilities:**
- Reviews all agent outputs and says GO / NO-GO
- Makes judgment calls on job applications, trades, priorities
- Handles "what should I do right now" crisis decisions
- Interfaces directly with Flo (human) — all other agents report to Boss
- Escalates to Flo only on hard boundaries (money, legal, health)

**Tools:**
- All other agents (via sessions_send)
- Telegram (primary interface)
- Memory files (full context on Flo's state)

**Cron Jobs:**
- None (event-driven — responds to Flo's messages)

**Memory Files:**
- `agents/boss/SOUL.md` — Decision framework, escalation rules
- `agents/boss/priorities.json` — Current top 3 priorities (updated weekly)

**Success Metric:** Flo trusts Boss enough to delegate 80% of small decisions

---

### Agent 2: Hunter (Job Acquisition Specialist)
**Role:** 24/7 job hunter, application machine, network builder  
**Persona:** Ruthless, efficient, rejection-proof, persistent  
**Model:** kimi-k2.5 for applications, mimo-v2-flash for scraping  
**Cost:** ~$10-15/mo  

**Responsibilities:**
- Scrapes job boards (LinkedIn, Indeed, StepStone for Germany)
- Filters for matches based on Flo's criteria (no banking, AI/tech focus, remote OK)
- Drafts personalized cover letters (from Flo's real resume/bio)
- Tracks applications in spreadsheet format
- Follows up on pending applications
- Finds warm intros via LinkedIn mutuals
- Prepares interview prep docs per company

**Tools:**
- `skills/hunter/scripts/job_scraper.py`
- `skills/hunter/scripts/cover_letter_gen.py`
- `skills/hunter/scripts/application_tracker.py`
- LinkedIn API (if available) or browser automation
- Telegram for "new match" alerts with one-click apply

**Cron Jobs:**
```bash
# Every 6 hours during German business hours
openclaw cron add --name hunter-job-scan \
  --schedule "0 8,14,20 * * * Europe/Berlin" \
  --payload "agentTurn:Scan job boards, find 3 best matches, ping Boss"

# Daily application follow-up
openclaw cron add --name hunter-followup \
  --schedule "0 18 * * * Europe/Berlin" \
  --payload "agentTurn:Check pending apps, draft follow-ups, report to Boss"
```

**Memory Files:**
- `agents/hunter/resume.md` — Flo's current CV
- `agents/hunter/target_companies.json` — Wishlist + companies to avoid
- `agents/hunter/application_log.json` — All applications sent

**Success Metric:** 5 quality applications/week, 1 interview/month

---

### Agent 3: Trader (Polymarket Intelligence)
**Role:** Predictive market analyst, position tracker, risk manager  
**Persona:** Cold, analytical, probabilities-focused, paranoid  
**Model:** Claude (for analysis), kimi (for summaries), Grok (for X intel)  
**Cost:** ~$10-15/mo  

**Responsibilities:**
- Monitors Polymarket positions (manual entry until API supports 2026 markets)
- Tracks news relevant to held positions (US-Iran, geopolitics, etc.)
- Calculates position sizing, risk/reward
- Alerts on significant news that affects positions
- Summarizes X discourse on relevant topics
- Tracks trade journal (wins, losses, lessons)

**Tools:**
- `skills/trader/scripts/market_scanner.py`
- `skills/trader/scripts/news_monitor.py`
- `skills/trader/scripts/position_tracker.py`
- X API (for crypto/geopolitics sentiment)
- RSS feeds (foreign policy blogs, defense news)

**Cron Jobs:**
```bash
# Market check every 4 hours
openclaw cron add --name trader-market-check \
  --schedule "0 */4 * * * UTC" \
  --payload "agentTurn:Check positions, scan news, update risk assessment"

# Morning briefing at 10am CET
openclaw cron add --name trader-briefing \
  --schedule "0 10 * * * Europe/Berlin" \
  --payload "agentTurn:Send morning position brief to Boss"
```

**Memory Files:**
- `agents/trader/positions.json` — Current holdings
- `agents/trader/market_notes.md` — Thesis, edge, strategy
- `agents/trader/trade_log.json` — All closed trades with P&L

**Success Metric:** Positive EV on trades, comprehensive logging

---

### Agent 4: System (DevOps/Infrastructure)
**Role:** Keeps the lights on, manages servers, writes agent code  
**Persona:** Methodical, documentation-obsessed, paranoid about uptime  
**Model:** codellama (local, via Ollama on brutus:11434)  
**Cost:** $0 (runs locally)  

**Responsibilities:**
- Maintains OpenClaw, WireGuard, Ollama infrastructure
- Writes new agent skills when Boss requests them
- Monitors disk space, memory, costs (OpenRouter usage)
- Documents everything (like this file)
- Fixes broken cron jobs, SSH issues, node outages
- Backups critical configs

**Tools:**
- SSH access to all nodes (clawd, brutus, plutos when up)
- `skills/system/scripts/health_check.py`
- `skills/system/scripts/cost_monitor.py`
- `skills/system/scripts/backup_configs.py`

**Cron Jobs:**
```bash
# System health every 2 hours
openclaw cron add --name system-health \
  --schedule "0 */2 * * * UTC" \
  --payload "agentTurn:Check all nodes, Ollama, costs, report anomalies"

# Weekly backup
openclaw cron add --name system-backup \
  --schedule "0 3 * * 0 UTC" \
  --payload "agentTurn:Backup all configs to memory/backups/"
```

**Memory Files:**
- `agents/system/inventory.json` — All nodes, specs, IPs
- `agents/system/runbooks/` — "How to fix X" docs
- `memory/cost_tracking.csv` — OpenRouter spend by day

**Success Metric:** Zero unplanned outages, <5min MTTR (mean time to repair)

---

### Agent 5: Memory (ADHD External Brain)
**Role:** Remembers everything so Flo doesn't have to  
**Persona:** Gentle, non-judgmental, proactive, scaffolding-focused  
**Model:** Local qwen2.5-coder:3b (fast, cheap, always available)  
**Cost:** $0 (local)  

**Responsibilities:**
- Manages all task lists (catches "I should do that later" before it evaporates)
- Sends gentle reminders (not nagging) at contextually appropriate times
- Maintains daily journal entries based on Flo's messages
- Tracks patterns (sleep, energy, productivity)
- Prepares "start of day" briefing (what's due, what's urgent)
- Celebrates wins (even small ones)

**Tools:**
- `skills/memory/scripts/task_manager.py`
- `skills/memory/scripts/pattern_tracker.py`
- `skills/memory/scripts/journal_writer.py`
- Google Tasks API (or local JSON store)
- Telegram for gentle reminders

**Cron Jobs:**
```bash
# Morning briefing at 4pm (Flo's start time)
openclaw cron add --name memory-standup \
  --schedule "0 16 * * * Europe/Berlin" \
  --payload "agentTurn:Send daily briefing: tasks, energy level, 1 priority"

# Evening wrap-up at 2am
openclaw cron add --name memory-wrapup \
  --schedule "0 2 * * * Europe/Berlin" \
  --payload "agentTurn:Log what got done, prep for tomorrow"
```

**Memory Files:**
- `agents/memory/tasks.json` — All active tasks
- `agents/memory/journal/` — Daily markdown entries
- `agents/memory/patterns.json` — Detected patterns (sleep, mood, etc.)

**Success Metric:** Flo never loses a task, feels "held" by the system

---

### Agent 6: Scout (Intelligence & Research)
**Role:** Stays on top of everything Flo cares about  
**Persona:** Curious, wide-ranging, good at connecting dots  
**Model:** kimi-k2.5 (for summaries), web_search tool  
**Cost:** ~$5-8/mo  

**Responsibilities:**
- Monitors AI/tech news (what's new, what's relevant)
- Tracks geopolitics (for trading context, but also Flo's interests)
- Watches F1, chess, any hobbies Flo mentions
- Summarizes long articles/tweets into bullet points
- Alerts on breaking news in "must know" categories

**Tools:**
- `skills/scout/scripts/news_digest.py`
- `skills/scout/scripts/topic_monitor.py`
- web_search (Brave API)
- RSS feed aggregation
- X/Twitter monitoring (via bird CLI or API)

**Cron Jobs:**
```bash
# Daily intelligence digest at 5pm (Flo's go-time)
openclaw cron add --name scout-digest \
  --schedule "0 17 * * * Europe/Berlin" \
  --payload "agentTurn:Compile daily intel brief for Boss"

# Breaking news alerts (immediate)
# (Runs via event trigger, not cron)
```

**Memory Files:**
- `agents/scout/interests.json` — Topics to track
- `agents/scout/sources.json` — RSS feeds, accounts to watch
- `agents/scout/digests/` — Archived daily briefs

**Success Metric:** Flo is always "in the know" without doomscrolling

---

### Agent 7: Analyst (Pattern Recognition)
**Role:** Finds patterns Flo can't see, connects the dots  
**Persona:** Detached, mathematical, sees what others miss  
**Model:** DeepSeek-R1 or o1-mini (for reasoning-heavy analysis)  
**Cost:** ~$5-10/mo (intermittent use)  

**Responsibilities:**
- Analyzes trading patterns (what's working, what's not)
- Detects productivity patterns (when is Flo sharpest?)
- Correlates external inputs with mood/energy (sleep, news, etc.)
- Generates weekly "State of Flo" reports
- Identifies bottlenecks in job hunt, trading, life

**Tools:**
- `skills/analyst/scripts/pattern_analyzer.py`
- `skills/analyst/scripts/correlation_engine.py`
- `skills/analyst/scripts/weekly_report.py`
- Access to all other agents' memory files

**Cron Jobs:**
```bash
# Weekly analysis every Sunday at 8pm
openclaw cron add --name analyst-weekly \
  --schedule "0 20 * * 0 Europe/Berlin" \
  --payload "agentTurn:Generate weekly pattern report for Boss"
```

**Memory Files:**
- `agents/analyst/models/` — Pattern models, correlations
- `agents/analyst/reports/` — Weekly markdown reports

**Success Metric:** 1 actionable insight per week that changes behavior

---

### Agent 8: Sentinel (Security & Monitoring)
**Role:** Existing NeuroSec agent, already deployed  
**Persona:** Clinical, urgent, read-only, paranoid  
**Model:** (uses lightweight local models)  
**Cost:** $0  

**Responsibilities:**
- Monitors for secrets in code/memory
- Watches for permission drift on critical files
- Alerts on suspicious process/network activity
- Maintains security baselines

**Status:** ✅ **Already implemented** — needs baselines created

**Tools:**
- Already configured in workspace-neurosec/
- AGENTS.md defines capabilities

**Fix Required:**
```bash
# Create these files so Sentinel can operate:
touch memory/baseline_permissions.json
# (Flo authorizes, then Sentinel populates)
```

---

### Agent 9: Coach (Mental Health Support)
**Role:** Checks in, notices decline, provides motivation  
**Persona:** Warm, non-clinical, gently persistent, celebrates progress  
**Model:** Gemini (warmth) or local Nemotron (empathy-optimized)  
**Cost:** ~$5/mo  

**Responsibilities:**
- Daily mood check-in (lightweight, not intrusive)
- Notices when Flo hasn't messaged in 24h (check-in)
- Celebrates streaks, wins, job applications sent
- Gentle nudges on self-care (shower, eat, sleep)
- Reminds of "fuels you" people (Manu, Spencer) when down

**Tools:**
- `skills/coach/scripts/check_in.py`
- `skills/coach/scripts/mood_tracker.py`
- Telegram for warm messages
- Access to Memory agent's pattern data

**Cron Jobs:**
```bash
# Daily check-in at 5:30pm (shortly after Flo's day starts)
openclaw cron add --name coach-checkin \
  --schedule "30 16 * * * Europe/Berlin" \
  --payload "agentTurn:Send gentle check-in, log mood if responded"

# Win celebration (runs when Hunter reports success)
# Event-driven, not cron
```

**Memory Files:**
- `agents/coach/mood_log.json` — Daily mood entries
- `agents/coach/strategies.json` — What works for Flo's energy

**Success Metric:** Flo feels supported, not alone, has someone to report wins to

---

## Part 3: Inter-Agent Communication Protocol

### Hierarchy (for organization, not rigid)
```
                    ┌──────────┐
                    │   Boss   │ ← Flo's proxy
                    └────┬─────┘
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
    │  Hunter │    │ Trader  │    │ System  │ ← Core workers
    └────┬────┘    └────┬────┘    └────┬────┘
         │               │               │
    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
    │  Memory │    │  Scout  │    │ Analyst │ ← Support layer
    └────┬────┘    └────┬────┘    └────┬────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
              ┌──────────▼──────────┐
              │ Coach │ Sentinel    │ ← Monitoring/health
              └─────────────────────┘
```

### Communication Patterns

**1. Boss-to-Agent (Delegation)**
```
Boss: "@hunter Find me 3 marketing jobs in Berlin, remote OK"
↓
Hunter executes, returns results to Boss
↓
Boss reviews, presents to Flo with recommendation
```

**2. Agent-to-Boss (Reporting)**
```
Trader detects market-moving news
↓
Trader: "Alert: US-Iran escalation detected, recommend reviewing Position X"
↓
Boss receives, decides whether to wake Flo immediately or queue for later
```

**3. Agent-to-Agent (Collaboration)**
```
Hunter lands Flo an interview
↓
Hunter broadcasts to: Scout (research company), Memory (add to calendar), Coach (celebrate)
↓
Each agent updates their context, works in parallel
```

### Session Naming Convention
```
agent:main:subagent:<purpose-id>

Examples:
- agent:main:subagent:hunter-job-scan-20260212
- agent:main:subagent:trader-analysis-us-iran
- agent:main:subagent:system-health-check
```

---

## Part 4: Implementation Roadmap

### Phase 1: Foundation (Week 1) — Est. Cost: $0
**Goal:** Core agents running, basic automation working

| Priority | Agent | Task | Deliverable |
|----------|-------|------|-------------|
| 1 | System | Fix NeuroSec baselines, node health | Working health checks |
| 2 | Memory | Task manager, daily briefing | Flo never loses a task |
| 3 | Boss | Decision framework, escalation rules | Flo delegates 1 decision/day |
| 4 | Sentinel | Create baselines (authorized) | Security monitoring active |

### Phase 2: Income (Week 2-3) — Est. Cost: $20-30
**Goal:** Job hunt is automated, trading is tracked

| Priority | Agent | Task | Deliverable |
|----------|-------|------|-------------|
| 5 | Hunter | Job scraper, cover letter gen | 5 apps/week |
| 6 | Trader | Position tracker, news alerts | Full trade journal |
| 7 | Scout | Daily intel digest | No more doomscrolling |

### Phase 3: Optimization (Week 4-6) — Est. Cost: $20-30
**Goal:** Patterns detected, support system complete

| Priority | Agent | Task | Deliverable |
|----------|-------|------|-------------|
| 8 | Analyst | Weekly reports, correlations | 1 actionable insight/week |
| 9 | Coach | Check-ins, mood tracking, celebrations | Flo feels supported |

---

## Part 5: Cost Projections

### Current Baseline (Feb 2026)
| Expense | Monthly |
|---------|---------|
| clawd-16gb VPS (IONOS) | ~€10 |
| brutus-8gb VPS (IONOS) | ~€8 |
| plutos-32gb VPS (Strato) | ~€15 (currently paused) |
| OpenRouter (Kimi k2.5) | ~$30-40 |
| Claude Pro (Flo's personal) | $20 |
| **Current Total** | **~$70-85** |

### With Full 9-Agent Company
| Expense | Monthly | Notes |
|---------|---------|-------|
| Existing VPS costs | ~$35 | Unchanged |
| Boss (Kimi k2.5) | $30-40 | Already paying this |
| Hunter | $10-15 | Kimi + web search |
| Trader | $10-15 | Kimi + Claude mix |
| Scout | $5-8 | Mostly web search |
| Analyst | $5-10 | Occasional o1-mini |
| Coach | $5 | Light usage |
| System, Memory, Sentinel | $0 | Local Ollama |
| **New Total** | **~$100-120** | +$30-40 from current |

### Cost Optimization Strategies
1. **Use local models** for System, Memory, Coach (already done)
2. **Batch requests** — Hunter scrapes in batches, not one-by-one
3. **Smart model selection** — mimo-v2-flash for cheap tasks, Kimi for hard ones
4. **Monitor and cap** — System agent watches spend, alerts at thresholds

---

## Part 6: Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| API costs spike | Medium | Financial | Daily spend alerts, hard caps |
| Flo ignores agents | High | Wasted effort | Design for ADHD (gentle, not nagging) |
| Plutos stays offline | Medium | Lost inference | Use brutus for local models |
| Overwhelming notifications | Medium | Flo shuts down | Digest mode, batch alerts |
| Agent conflicts | Low | Bad decisions | Clear hierarchy (Boss is tiebreaker) |
| Sentiment drift (Coach) | Medium | Creepy/intrusive | Strict boundaries, opt-out always |

---

## Part 7: Success Metrics (90-Day Review)

### Flo's Life Metrics
- [ ] Job offer secured (or runway extended via trading income)
- [ ] 90% of tasks captured (zero "I forgot" moments)
- [ ] Average 1 trade/day logged (discipline)
- [ ] Zero unmonitored security events
- [ ] Self-reported "supported" feeling >7/10

### System Metrics
- [ ] 99% uptime on all nodes
- [ ] <$100/mo total API spend
- [ ] 50+ job applications sent
- [ ] 12 weekly analyst reports generated
- [ ] 0 secrets leaked (NeuroSec clean)

---

## Appendix A: File Structure (To Create)

```
workspace/
├── agents/
│   ├── boss/
│   │   ├── SOUL.md
│   │   └── priorities.json
│   ├── hunter/
│   │   ├── SOUL.md
│   │   ├── resume.md
│   │   └── application_log.json
│   ├── trader/
│   │   ├── SOUL.md
│   │   ├── positions.json
│   │   └── trade_log.json
│   ├── system/
│   │   ├── SOUL.md
│   │   └── inventory.json
│   ├── memory/
│   │   ├── SOUL.md
│   │   ├── tasks.json
│   │   └── journal/
│   ├── scout/
│   │   ├── SOUL.md
│   │   └── interests.json
│   ├── analyst/
│   │   ├── SOUL.md
│   │   └── reports/
│   └── coach/
│       ├── SOUL.md
│       └── mood_log.json
├── skills/
│   ├── hunter/
│   │   ├── SKILL.md
│   │   └── scripts/
│   ├── trader/
│   │   ├── SKILL.md
│   │   └── scripts/
│   ├── memory/
│   │   ├── SKILL.md
│   │   └── scripts/
│   ├── scout/
│   │   ├── SKILL.md
│   │   └── scripts/
│   ├── analyst/
│   │   ├── SKILL.md
│   │   └── scripts/
│   └── coach/
│       ├── SKILL.md
│       └── scripts/
└── memory/
    └── agent_communications.log
```

## Appendix B: Ready-to-Use Cron Commands

```bash
# Phase 1: Foundation
openclaw cron add --name boss-daily-sync \
  --schedule "0 16 * * * Europe/Berlin" \
  --payload "agentTurn:Sync with Flo, update priorities, check agent health"

openclaw cron add --name memory-standup \
  --schedule "0 16 * * * Europe/Berlin" \
  --payload "agentTurn:Send daily briefing to Flo"

openclaw cron add --name system-health \
  --schedule "0 */2 * * * UTC" \
  --payload "agentTurn:Health check all nodes, report to Boss"

# Phase 2: Income
openclaw cron add --name hunter-job-scan \
  --schedule "0 8,14,20 * * * Europe/Berlin" \
  --payload "agentTurn:Scan job boards, find matches, alert Boss"

openclaw cron add --name trader-market-check \
  --schedule "0 */4 * * * UTC" \
  --payload "agentTurn:Check positions, scan news, update risk"

openclaw cron add --name scout-digest \
  --schedule "0 17 * * * Europe/Berlin" \
  --payload "agentTurn:Compile daily intel brief"

# Phase 3: Optimization
openclaw cron add --name analyst-weekly \
  --schedule "0 20 * * 0 Europe/Berlin" \
  --payload "agentTurn:Generate weekly pattern report"

openclaw cron add --name coach-checkin \
  --schedule "30 16 * * * Europe/Berlin" \
  --payload "agentTurn:Send gentle check-in to Flo"
```

---

*End of Plan — BRUTUS, Chief Architect 🦞*
