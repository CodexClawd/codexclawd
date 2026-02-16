#!/usr/bin/env python3
import csv
from datetime import datetime
from collections import defaultdict

csv_path = '/home/boss/.openclaw/media/inbound/file_15---1a5c7b78-4fc1-4e17-8fa9-174ed41c51d9.csv'
today = datetime(2026, 2, 13).date()

records = []
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        created_at = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S.%f')
        if created_at.date() == today:
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

if not records:
    print("No records for today")
    exit(0)

print(f"Records today: {len(records)}")
total_cost = sum(r['cost_total'] for r in records)
total_prompt = sum(r['tokens_prompt'] for r in records)
total_completion = sum(r['tokens_completion'] for r in records)
total_reasoning = sum(r['tokens_reasoning'] for r in records)
total_cached = sum(r['tokens_cached'] for r in records)
total_requests = len(records)
gen_times = [r['generation_time_ms'] for r in records if r['generation_time_ms'] > 0]
avg_latency = sum(gen_times) / len(gen_times) if gen_times else 0
total_tokens = total_prompt + total_completion

print(f"Total spend: ${total_cost:.4f}")
print(f"Total requests: {total_requests}")
print(f"Cost per request: ${total_cost/total_requests:.4f}")
print(f"Total prompt tokens: {total_prompt:,}")
print(f"Total completion tokens: {total_completion:,}")
print(f"Total reasoning tokens: {total_reasoning:,}")
print(f"Total cached tokens: {total_cached:,}")
print(f"Total tokens (prompt+completion): {total_tokens:,}")
if total_tokens > 0:
    print(f"Cost per 1K tokens: ${(total_cost / (total_tokens / 1000)):.4f}")
print(f"Average generation time: {avg_latency:.0f} ms")

# Hourly breakdown for today
hourly = defaultdict(lambda: {'cost': 0, 'requests': 0, 'tokens': 0})
for r in records:
    hour_key = r['created_at'].replace(minute=0, second=0, microsecond=0)
    hourly[hour_key]['cost'] += r['cost_total']
    hourly[hour_key]['requests'] += 1
    hourly[hour_key]['tokens'] += r['tokens_prompt'] + r['tokens_completion']

print("\nHourly breakdown for today:")
for hour, data in sorted(hourly.items()):
    print(f"  {hour.strftime('%H:%M')}: ${data['cost']:.4f}, {data['requests']} requests, {data['tokens']:,} tokens")

# Model breakdown
model_cost = defaultdict(float)
for r in records:
    model_cost[r['model_permaslug']] += r['cost_total']
print("\nModel cost breakdown:")
for model, cost in sorted(model_cost.items(), key=lambda x: x[1], reverse=True):
    print(f"  {model}: ${cost:.4f}")

# Provider breakdown
provider_cost = defaultdict(float)
for r in records:
    provider_cost[r['provider_name']] += r['cost_total']
print("\nProvider cost breakdown:")
for provider, cost in sorted(provider_cost.items(), key=lambda x: x[1], reverse=True):
    print(f"  {provider}: ${cost:.4f}")