# Agent Registry — v2.0

*Maintained by BRUTUS orchestrator. Updated when agents change.*

## Active Agents

| Agent | Domain | Model | Status | Daily Budget |
|-------|--------|-------|--------|--------------|
| **macro** | Central bank analysis | kimi-k2.5 | ✅ Ready | N/A (cron) |
| **banker** | BBBank/private banking | kimi-k2.5 | ✅ Ready | ~$2 |
| **sentinel** | Infrastructure monitoring | mimo-v2-flash | ✅ Ready | ~$0 |
| **digest** | Morning briefing | mimo-v2-flash | ✅ Ready | ~$0 |
| **neurosec** | Security baselines | local-3b | ✅ Ready | $0 |

## Planned Agents (Phase 2)

| Agent | Domain | Priority | Status |
|-------|--------|----------|--------|
| alpha | Market/stock analysis | High | ⏳ Pending |
| scribe | Communications/drafting | Medium | ⏳ Pending |
| trendy | News scanning | Medium | ⏳ Pending |
| cloud | SSH/server ops | Medium | ⏳ Pending |
| atlas | Deep research | Low | ⏳ Pending |
| pitwall | Motorsport | Low | ⏳ Pending |
| munich | Life management | Low | ⏳ Pending |
| gambit | Chess training | Low | ⏳ Pending |
| mentor | Learning roadmap | Low | ⏳ Pending |
| ledger | Personal finance | Low | ⏳ Pending |
| compliance | Regulatory monitoring | Low | ⏳ Pending |

## Classification Confidence Thresholds

- **>0.90:** Spawn immediately, single agent
- **0.70-0.90:** Spawn with secondary standby, or brief clarification
- **0.50-0.70:** Ask clarifying question
- **<0.50:** Handle directly (unknown domain)

## Multi-Agent Sequences

| Scenario | Sequence |
|----------|----------|
| "How do rates affect BBBank mortgages?" | Macro → Banker → BRUTUS synthesis |
| "What's happening with European banks?" | Trendy scan → Alpha analysis → BRUTUS summary |
| "Prepare me for tomorrow's client meeting" | Macro (context) → Banker (prep) → BRUTUS (briefing) |

## Spawn Command Reference

```
sessions_spawn(agentId="macro", task="[specific instruction with context]")
sessions_spawn(agentId="banker", task="[specific instruction with context]")
```

---
*Last updated: 2026-02-12*
