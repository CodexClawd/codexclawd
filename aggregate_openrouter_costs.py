#!/usr/bin/env python3
"""
Aggregate OpenRouter usage from multiple CSV files
"""

import csv
from datetime import datetime
from pathlib import Path
import sys

def parse_timestamp(ts_str):
    return datetime.strptime(ts_str.strip(), '%Y-%m-%d %H:%M:%S.%f')

def load_csv(csv_path):
    records = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                record = {
                    'generation_id': row['generation_id'],
                    'created_at': parse_timestamp(row['created_at']),
                    'cost_total': float(row['cost_total']) if row['cost_total'] else 0,
                    'tokens_prompt': int(row['tokens_prompt']) if row['tokens_prompt'] else 0,
                    'tokens_completion': int(row['tokens_completion']) if row['tokens_completion'] else 0,
                    'tokens_reasoning': int(row['tokens_reasoning']) if row['tokens_reasoning'] else 0,
                    'model_permaslug': row['model_permaslug'],
                    'provider_name': row['provider_name'],
                }
                records.append(record)
            except (ValueError, KeyError) as e:
                continue
    return records

def main():
    csv_dir = Path('/home/boss/.openclaw/media/inbound')
    csv_files = sorted(csv_dir.glob('file_*.csv'))
    
    all_records = []
    for csv_file in csv_files:
        records = load_csv(csv_file)
        all_records.extend(records)
    
    # Filter to last 7 days
    cutoff = datetime(2026, 2, 11)  # One week ago from Feb 18
    recent = [r for r in all_records if r['created_at'] >= cutoff]
    
    if not recent:
        print("No recent records found")
        return
    
    # Calculate totals
    total_cost = sum(r['cost_total'] for r in recent)
    total_requests = len(recent)
    total_prompt = sum(r['tokens_prompt'] for r in recent)
    total_completion = sum(r['tokens_completion'] for r in recent)
    total_reasoning = sum(r['tokens_reasoning'] for r in recent)
    total_tokens = total_prompt + total_completion + total_reasoning
    
    # Date range
    dates = [r['created_at'] for r in recent]
    date_range = f"{min(dates).date()} to {max(dates).date()}"
    
    # Per day breakdown
    daily = {}
    for r in recent:
        date = r['created_at'].date()
        if date not in daily:
            daily[date] = {'cost': 0, 'requests': 0, 'tokens': 0}
        daily[date]['cost'] += r['cost_total']
        daily[date]['requests'] += 1
        daily[date]['tokens'] += r['tokens_prompt'] + r['tokens_completion'] + r['tokens_reasoning']
    
    # Model breakdown
    models = {}
    for r in recent:
        model = r['model_permaslug']
        if model not in models:
            models[model] = {'cost': 0, 'requests': 0, 'tokens': 0}
        models[model]['cost'] += r['cost_total']
        models[model]['requests'] += 1
        models[model]['tokens'] += r['tokens_prompt'] + r['tokens_completion'] + r['tokens_reasoning']
    
    print("="*80)
    print("📊 OpenRouter Usage Summary (Last 7 Days)")
    print("="*80)
    print(f"📅 Date Range: {date_range}")
    print(f"💰 Total Spend: ${total_cost:.4f}")
    print(f"📈 Total Requests: {total_requests:,}")
    print(f"🔤 Total Tokens: {total_tokens:,}")
    if total_requests > 0:
        print(f"   Avg Cost/Request: ${total_cost/total_requests:.4f}")
    if total_tokens > 0:
        print(f"   Cost per 1K tokens: ${(total_cost / (total_tokens/1000)):.4f}")
    print()
    
    print("📅 Daily Breakdown")
    print("-"*80)
    print(f"{'Date':<12} {'Cost ($)':>10} {'Requests':>10} {'Tokens':>12}")
    for date in sorted(daily.keys()):
        d = daily[date]
        print(f"{str(date):<12} {d['cost']:>10.4f} {d['requests']:>10} {d['tokens']:>12,}")
    print()
    
    print("🤖 Model Usage")
    print("-"*80)
    print(f"{'Model':<40} {'Cost ($)':>10} {'Requests':>10} {'Tokens':>12}")
    for model in sorted(models.items(), key=lambda x: x[1]['cost'], reverse=True):
        name, data = model
        name_short = name[:39] if len(name) > 39 else name
        print(f"{name_short:<40} {data['cost']:>10.4f} {data['requests']:>10} {data['tokens']:>12,}")

if __name__ == '__main__':
    main()
