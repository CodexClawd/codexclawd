---
name: TriageBot
description: Request classifier using tinyllama. Tags incoming tasks and routes them appropriately.
---

# TriageBot 🎯

The bouncer at the door. Parses Flo's requests in <100ms, tags them, decides who handles what.

## Tags

| Tag | Meaning | Route |
|-----|---------|-------|
| `[URGENT]` | Broken, security, needs now | → Kimi |
| `[DEEP_THINK]` | Complex, research, analysis | → Kimi |
| `[QUICK_ANSWER]` | Factual, 1-2 sentences | → Handle locally |
| `[FYI]` | Info only, no response | → Log silently |
| `[AUTOMATION]` | Can be scripted | → Spawn coder subagent |

## Usage

```bash
python3 scripts/triage.py "your request here"
```

## Model

- **tinyllama** on clawd (637MB, fast inference)
- Temperature 0.1 (consistent tagging)
- 10s timeout (fail fast, escalate)
