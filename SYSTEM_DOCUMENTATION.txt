# Clawd/Brutus System Documentation
**For New Developers**

*Last Updated: 2026-02-12*
* Maintained by: BRUTUS AI Agent*

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Server Infrastructure](#server-infrastructure)
4. [Network Topology (WireGuard Mesh)](#network-topology-wireguard-mesh)
5. [OpenClaw Configuration](#openclaw-configuration)
6. [Skills Registry](#skills-registry)
7. [Cron Jobs & Automation](#cron-jobs--automation)
8. [Security & Monitoring (NeuroSec)](#security--monitoring-neurosec)
9. [Directory Structure](#directory-structure)
10. [Development Workflow](#development-workflow)
11. [Known Issues](#known-issues)
12. [Quick Commands](#quick-commands)

---

## Executive Summary

**Clawd/Brutus** is a personal AI assistant infrastructure built on OpenClaw, serving Flo (User: @notabanker1, Munich, CET timezone). The system runs across multiple VPS nodes connected via WireGuard mesh VPN, with the primary agent (BRUTUS) operating on the `clawd-16gb` node.

### Primary Purpose
- Personal AI assistant for task management, monitoring, and automation
- Distributed LLM inference via Ollama cluster
- Crypto/news monitoring and alerting
- Security monitoring via NeuroSec agent

### Key Vibe
- Direct, best-buddy communication style
- Gen-Z slang allowed, corporate speak banned
- ADHD-aware: external scaffolding for structure
- Night-owl optimized (active 4pm-2am CET)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE LAYER                            │
├─────────────────────────────────────────────────────────────────────────┤
│  Telegram (@notabanker1)  │  Web Chat  │  (Future: WhatsApp, Signal)   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        OPENCLAW GATEWAY (clawd)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐   │
│  │   BRUTUS    │  │   NeuroSec  │  │  Subagents  │  │   Cron Jobs  │   │
│  │  (Main AI)  │  │ (Security)  │  │  (Spawned)  │  │  (Scheduled) │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────────────┘   │
│                                                                         │
│  Default Model: openrouter/moonshotai/kimi-k2.5                        │
│  Fallback: openrouter/xiaomi/mimo-v2-flash                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ WireGuard Mesh (10.0.0.0/24)
┌─────────────────────────────────────────────────────────────────────────┐
│                        INFRASTRUCTURE LAYER                             │
├──────────────────┬──────────────────┬──────────────────┬────────────────┤
│    NEXUS/        │    CLAWD-16GB    │    BRUTUS-8GB    │   PLUTOS-32GB  │
│  Servitro-001    │   (10.0.0.2)     │   (10.0.0.3)     │   (10.0.0.4)   │
│   (10.0.0.1)     │                  │                  │                │
├──────────────────┼──────────────────┼──────────────────┼────────────────┤
│  WireGuard Hub   │  OpenClaw GW     │  Coding Agent    │  Inference     │
│  Security Bastion│  Telegram Bot    │  Ollama Server   │  (14B+ models) │
│  Jump Host       │  Ollama Server   │                  │                │
└──────────────────┴──────────────────┴──────────────────┴────────────────┘
       │                   │                   │                   │
       └───────────────────┴───────────────────┴───────────────────┘
                                    │
                         Ollama Distributed Cluster
                         (models: qwen2.5-coder, nemotron-mini,
                          deepseek-r1, codellama, llama3.1)
```

---

## Server Infrastructure

### Node 1: Nexus (Servitro-001) — Security Hub
| Attribute | Value |
|-----------|-------|
| **Provider** | Servitro.com |
| **Cost** | $12/year ($1/month) |
| **Location** | Frankfurt, Germany |
| **Public IP** | (Assigned by provider) |
| **WireGuard IP** | 10.0.0.1 |
| **Hostname** | servitro-001 |
| **vCPUs** | 1 (AMD EPYC 7443P) |
| **RAM** | 1 GB DDR4 |
| **Storage** | 10 GB SSD |
| **OS** | Ubuntu 24.04 LTS |
| **Role** | WireGuard hub, security bastion, jump host |
| **Status** | ⚠️ SSH connection refused (needs investigation) |
| **Fail2ban** | ✅ Configured |

**Purpose:** Central entry point for WireGuard mesh. Acts as hub for star topology fallback.

**Access Issues:** Currently responds to ping but SSH connection refused. Likely fail2ban block or SSH daemon issue.

---

### Node 2: Clawd-16gb — Primary Gateway
| Attribute | Value |
|-----------|-------|
| **Provider** | IONOS |
| **Location** | Germany |
| **Public IP** | 85.215.46.147 |
| **WireGuard IP** | 10.0.0.2 |
| **Color Code** | 🩷 Pink |
| **Hostname** | clawd-16gb |
| **vCPUs** | 8 (AMD EPYC-Milan, 4c/8t) |
| **RAM** | 16 GB DDR4 (~14 GB free) |
| **Storage** | 480 GB NVMe SSD (~434 GB free) |
| **OS** | Ubuntu 24.04 LTS |
| **OpenClaw** | 2026.2.6-3 |
| **Node.js** | v22.22.0 |
| **Docker** | v28.2.2 |
| **Ollama** | v0.15.5 |
| **Models** | llama3.1 (4.9GB), codellama (3.8GB), qwen2.5-coder:3b, deepseek-r1:1.5b |
| **Role** | OpenClaw Gateway, Telegram Bot, main API hub |
| **Status** | ✅ Operational |
| **Fail2ban** | ✅ Active |

**Primary Services:**
- OpenClaw Gateway daemon
- Telegram bot (@brutusclawdbot)
- Ollama inference endpoint (localhost:11434)
- WireGuard peer (wg0 interface)
- Cron scheduler

**Key Processes:**
```
/usr/sbin/cron -f -P                    # Cron daemon
openclaw-gateway                        # Main gateway process
ollama serve                            # LLM inference server
```

---

### Node 3: Brutus-8gb — Coding Workstation
| Attribute | Value |
|-----------|-------|
| **Provider** | IONOS |
| **Location** | Germany |
| **Public IP** | 87.106.6.144 |
| **WireGuard IP** | 10.0.0.3 |
| **Color Code** | 💛 Yellow |
| **Hostname** | brutus-8gb |
| **vCPUs** | 6 (AMD EPYC-Milan, 3c/6t) |
| **RAM** | 8 GB DDR4 (~7 GB free) |
| **Storage** | 232 GB SSD (~221 GB free) |
| **OS** | Ubuntu 24.04 LTS |
| **Ollama** | v0.15.5 |
| **Models** | nemotron-mini:4b, qwen2.5-coder:3b |
| **Role** | Coding agent, secondary inference node |
| **Status** | ✅ Operational |
| **Fail2ban** | ✅ Active |

**Access:** SSH via mesh: `ssh boss@10.0.0.3`

**Services:**
- Ollama server (accessible via mesh)
- Code generation workloads

---

### Node 4: Plutos-32gb — Inference Beast
| Attribute | Value |
|-----------|-------|
| **Provider** | Strato.com |
| **Location** | Germany |
| **WireGuard IP** | 10.0.0.4 |
| **Color Code** | ❤️ Red |
| **Hostname** | plutos-32gb / plutos🎳 |
| **RAM** | 32 GB DDR4 |
| **Role** | Heavy inference (14B+ parameter models) |
| **Status** | 🔴 **OFFLINE** — Invoice pending payment |

**Note:** Node suspended by Strato due to unpaid invoice. Flo will restore when payment processed.

---

### Control Station: Private Mac Mini M1
| Attribute | Value |
|-----------|-------|
| **Device** | Mac Mini M1 |
| **CPU** | Apple Silicon M1 (8-core) |
| **RAM** | 8 GB Unified Memory |
| **Storage** | 512 GB local + 2 TB Google Cloud + 2 TB iCloud |
| **OS** | macOS |
| **Role** | Terminal control center, VS Code remote dev |
| **SSH Config** | Host entries for all VPS nodes |

---

## Network Topology (WireGuard Mesh)

### Mesh Configuration
```
Network: 10.0.0.0/24
Protocol: WireGuard (UDP 51820)
Topology: Full mesh (intended), currently partial mesh
```

### Current Status (2026-02-12)
| Node | WG IP | Status | Latency | Notes |
|------|-------|--------|---------|-------|
| Nexus | 10.0.0.1 | ⚠️ Degraded | ~40ms | Ping OK, SSH refused |
| Clawd | 10.0.0.2 | ✅ Online | 0.05ms | Local host |
| Brutus | 10.0.0.3 | ✅ Online | ~50ms | Healthy |
| Plutos | 10.0.0.4 | 🔴 Offline | — | Invoice suspended |

### WireGuard Interface (clawd)
```bash
$ ip addr show wg0
6: wg0: <POINTOPOINT,NOARP,UP,LOWER_UP>
    inet 10.0.0.2/24 scope global wg0
    MTU: 1420
```

### /etc/hosts Configuration
```
10.0.0.1    nexus
10.0.0.3    brutus
# 10.0.0.4  plutos (currently offline)
```

### Connectivity Matrix
| From/To | Nexus | Clawd | Brutus | Plutos |
|---------|-------|-------|--------|--------|
| Nexus | — | ✅ | ? | ? |
| Clawd | ⚠️ | — | ✅ | 🔴 |
| Brutus | ? | ✅ | — | 🔴 |
| Plutos | 🔴 | 🔴 | 🔴 | — |

Legend: ✅ Working | ⚠️ Partial | 🔴 Down | ? Untested

---

## OpenClaw Configuration

### Global Config (`~/.openclaw/config.json`)
```json
{
  "agents": {
    "defaults": {
      "provider": "openrouter",
      "model": "xiaomi/mimo-v2-flash"
    }
  }
}
```

### Runtime Defaults
| Setting | Value |
|---------|-------|
| Default Provider | OpenRouter |
| Default Model | kimi-k2.5 (openrouter/moonshotai/kimi-k2.5) |
| Fallback Model | mimo-v2-flash (openrouter/xiaomi/mimo-v2-flash) |
| Gateway Version | 2026.2.6-3 |
| Primary Channel | Telegram (@notabanker1) |

### Agent Identity Files
| File | Purpose |
|------|---------|
| `IDENTITY.md` | Who BRUTUS is, server colors, infrastructure |
| `SOUL.md` | Personality, tone, communication rules |
| `MEMORY.md` | User profile, preferences, triggers |
| `USER.md` | Quick reference for Flo's preferences |
| `AGENTS.md` | NeuroSec security agent configuration |

### Channel Configuration
- **Telegram**: Primary, enabled with inline buttons
- **WhatsApp**: Session exists but not actively used
- **Web Chat**: Via OpenClaw web interface

---

## Skills Registry

Skills are self-contained modules in `workspace/skills/`.

### Active Skills

| Skill | Location | Purpose | CLI | Status |
|-------|----------|---------|-----|--------|
| **newsclawd** | `skills/newsclawd/` | Crypto/news monitoring, hourly digests | — | ✅ Active |
| **clawd-mail** | `skills/clawd-mail/` | Fastmail SMTP integration | `clawd-mail` | ✅ Active |
| **fastmail** | `skills/fastmail/` | Email sending | — | ✅ Configured |
| **openrouter-analyzer** | `skills/openrouter-analyzer/` | Cost/usage analysis from CSV | Python scripts | ✅ Installed |
| **gog** | `skills/gog/` | Google Workspace integration | `gog` | ⚠️ OAuth pending |
| **sonoscli** | `skills/sonoscli/` | Sonos speaker control | `sonoscli` | ✅ Installed |
| **triagebot** | `skills/triagebot/` | Request classifier (tinyllama) | — | ✅ Installed |
| **agentskills-io** | `skills/agentskills-io/` | Skills standard validation | — | ✅ Dev tool |
| **clawdbot-truth** | `skills/clawdbot-truth/` | Bot personality module | — | ✅ Active |
| **binance** | `skills/binance/` | Crypto exchange API | — | ✅ Configured |

### Skill Structure Pattern
```
skills/<name>/
├── SKILL.md          # Documentation + usage
├── scripts/          # Implementation scripts
│   ├── monitor.py
│   ├── notify.py
│   └── ...
└── references/       # External docs, specs
```

### NewsClawd Architecture
**Purpose:** Hourly monitoring and alerting

**Components:**
- Mesh health checks (pings all nodes)
- Ollama status checks (API calls to 10.0.0.3:11434)
- Crypto price fetching (Coinbase/CoinGecko)
- Telegram digest delivery

**Config Location:** `~/.config/newsclawd/config.json` (if exists)

---

## Cron Jobs & Automation

### Active Cron Jobs

| ID | Name | Schedule | Target | Agent | Status |
|----|------|----------|--------|-------|--------|
| `91361d22-...` | hourly-mesh-confirmation | `0 * * * *` (every hour :00) | isolated | main | ✅ Active |
| `d2408ac4-...` | hourly-newsclawd-update | `0 * * * *` (every hour :00) | isolated | main | ✅ Active |

### Job Details

#### hourly-mesh-confirmation
- **Purpose:** Verify all mesh nodes are online
- **Output:** Logs to `memory/mesh_status_latest.json`
- **Issues:** Intermittent JSON errors, tool failures

#### hourly-newsclawd-update
- **Purpose:** Full system digest (mesh + crypto + usage)
- **Output:** Attempts delivery to @brutusclawdbot
- **Issues:** Delivery often fails ("chat not found")

### Cron Log Location
```
~/.openclaw/cron/
```

---

## Security & Monitoring (NeuroSec)

### NeuroSec Agent
- **Classification:** Read-only security monitor
- **Persona:** Clinical, urgent, precise
- **Constraint:** NEVER modifies files (detection only)

### Required Baseline Files (MISSING)
NeuroSec cannot operate fully without these — they need to be created:

| File | Purpose | Status |
|------|---------|--------|
| `memory/baseline_permissions.json` | File permission baseline | 🔴 Missing |
| `memory/network_baseline.json` | Expected listening ports | 🔴 Missing |
| `memory/known_secrets.json` | Hashed known secrets | 🔴 Missing |

### Security Checklist
- [x] SSH key-based auth (clawd ↔ brutus)
- [x] Fail2ban on all nodes
- [x] WireGuard mesh encryption
- [ ] NeuroSec baselines (pending)
- [ ] Servitro hardening (pending)

---

## Directory Structure

### Home Directory (`~/.openclaw/`)
```
~/.openclaw/
├── agents/                 # Agent definitions
├── bin/                    # CLI binaries
├── canvas/                 # Canvas outputs
├── completions/            # Shell completions
├── config.json             # Global config
├── credentials/            # Secure creds storage
├── cron/                   # Cron job data
├── devices/                # Paired device info
├── identity/               # Identity artifacts
├── media/                  # Generated media
├── notifications/          # Notification templates
├── openclaw.json           # Gateway config (main)
├── subagents/              # Subagent state
├── telegram/               # Telegram session data
├── whatsapp-session/       # WhatsApp session
├── workspace/              # ⭐ MAIN WORKSPACE
│   ├── skills/             # All agent skills
│   ├── memory/             # Logs, status, history
│   ├── alerts/             # NeuroSec alerts
│   ├── SOUL.md
│   ├── IDENTITY.md
│   ├── MEMORY.md
│   ├── USER.md
│   ├── AGENTS.md
│   └── ...
└── workspace-neurosec/     # NeuroSec workspace (isolated)
```

### Workspace (`workspace/`)
```
workspace/
├── skills/                 # 15+ skills (see Skills Registry)
├── memory/
│   ├── mesh_status_latest.json
│   ├── mesh_status.json
│   ├── mesh_history.log
│   ├── *.md (dated notes)
│   └── mesh_monitor/
├── alerts/                 # Security alerts
└── [agent config files]
```

---

## Development Workflow

### Testing Changes
```bash
# Restart OpenClaw after config changes
openclaw gateway restart

# Check status
openclaw status

# View cron jobs
openclaw cron list

# View cron run history
openclaw cron runs --job-id <id>
```

### Skill Development
1. Create directory: `mkdir workspace/skills/<name>/`
2. Add `SKILL.md` with documentation
3. Add scripts in `scripts/` subdirectory
4. Test manually before integration

### SSH Access Pattern
```bash
# To brutus from clawd
ssh boss@10.0.0.3

# Check node status
ping 10.0.0.1  # Nexus
ping 10.0.0.3  # Brutus
ping 10.0.0.4  # Plutos (currently down)
```

---

## Known Issues

| Issue | Severity | Status | Owner |
|-------|----------|--------|-------|
| Plutos offline (invoice) | 🔴 High | Awaiting payment | Flo |
| Nexus SSH refused | 🟡 Medium | Needs investigation | Dev |
| NeuroSec baselines missing | 🟡 Medium | Needs creation | Dev |
| Cron job contention at :00 | 🟡 Medium | Should offset | Dev |
| @brutusclawdbot delivery fails | 🟡 Medium | Config issue | Dev |
| Ollama on clawd bound to localhost | 🟢 Low | Config change | Dev |
| Ghost skill directories (.skill suffix) | 🟢 Low | Cleanup | Dev |
| Price delta tracking lost | 🟢 Low | Restore history | Dev |

---

## Quick Commands

### System Status
```bash
# OpenClaw status
openclaw status

# Gateway info
openclaw gateway config.get

# Cron jobs
openclaw cron list

# Node connectivity
for ip in 10.0.0.1 10.0.0.3 10.0.0.4; do ping -c1 -W3 $ip; done

# Ollama status (brutus)
curl -s http://10.0.0.3:11434/api/tags | jq '.models[].name'
```

### Development
```bash
# Edit workspace files
cd ~/.openclaw/workspace
ls skills/
ls memory/

# View logs
tail -f ~/.openclaw/logs/*.log

# Restart services
sudo systemctl restart openclaw  # If systemd
# OR
openclaw gateway restart
```

---

## Contact & Context

**Human Operator:** Flo (@notabanker1 on Telegram/X)
**Location:** Munich, Germany (CET/UTC+1)
**Primary AI:** BRUTUS (clawd-16gb node)
**Security AI:** NeuroSec (read-only monitor)

### User Context (Important for Development)
- **ADHD diagnosed:** Needs external structure, forgets things
- **Night owl:** Sharp after 4pm CET
- **Stress triggers:** Repeating instructions, corporate speak
- **Current pressure:** ~6 months financial runway, job hunting
- **Interests:** AI, automation, geopolitics, F1, chess

---

*End of Documentation — Generated by BRUTUS 🦞*
