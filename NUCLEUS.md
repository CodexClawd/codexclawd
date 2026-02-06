# NUCLEUS.md — Model Strategy & AI Tool Configuration

**Version:** 1.0  
**Created:** 2026-02-06  
**Last Updated:** 2026-02-06

---

## Your Model Arsenal

### Primary (Default)
**`openrouter/moonshotai/kimi-k2.5`**
- **Role:** Daily driver, main assistant (Brutus)
- **Why:** Fast, capable, cost-effective, you like it
- **Use for:** General chat, task management, brainstorming, most queries
- **Thinking Level:** Low (fast responses)

### Available Models

| Model | Alias/Role | Best For | Cost |
|-------|-----------|----------|------|
| `openrouter/moonshotai/kimi-k2.5` | Brutus (Default) | General purpose, daily use | Paid |
| `openrouter/nvidia/nemotron-3-nano-30b-a3b:free` | Free option | Light tasks, testing, cost-sensitive | Free |
| `openrouter/free` | OpenRouter Free | Fallback, simple queries | Free |
| `openrouter/x-ai/grok-code-fast-1` | Grok | Coding tasks, quick technical work | Paid |
| `openrouter/deepseek/deepseek-v3.2` | DeepSeek | Reasoning, analysis, complex problems | Paid |
| `openrouter/stepfun/step-3.5-flash:free` | Step Free | Fast free responses | Free |
| `openrouter/xiaomi/mimo-v2-flash` | Mimo | Quick tasks | Paid |
| `google-antigravity/claude-opus-4-5-thinking` | Claude | Deep reasoning, long context, careful analysis | Paid |

### External Models (Manual Use)

| Model | Access | Use Case |
|-------|--------|----------|
| ChatGPT (OpenAI) | Direct | When you want GPT specifically |
| Gemini (Google) | Direct | Google ecosystem tasks |
| Claude (Anthropic) | Direct + via OpenRouter | Deep analysis, coding |

---

## Model Selection Strategy

### By Task Type

**Quick Chat / Daily Operations:**
- Primary: Kimi-k2.5
- Fallback: Grok-code-fast-1

**Complex Reasoning / Analysis:**
- Primary: DeepSeek-v3.2
- Heavy lifting: Claude-opus-4-5-thinking

**Coding:**
- Fast: Grok-code-fast-1
- Deep: Claude-opus-4-5-thinking
- General: Kimi-k2.5

**Cost-Sensitive / Testing:**
- Free tier: OpenRouter/free
- Light tasks: Nemotron-3-nano (free)

**Research / Geopolitics:**
- Analysis: DeepSeek-v3.2
- Summarization: Kimi-k2.5

### By Urgency

| Urgency | Model | Response Time |
|---------|-------|---------------|
| Immediate | Kimi-k2.5 / Grok-code-fast-1 | <5s |
| Normal | Kimi-k2.5 | <10s |
| Deep work | DeepSeek / Claude | 15-30s |
| Background | Any free model | Variable |

---

## Usage Patterns

### Your Current Mix (Observed)

1. **Kimi-k2.5** — Daily driver, main interactions
2. **Grok** — Code, quick technical stuff
3. **ChatGPT** — General purpose, familiar
4. **Gemini** — Google ecosystem
5. **Claude** — Deep reasoning, careful work

### Brutus's Role

Brutus (Kimi-k2.5) orchestrates — knows when to:
- Handle directly (most things)
- Spawn sub-agent with different model (complex tasks)
- Recommend you use specific model for specific task

---

## Model Preferences by Context

### Telegram / Quick Messages
- **Default:** Kimi-k2.5
- **Reason:** Fast, conversational, maintains voice

### Email Drafting
- **Default:** Kimi-k2.5
- **Review mode:** Claude-opus (if tone needs checking)

### Code / Technical
- **Fast:** Grok-code-fast-1
- **Complex:** Claude-opus-4-5-thinking

### Analysis / Research
- **Quick:** Kimi-k2.5
- **Deep:** DeepSeek-v3.2 or Claude-opus

### Job Applications / Professional
- **Drafting:** Kimi-k2.5
- **Review:** Claude-opus (professional tone check)

---

## Cost Management

### Free Tier Options
- `openrouter/free` — Generic free model
- `openrouter/nvidia/nemotron-3-nano-30b-a3b:free` — 30B params, capable
- `openrouter/stepfun/step-3.5-flash:free` — Flash model, fast

### When to Use Free
- Testing new prompts
- Low-stakes queries
- Background tasks
- Cost-sensitive periods

### When to Use Paid
- Important communications
- Complex reasoning
- Code that matters
- Time-sensitive tasks

---

## Sub-Agent Model Assignment

When Brutus spawns sub-agents for specific tasks:

| Task Type | Sub-Agent Model | Timeout |
|-----------|----------------|---------|
| Research | DeepSeek-v3.2 | 120s |
| Coding | Grok-code-fast-1 | 60s |
| Writing | Kimi-k2.5 | 60s |
| Analysis | Claude-opus-4-5-thinking | 180s |
| Background task | Nemotron-3-nano (free) | 300s |

---

## Model Health & Fallbacks

### Primary Chain
1. Kimi-k2.5 (first try)
2. Grok-code-fast-1 (if Kimi slow/fails)
3. OpenRouter/free (last resort)

### Error Handling
- Model timeout → Retry with lighter model
- Rate limit → Queue or fallback
- Quality drop → Flag for review

---

## Tracking & Optimization

Brutus tracks:
- Model usage frequency
- Response quality by task type
- Cost per task category
- User satisfaction by model

Goal: Automatically suggest best model for new task types based on patterns.

---

## Configuration Access

Models configured in:
- File: `/home/boss/.openclaw/openclaw.json`
- Section: `agents.defaults.models`

To add new model:
```
openclaw config patch --raw '{"agents":{"defaults":{"models":{"provider/model-name":{}}}}}'
```

---

**Note:** This config evolves with your usage. Review monthly to optimize for your actual patterns.
