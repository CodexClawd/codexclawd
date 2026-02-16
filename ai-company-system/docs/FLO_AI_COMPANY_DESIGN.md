# Flo's AI Company — System Design Document

## Executive Summary

A personalized 9-agent autonomous system that functions as Flo's digital company, handling job hunting, Polymarket trading, ADHD productivity support, and system management. Each agent is a specialized "employee" with defined responsibilities, working together through a hierarchical structure with human oversight at critical decision points.

---

## Design Philosophy

### Core Principles

1. **Human-in-the-Loop for High Stakes**
   - Trading decisions > $100 require approval
   - Job applications require Flo's final review
   - System changes affecting files need confirmation

2. **ADHD-Optimized Workflows**
   - Agents handle interruptions so Flo can focus
   - Context-preservation across task switches
   - Proactive reminders without being overwhelming
   - "Focus mode" where non-urgent agents are silenced

3. **Progressive Automation**
   - Start with suggestions, move to automation as trust builds
   - Every agent has a "learning mode" vs "autonomous mode"
   - Easy rollback to manual for any workflow

4. **Transparency First**
   - All agent reasoning visible to Flo
   - Daily digest of what agents did and why
   - Cost tracking per agent (API usage)

---

## Flo's Context Mapping

### Current Challenges → Agent Solutions

| Challenge | Agent Solution | Automation Level |
|-----------|----------------|------------------|
| Job search is overwhelming | **Career Agent** handles sourcing, tailoring, tracking | Semi-automated (Flo approves applications) |
| Miss trading opportunities | **Trading Agent** monitors markets 24/7, alerts on edge | Alerts → Flo decides → Agent executes |
| ADHD focus fragmentation | **Focus Agent** blocks distractions, manages deep work | Fully automated during focus blocks |
| System maintenance forgotten | **SysAdmin Agent** monitors, patches, backs up | Mostly automated with monthly reports |
| Information scattered everywhere | **Knowledge Agent** organizes, connects, surfaces | Fully automated |
| Hard to track progress | **Analytics Agent** dashboards, weekly reviews | Automated reports, Flo reviews |
| Decision fatigue | **Strategist Agent** prioritizes, recommends | Suggestions, Flo decides |
| Communication overhead | **Communications Agent** drafts, schedules, follows up | Drafts for Flo to approve |
| Security blind spots | **Security Agent** (NeuroSec) monitors threats | Automated monitoring + alerts |

---

## The 9-Agent Organization

### Organizational Chart

```
                         ┌─────────────────┐
                         │   STRATEGIST    │
                         │    AGENT #1     │ ← CEO / Priority Setter
                         │  "Archimedes"   │
                         └────────┬────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
      ┌───────▼──────┐   ┌────────▼────────┐  ┌──────▼───────┐
      │    CAREER    │   │     TRADING     │  │    FOCUS     │
      │  AGENT #2    │   │   AGENT #3      │  │  AGENT #4    │ ← Department Heads
      │   "Meridian" │   │  "Oracle"       │  │ "Aegis"      │
      └───────┬──────┘   └────────┬────────┘  └──────┬───────┘
              │                   │                   │
    ┌─────────┴────────┐         │          ┌────────┴────────┐
    │                  │         │          │                 │
┌───▼───┐         ┌────▼────┐   │      ┌───▼───┐        ┌────▼────┐
│KNOWLEDGE│       │SYSADMIN │   │      │COMMS  │        │ANALYTICS│
│AGENT #5 │       │AGENT #6 │   │      │AGENT#7│        │AGENT #8 │
│"Mnemos" │       │"Daedalus"│   │      │"Hermes"│       │"Chronos" │
└─────────┘       └─────────┘   │      └───────┘        └─────────┘
                                │
                         ┌──────▼───────┐
                         │   SECURITY   │
                         │  AGENT #9    │ ← Cross-cutting concern
                         │  "NeuroSec"  │
                         │  (existing)  │
                         └──────────────┘
```

---

## Agent Specifications

### Agent #1: Strategist ("Archimedes")
**Role:** Chief Executive / Priority Orchestrator

