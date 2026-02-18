#!/usr/bin/env python3
import csv
from datetime import datetime, timedelta
from collections import defaultdict
import sys

# Use the most recent CSV file
csv_path = '/home/boss/.openclaw/media/inbound/file_23---f04adbfe-6ae6-444d-b0c9-33418e0a143c.csv'

# Target dates: today (Feb 18 UTC) and maybe yesterday for comparison
today_utc = datetime.utcnow().date()
print(f"Current UTC date: {today_utc}")
print(f"Analyzing CSV: {csv_path}\n")

records = []
try:
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            created_at_str = row['created_at']
            try:
                created_at = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                continue
            records.append({
                'cost_total': float(row['cost_total']) if row['cost_total'] else 0,
                'tokens_prompt': int(row['tokens_prompt']) if row['tokens_prompt'] else 0,
                'tokens_completion': int(row['tokens_completion']) if row['tokens_completion'] else 0,
                'tokens_reasoning': int(row['tokens_reasoning']) if row['tokens_reasoning'] else 0,
                'tokens_cached': int(row['tokens_cached']) if row['tokens_cached'] else 0,
                'generation_time_ms': float(row['generation_time_ms']) if row.get('generation_time_ms') else 0,
                'model_permaslug': row['model_permaslug'],
                'provider_name': row['provider_name'],
                'created_at': created_at
            })
except Exception as e:
    print(f"Error reading CSV: {e}")
    sys.exit(1)

if not records:
    print("No records found in CSV.")
    sys.exit(0)

# Group by date
daily = defaultdict(list)
for r in records:
    daily[r['created_at'].date()].append(r)

# Print summary for each day, focusing on most recent
sorted_dates = sorted(daily.keys(), reverse=True)
print(f"Found data for {len(sorted_dates)} day(s): {', '.join(d.strftime('%Y-%m-%d') for d in sorted_dates)}\n")

for date in sorted_dates[:3]:  # Last 3 days max
    day_records = daily[date]
    total_cost = sum(r['cost_total'] for r in day_records)
    total_requests = len(day_records)
    total_prompt = sum(r['tokens_prompt'] for r in day_records)
    total_completion = sum(r['tokens_completion'] for r in day_records)
    total_reasoning = sum(r['tokens_reasoning'] for r in day_records)
    total_cached = sum(r['tokens_cached'] for r in day_records)
    total_tokens = total_prompt + total_completion

    print(f"=== {date.strftime('%Y-%m-%d')} ({'TODAY' if date == today_utc else 'Yesterday' if date == today_utc - timedelta(days=1) else 'Earlier'}) ===")
    print(f"Requests: {total_requests}")
    print(f"Total Spend: ${total_cost:.4f}")
    if total_requests > 0:
        print(f"Cost per Request: ${total_cost/total_requests:.4f}")
    if total_tokens > 0:
        print(f"Cost per 1K tokens: ${(total_cost / (total_tokens / 1000)):.4f}")
    print(f"Tokens: prompt={total_prompt:,}, completion={total_completion:,}, reasoning={total_reasoning:,}")
    print()

    # Hourly breakdown for this day
    hourly = defaultdict(lambda: {'cost': 0, 'requests': 0, 'tokens': 0})
    for r in day_records:
        hour_key = r['created_at'].replace(minute=0, second=0, microsecond=0)
        hourly[hour_key]['cost'] += r['cost_total']
        hourly[hour_key]['requests'] += 1
        hourly[hour_key]['tokens'] += r['tokens_prompt'] + r['tokens_completion']

    print("Hourly breakdown:")
    for hour, data in sorted(hourly.items())[-24:]:  # Last 24 hours
        print(f"  {hour.strftime('%H:%M')}: ${data['cost']:.4f}, {data['requests']} req, {data['tokens']:,} tokens")
    print()

    # Model breakdown
    model_cost = defaultdict(float)
    for r in day_records:
        model_cost[r['model_permaslug']] += r['cost_total']
    print("Model cost breakdown:")
    for model, cost in sorted(model_cost.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {model}: ${cost:.4f}")
    print()

    # Provider breakdown
    provider_cost = defaultdict(float)
    for r in day_records:
        provider_cost[r['provider_name']] += r['cost_total']
    print("Provider cost breakdown:")
    for provider, cost in sorted(provider_cost.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {provider}: ${cost:.4f}")
    print("\n")
