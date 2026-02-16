---
name: openrouter-analyzer
description: Analyze OpenRouter API usage CSV exports to calculate costs, token usage, and efficiency metrics by hour, day, model, and provider. Use when the user attaches a CSV file from OpenRouter, mentions analyzing token usage, cost analysis, or OpenRouter usage data. Automatically detects OpenRouter CSV format and generates hourly breakdowns, model usage stats, and provider cost breakdowns.
---

# OpenRouter Usage Analyzer

Analyzes OpenRouter API usage exports to provide cost and token insights.

## When to Use

- User attaches a CSV file from OpenRouter dashboard
- User asks to analyze token usage or costs
- User mentions OpenRouter usage data
- User wants hourly/daily cost breakdowns

## How to Use

When triggered by CSV attachment or usage analysis request:

1. Save the attached CSV to a temp location if needed
2. Run the analyzer script: `python3 scripts/analyze.py <csv_path> --model --provider`
3. Present the results in a clean, formatted way highlighting:
   - Total spend and cost per request
   - Peak usage hours
   - Model breakdown (Kimi, Mimo, etc.)
   - Provider costs (Moonshot, Chutes, Novita, etc.)
   - Cost efficiency metrics

## Output Format

Present results in sections:
- 💰 Cost Efficiency (total spend, per-request cost, avg latency)
- 📊 Hourly Breakdown (cost per hour, requests, tokens)
- 📅 Daily Summary (if multi-day)
- 🤖 Model Breakdown (which models cost what)
- 🏢 Provider Breakdown (which providers used)

## Script Usage

```bash
# Basic analysis
python3 scripts/analyze.py <csv_file>

# With all breakdowns
python3 scripts/analyze.py <csv_file> --model --provider

# Export to CSV
python3 scripts/analyze.py <csv_file> --export output.csv
```

The script has no dependencies - uses only Python standard library.