**Responsibility:**
- Daily priority setting based on all inputs
- Cross-agent coordination and conflict resolution
- Weekly strategic reviews with Flo
- Resource allocation (Flo's time, attention, capital)

**Model:** Claude 3.5 Sonnet (reasoning + cost balance)

**Tools:**
- All other agents (coordination)
- Calendar API (Google/CalDAV)
- Telegram (daily briefings)
- Notion/Obsidian (planning docs)

**Memory:**
- `/memory/strategic_goals.md` — Long-term objectives
- `/memory/weekly_reviews/` — Performance retrospectives
- `/memory/decision_log.json` — Major decisions and outcomes

**Cron Jobs:**
```bash
# Daily planning (8:00 AM)
openclaw cron add --name "strategist-morning" --schedule "0 8 * * *" \
  --command "run strategist generate-daily-plan"

# Evening review (7:00 PM)  
openclaw cron add --name "strategist-evening" --schedule "0 19 * * *" \
  --command "run strategist daily-review"

# Weekly strategy (Sunday 10:00 AM)
openclaw cron add --name "strategist-weekly" --schedule "0 10 * * 0" \
  --command "run strategist weekly-strategy-session"
```

**Communication:**
- Broadcasts priorities to all agents daily
- Sends Flo morning brief via Telegram
- Escalates conflicts between agents

---

### Agent #2: Career ("Meridian")
**Role:** Job Search & Career Development Manager

**Responsibility:**
- Monitor job boards (LinkedIn, Indeed, niche sites)
- Tailor resumes/CVs per application
- Track application pipeline (applied → interview → offer)
- Research companies and interviewers
- Prepare interview prep materials
- Negotiation support for offers

**Model:** GPT-4o (strong writing + research)

**Tools:**
- LinkedIn API / scraping
- Indeed, Glassdoor APIs
- Google Search (company research)
- Resume parsing (PDF/DOCX)
- Cover letter generation
- Email drafting (Gmail API)

**Memory:**
- `/memory/job_pipeline.json` — Active applications
- `/memory/company_research/` — Research on target companies
- `/memory/resume_versions/` — Tailored resume variants
- `/memory/interview_prep/` — Q&A prep for upcoming interviews

**Cron Jobs:**
```bash
# Job scan (every 6 hours)
openclaw cron add --name "career-job-scan" --schedule "0 */6 * * *" \
  --command "run career scan-job-boards"

# Application follow-ups (daily at 10 AM)
openclaw cron add --name "career-followups" --schedule "0 10 * * *" \
  --command "run career check-follow-ups"

# Pipeline review (weekly)
openclaw cron add --name "career-pipeline-review" --schedule "0 9 * * 1" \
  --command "run career pipeline-report"
```

**Human Touchpoints:**
- Requires Flo approval before submitting any application
- Presents top 3 daily matches with rationale
- Interview prep requires Flo's input on stories/examples

---

### Agent #3: Trading ("Oracle")
**Role:** Polymarket & Financial Opportunity Analyst

**Responsibility:**
- 24/7 market monitoring (Polymarket, prediction markets)
- News/sentiment analysis for market-moving events
- Position sizing and risk calculation
- Alert on high-confidence opportunities
- Trade execution (with approval)
- Portfolio tracking and P&L reporting

**Model:** GPT-4o (complex reasoning + math)

**Tools:**
- Polymarket API
- Web search (breaking news)
- Twitter/X API (sentiment)
- Crypto price feeds
- Risk calculation libraries

**Memory:**
- `/memory/positions.json` — Current holdings
- `/memory/trade_history.json` — All executed trades
- `/memory/market_notes/` — Research on active markets
- `/memory/strategies/` — Backtested strategies

**Cron Jobs:**
```bash
# Market scan (every 5 minutes during market hours)
openclaw cron add --name "trading-market-scan" --schedule "*/5 6-23 * * *" \
  --command "run trading scan-markets"

# News check (every 15 minutes)
openclaw cron add --name "trading-news" --schedule "*/15 * * * *" \
  --command "run trading check-news"

# Daily P&L (9:00 PM)
openclaw cron add --name "trading-pnl" --schedule "0 21 * * *" \
  --command "run trading generate-pnl-report"
```

**Safety Constraints:**
- Max position size: $500 per market
- Daily loss limit: $200 (auto-stop)
- Requires explicit approval for trades > $100
- Never trades in last 30 minutes before resolution

---

### Agent #4: Focus ("Aegis")
**Role:** ADHD Productivity & Deep Work Guardian

**Responsibility:**
- Manage focus blocks (Pomodoro, deep work sessions)
- Block distractions (website blocking suggestions)
- Context restoration after interruptions
- Energy level tracking and task matching
- End-of-day shutdown ritual
- Morning startup routine

**Model:** Claude 3.5 Sonnet (understanding context/emotional states)

**Tools:**
- System notifications
- Telegram (gentle nudges)
- Calendar (focus block scheduling)
- Todo list integration
- Time tracking

**Memory:**
- `/memory/focus_sessions.json` — Historical focus data
- `/memory/interruption_log.json` — What breaks focus
- `/memory/energy_patterns.json` — When Flo is most productive
- `/memory/context_snapshots/` — Saved work contexts

**Cron Jobs:**
```bash
# Morning startup (8:30 AM)
openclaw cron add --name "focus-morning" --schedule "30 8 * * *" \
  --command "run focus morning-routine"

# Check-ins during work hours (every 2 hours)
openclaw cron add --name "focus-checkin" --schedule "0 10,12,14,16 * * 1-5" \
  --command "run focus gentle-checkin"

# Evening shutdown (6:30 PM)
openclaw cron add --name "focus-shutdown" --schedule "30 18 * * *" \
  --command "run focus shutdown-ritual"
```

**ADHD-Specific Features:**
- "Parking lot" for distracting thoughts (capture without breaking flow)
- Context snapshots before breaks (know exactly where to resume)
- Body-doubling mode (agent stays present during focus blocks)
- Task breakdown for overwhelming projects

---

### Agent #5: Knowledge ("Mnemos")
**Role:** Personal Knowledge Manager

**Responsibility:**
- Ingest and organize all information Flo encounters
- Build connections between notes/ideas
- Surface relevant past notes when needed
- Maintain "second brain" in Obsidian/Notion
- Tag and categorize automatically
- Answer questions from personal knowledge base

**Model:** Claude 3.5 Sonnet + Embeddings (vector search)

**Tools:**
- Obsidian API
- Notion API
- File system watcher
- Web clipping
- OCR for screenshots/PDFs
- Vector database (Chroma/Pinecone)

**Memory:**
- `/memory/knowledge_graph.json` — Entity relationships
- `/memory/inbox/` — Unprocessed captures
- `/memory/tags/` — Auto-generated taxonomy
- `/memory/queries.log` — What Flo asks for

**Cron Jobs:**
```bash
# Process inbox (every 2 hours)
openclaw cron add --name "knowledge-process" --schedule "0 */2 * * *" \
  --command "run knowledge process-inbox"

# Daily connections (11 PM)
openclaw cron add --name "knowledge-connections" --schedule "0 23 * * *" \
  --command "run knowledge suggest-connections"

# Weekly knowledge review (Friday 4 PM)
openclaw cron add --name "knowledge-review" --schedule "0 16 * * 5" \
  --command "run knowledge weekly-digest"
```

---

### Agent #6: SysAdmin ("Daedalus")
**Role:** System & Infrastructure Manager

**Responsibility:**
- System health monitoring
- Backup verification
- Update management (security patches)
- Disk space monitoring
- Process monitoring
- Log analysis
- Coordinate with NeuroSec on security

**Model:** GPT-4o-mini (sufficient for sysadmin, cost-effective)

**Tools:**
- System commands (df, ps, netstat)
- Docker management
- Git operations
- SSH to remote systems
- Backup scripts
- Log parsing

**Memory:**
- `/memory/system_baseline.json` — Normal system state
- `/memory/update_history.json` — Patch history
- `/memory/backup_log.json` — Backup verification status

**Cron Jobs:**
```bash
# Health check (every 5 minutes)
openclaw cron add --name "sysadmin-health" --schedule "*/5 * * * *" \
  --command "run sysadmin health-check"

# Backup verification (daily 3 AM)
openclaw cron add --name "sysadmin-backup" --schedule "0 3 * * *" \
  --command "run sysadmin verify-backups"

# Update check (weekly Sunday 2 AM)
openclaw cron add --name "sysadmin-updates" --schedule "0 2 * * 0" \
  --command "run sysadmin check-updates"
```

---

### Agent #7: Communications ("Hermes")
**Role:** Message & Relationship Manager

**Responsibility:**
- Draft responses to emails/messages
- Manage follow-up reminders
- Prepare meeting agendas
- Summarize long threads
- Track important relationships
- Calendar management

**Model:** Claude 3.5 Sonnet (writing quality)

**Tools:**
- Gmail API
- Telegram API
- Calendar API
- Contact management
- Meeting notes

**Memory:**
- `/memory/relationships.json` — Contact history
- `/memory/follow_ups.json` — Pending responses
- `/memory/meeting_notes/` — Archived agendas

**Cron Jobs:**
```bash
# Inbox scan (every 30 minutes during work hours)
openclaw cron add --name "comms-inbox" --schedule "*/30 9-18 * * 1-5" \
  --command "run communications scan-inbox"

# Follow-up check (daily 11 AM)
openclaw cron add --name "comms-followups" --schedule "0 11 * * *" \
  --command "run communications check-follow-ups"
```

---

### Agent #8: Analytics ("Chronos")
**Role:** Data Analyst & Performance Tracker

**Responsibility:**
- Aggregate data from all agents
- Generate dashboards and reports
- Track progress toward goals
- Identify patterns and insights
- Cost tracking (API usage)
- Weekly/monthly performance reviews

**Model:** Claude 3.5 Sonnet (analysis + visualization planning)

**Tools:**
- Data aggregation from all agents
- Chart generation (matplotlib, plotly)
- SQL queries on agent logs
- CSV/Excel export

**Memory:**
- `/memory/metrics.json` — Key performance indicators
- `/memory/cost_tracking.json` — API spend by agent
- `/memory/goal_progress.json` — Progress toward objectives

**Cron Jobs:**
```bash
# Daily metrics (9:30 PM)
openclaw cron add --name "analytics-daily" --schedule "30 21 * * *" \
  --command "run analytics daily-report"

# Weekly review (Sunday 6 PM)
openclaw cron add --name "analytics-weekly" --schedule "0 18 * * 0" \
  --command "run analytics weekly-review"

# Monthly deep analysis (last day of month)
openclaw cron add --name "analytics-monthly" --schedule "0 9 28-31 * *" \
  --command "run analytics monthly-deep-dive"
```

---

### Agent #9: Security ("NeuroSec")
**Role:** Security Monitoring & Threat Detection

**Status:** ✅ ALREADY IMPLEMENTED

See existing NeuroSec configuration at `/workspace/AGENTS.md`

**Responsibility:**
- Monitor all agent activities for security issues
- Secret detection in generated files
- Permission auditing
- Alert on suspicious patterns
- Cross-agent security coordination

---

## Inter-Agent Communication Protocol

### Message Types

```json
{
  "message": {
    "id": "uuid-v4",
    "timestamp": "2026-02-12T12:00:00Z",
    "from": "agent_id",
    "to": "agent_id|broadcast|human",
    "type": "task|alert|query|response|handoff|broadcast",
    "priority": 1-5,
    "ttl": 3600,
    "payload": { ... },
    "context": {
      "session_id": "...",
      "chain": ["msg-1", "msg-2"],
      "requires_human": false
    }
  }
}
```

### Communication Patterns

1. **Task Assignment**
   ```
   Strategist → Career: {"type": "task", "action": "prioritize_jobs", "deadline": "..."}
   Career → Strategist: {"type": "response", "result": [...]}
   ```

2. **Alert Broadcasting**
   ```
   Trading → broadcast: {"type": "alert", "severity": "high", "market": "..."}
   ```

3. **Handoff**
   ```
   Focus → Knowledge: {"type": "handoff", "context": "research_session", "data": {...}}
   ```

4. **Human Approval Request**
   ```
   Trading → human: {"type": "query", "action": "execute_trade", "details": {...}}
   ```

---

## Telegram Integration

### Channel Structure

| Channel | Purpose | Agents |
|---------|---------|--------|
| `#ai-company-alerts` | Critical alerts only | All (priority 1-2) |
| `#trading-signals` | Trading opportunities | Trading, Strategist |
| `#career-updates` | Job matches, interview prep | Career |
| `#focus-companion` | Focus session support | Focus |
| `#daily-briefing` | Morning/evening summaries | Strategist |
| `#system-health` | System/security alerts | SysAdmin, NeuroSec |

### Message Format

```
🤖 [AGENT NAME]

📋 ACTION / ALERT / UPDATE

Details...

🔘 [Approve] [Reject] [More Info]  ← Interactive buttons where applicable
```

---

## Implementation Priority Roadmap

### Phase 1: Foundation (Week 1-2)
**Goal:** Core infrastructure + 3 essential agents

- [ ] Set up shared memory architecture
- [ ] Implement message bus
- [ ] Deploy **Strategist** (essential for coordination)
- [ ] Deploy **Focus** (immediate ADHD benefit)
- [ ] Deploy **Trading** (Flo's active priority)
- [ ] Basic Telegram integration

### Phase 2: Career & Knowledge (Week 3-4)
**Goal:** Add high-impact agents

- [ ] Deploy **Career** (job search automation)
- [ ] Deploy **Knowledge** (information organization)
- [ ] Connect to Obsidian/Notion
- [ ] LinkedIn integration

### Phase 3: Operations (Week 5-6)
**Goal:** Full system coverage

- [ ] Deploy **SysAdmin**
- [ ] Deploy **Communications**
- [ ] Deploy **Analytics**
- [ ] Full inter-agent coordination

### Phase 4: Optimization (Week 7+)
**Goal:** Polish and cost optimization

- [ ] Model tier optimization (switch to cheaper models where appropriate)
- [ ] Caching layer implementation
- [ ] Advanced automation rules
- [ ] Weekly performance reviews

---

## Cost Estimates

### Daily API Usage (Projected)

| Agent | Requests/Day | Model | Cost/Day |
|-------|--------------|-------|----------|
| Strategist | 50 | Claude 3.5 Sonnet | $0.75 |
| Career | 30 | GPT-4o | $1.50 |
| Trading | 200 | GPT-4o-mini | $0.60 |
| Focus | 40 | Claude 3.5 Sonnet | $0.60 |
| Knowledge | 20 | Claude 3.5 Sonnet | $0.30 |
| SysAdmin | 288 | GPT-4o-mini | $0.40 |
| Communications | 20 | Claude 3.5 Sonnet | $0.30 |
| Analytics | 5 | Claude 3.5 Sonnet | $0.08 |
| NeuroSec | 100 | GPT-4o-mini | $0.15 |
| **TOTAL** | | | **~$4.68/day** |

**Monthly Estimate: ~$140**

### Cost Optimization Strategies

1. **Model Tiering**: Use GPT-4o-mini for routine tasks
2. **Caching**: Cache similar queries (30% reduction possible)
3. **Batching**: Combine small requests
4. **Selective Activation**: Disable non-essential agents during sleep hours

---

## Success Metrics

### 30-Day Goals
- [ ] Trading agent generates 3+ actionable alerts/week
- [ ] Career agent surfaces 5+ quality job matches/week
- [ ] Focus agent facilitates 20+ hours of deep work
- [ ] Zero missed critical alerts
- [ ] System uptime >99%

### 90-Day Goals
- [ ] 50% reduction in Flo's manual job search time
- [ ] Profitable trading assistance (positive EV)
- [ ] Fully autonomous daily planning
- [ ] Complete knowledge base migration
- [ ] < $100/month API costs

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| API costs balloon | Daily spend caps, model tiering, alerts at $5/day |
| Agents conflict | Clear ownership boundaries, Strategist arbitration |
| Trading losses | Position limits, mandatory approval, stop-losses |
| Job application errors | Human approval gate, double-check drafts |
| System overload | Rate limiting, priority queues, agent sleep schedules |
| Over-reliance | Manual override for all agents, weekly human review |

---

## Appendix: Naming Convention

Agents are named after mythological figures representing their domain:

| Agent | Name | Origin | Meaning |
|-------|------|--------|---------|
| 1 | Archimedes | Greek | Master strategist, "Eureka!" moments |
| 2 | Meridian | Latin | Peak/culmination, career pinnacle |
| 3 | Oracle | Greek | Prophecy, prediction markets |
| 4 | Aegis | Greek | Protection, shield (focus guardian) |
| 5 | Mnemos | Greek | Memory, Mnemosyne (memory goddess) |
| 6 | Daedalus | Greek | Master craftsman, builder |
| 7 | Hermes | Greek | Messenger, communication |
| 8 | Chronos | Greek | Time, analytics/history |
| 9 | NeuroSec | Modern | Neural security (existing) |

---

*Document Version: 1.0*
*Created: 2026-02-12*
*For: Flo's Personal AI Company*
