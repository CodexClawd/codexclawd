#!/usr/bin/env python3
"""
OpenRouter Usage Analyzer
Analyzes token usage and costs from OpenRouter CSV exports
No external dependencies - uses only standard library
"""

import csv
from datetime import datetime
from collections import defaultdict
import sys
from pathlib import Path
import argparse


def parse_timestamp(ts_str):
    """Parse OpenRouter timestamp format"""
    # Format: 2026-02-06 18:54:30.040
    return datetime.strptime(ts_str.strip(), '%Y-%m-%d %H:%M:%S.%f')


def load_data(csv_path):
    """Load and parse the CSV file"""
    records = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                record = {
                    'generation_id': row['generation_id'],
                    'created_at': parse_timestamp(row['created_at']),
                    'cost_total': float(row['cost_total']) if row['cost_total'] else 0,
                    'cost_web_search': float(row['cost_web_search']) if row['cost_web_search'] else 0,
                    'cost_cache': float(row['cost_cache']) if row['cost_cache'] else 0,
                    'cost_file_processing': float(row['cost_file_processing']) if row['cost_file_processing'] else 0,
                    'byok_usage_inference': float(row['byok_usage_inference']) if row['byok_usage_inference'] else 0,
                    'tokens_prompt': int(row['tokens_prompt']) if row['tokens_prompt'] else 0,
                    'tokens_completion': int(row['tokens_completion']) if row['tokens_completion'] else 0,
                    'tokens_reasoning': int(row['tokens_reasoning']) if row['tokens_reasoning'] else 0,
                    'tokens_cached': int(row['tokens_cached']) if row['tokens_cached'] else 0,
                    'model_permaslug': row['model_permaslug'],
                    'provider_name': row['provider_name'],
                    'finish_reason_normalized': row.get('finish_reason_normalized', ''),
                    'generation_time_ms': float(row['generation_time_ms']) if row.get('generation_time_ms') else 0,
                    'time_to_first_token_ms': float(row['time_to_first_token_ms']) if row.get('time_to_first_token_ms') else 0,
                }
                records.append(record)
            except (ValueError, KeyError) as e:
                continue
    
    return records


def hourly_analysis(records):
    """Analyze usage by hour"""
    print("\n" + "="*80)
    print("📊 HOURLY BREAKDOWN")
    print("="*80)
    
    hourly = defaultdict(lambda: {
        'cost_total': 0,
        'tokens_prompt': 0,
        'tokens_completion': 0,
        'tokens_reasoning': 0,
        'tokens_cached': 0,
        'requests': 0,
        'gen_time_sum': 0,
        'gen_time_count': 0
    })
    
    for r in records:
        hour_key = r['created_at'].replace(minute=0, second=0, microsecond=0)
        hourly[hour_key]['cost_total'] += r['cost_total']
        hourly[hour_key]['tokens_prompt'] += r['tokens_prompt']
        hourly[hour_key]['tokens_completion'] += r['tokens_completion']
        hourly[hour_key]['tokens_reasoning'] += r['tokens_reasoning']
        hourly[hour_key]['tokens_cached'] += r['tokens_cached']
        hourly[hour_key]['requests'] += 1
        if r['generation_time_ms'] > 0:
            hourly[hour_key]['gen_time_sum'] += r['generation_time_ms']
            hourly[hour_key]['gen_time_count'] += 1
    
    # Sort by hour
    sorted_hours = sorted(hourly.items())
    
    # Header
    print(f"{'Hour':<20} {'Cost ($)':>10} {'Requests':>10} {'Total Tokens':>12} {'Avg ms':>10}")
    print("-" * 80)
    
    total_cost = 0
    for hour, data in sorted_hours:
        total_tokens = data['tokens_prompt'] + data['tokens_completion'] + data['tokens_reasoning']
        avg_gen_time = data['gen_time_sum'] / data['gen_time_count'] if data['gen_time_count'] > 0 else 0
        total_cost += data['cost_total']
        print(f"{hour.strftime('%Y-%m-%d %H:00'):<20} {data['cost_total']:>10.4f} {data['requests']:>10} {total_tokens:>12,} {avg_gen_time:>10.0f}")
    
    print("-" * 80)
    print(f"📈 Summary: ${total_cost:.4f} total | {len(records)} requests | ${total_cost/len(records):.4f} avg per request")
    
    return hourly


def daily_summary(records):
    """Summarize by day"""
    print("\n" + "="*80)
    print("📅 DAILY SUMMARY")
    print("="*80)
    
    daily = defaultdict(lambda: {
        'cost_total': 0,
        'tokens_prompt': 0,
        'tokens_completion': 0,
        'tokens_reasoning': 0,
        'requests': 0
    })
    
    for r in records:
        date_key = r['created_at'].date()
        daily[date_key]['cost_total'] += r['cost_total']
        daily[date_key]['tokens_prompt'] += r['tokens_prompt']
        daily[date_key]['tokens_completion'] += r['tokens_completion']
        daily[date_key]['tokens_reasoning'] += r['tokens_reasoning']
        daily[date_key]['requests'] += 1
    
    sorted_days = sorted(daily.items())
    
    print(f"{'Date':<15} {'Cost ($)':>10} {'Requests':>10} {'Total Tokens':>12}")
    print("-" * 80)
    
    for date, data in sorted_days:
        total_tokens = data['tokens_prompt'] + data['tokens_completion'] + data['tokens_reasoning']
        print(f"{str(date):<15} {data['cost_total']:>10.4f} {data['requests']:>10} {total_tokens:>12,}")


def model_analysis(records):
    """Analyze usage by model"""
    print("\n" + "="*80)
    print("🤖 MODEL BREAKDOWN")
    print("="*80)
    
    models = defaultdict(lambda: {
        'cost_total': 0,
        'tokens_prompt': 0,
        'tokens_completion': 0,
        'tokens_reasoning': 0,
        'requests': 0
    })
    
    for r in records:
        model = r['model_permaslug']
        models[model]['cost_total'] += r['cost_total']
        models[model]['tokens_prompt'] += r['tokens_prompt']
        models[model]['tokens_completion'] += r['tokens_completion']
        models[model]['tokens_reasoning'] += r['tokens_reasoning']
        models[model]['requests'] += 1
    
    # Sort by cost
    sorted_models = sorted(models.items(), key=lambda x: x[1]['cost_total'], reverse=True)
    
    print(f"{'Model':<45} {'Cost ($)':>10} {'Requests':>10} {'Total Tokens':>12}")
    print("-" * 80)
    
    for model, data in sorted_models:
        total_tokens = data['tokens_prompt'] + data['tokens_completion'] + data['tokens_reasoning']
        model_short = model[:44] if len(model) > 44 else model
        print(f"{model_short:<45} {data['cost_total']:>10.4f} {data['requests']:>10} {total_tokens:>12,}")


def provider_analysis(records):
    """Analyze usage by provider"""
    print("\n" + "="*80)
    print("🏢 PROVIDER BREAKDOWN")
    print("="*80)
    
    providers = defaultdict(lambda: {
        'cost_total': 0,
        'requests': 0,
        'tokens_prompt': 0,
        'tokens_completion': 0
    })
    
    for r in records:
        provider = r['provider_name']
        providers[provider]['cost_total'] += r['cost_total']
        providers[provider]['requests'] += 1
        providers[provider]['tokens_prompt'] += r['tokens_prompt']
        providers[provider]['tokens_completion'] += r['tokens_completion']
    
    sorted_providers = sorted(providers.items(), key=lambda x: x[1]['cost_total'], reverse=True)
    
    print(f"{'Provider':<25} {'Cost ($)':>10} {'Requests':>10} {'Tokens':>12}")
    print("-" * 80)
    
    for provider, data in sorted_providers:
        total_tokens = data['tokens_prompt'] + data['tokens_completion']
        print(f"{provider:<25} {data['cost_total']:>10.4f} {data['requests']:>10} {total_tokens:>12,}")


def cost_efficiency_metrics(records):
    """Calculate cost efficiency metrics"""
    print("\n" + "="*80)
    print("💰 COST EFFICIENCY METRICS")
    print("="*80)
    
    total_cost = sum(r['cost_total'] for r in records)
    total_prompt = sum(r['tokens_prompt'] for r in records)
    total_completion = sum(r['tokens_completion'] for r in records)
    total_reasoning = sum(r['tokens_reasoning'] for r in records)
    total_cached = sum(r['tokens_cached'] for r in records)
    total_requests = len(records)
    
    gen_times = [r['generation_time_ms'] for r in records if r['generation_time_ms'] > 0]
    avg_latency = sum(gen_times) / len(gen_times) if gen_times else 0
    
    total_tokens = total_prompt + total_completion
    
    print(f"  Total Spend:           ${total_cost:.4f}")
    print(f"  Total Prompt Tokens:    {total_prompt:,.0f}")
    print(f"  Total Completion:       {total_completion:,.0f}")
    print(f"  Total Reasoning:        {total_reasoning:,.0f}")
    print(f"  Total Cached:           {total_cached:,.0f}")
    print(f"  Total Requests:         {total_requests:,}")
    print()
    if total_tokens > 0:
        print(f"  Cost per 1K Tokens:     ${(total_cost / (total_tokens / 1000)):.4f}")
    print(f"  Cost per Request:       ${total_cost / total_requests:.4f}")
    if total_requests > 0:
        print(f"  Avg Tokens/Request:     {total_tokens / total_requests:.0f}")
    if avg_latency > 0:
        print(f"  Avg Generation Time:    {avg_latency:.0f} ms")


def export_hourly(records, output_path):
    """Export hourly summary to CSV"""
    hourly = defaultdict(lambda: {
        'cost_total': 0,
        'tokens_prompt': 0,
        'tokens_completion': 0,
        'tokens_reasoning': 0,
        'tokens_cached': 0,
        'requests': 0,
        'gen_time_sum': 0,
        'gen_time_count': 0
    })
    
    for r in records:
        hour_key = r['created_at'].replace(minute=0, second=0, microsecond=0)
        hourly[hour_key]['cost_total'] += r['cost_total']
        hourly[hour_key]['tokens_prompt'] += r['tokens_prompt']
        hourly[hour_key]['tokens_completion'] += r['tokens_completion']
        hourly[hour_key]['tokens_reasoning'] += r['tokens_reasoning']
        hourly[hour_key]['tokens_cached'] += r['tokens_cached']
        hourly[hour_key]['requests'] += 1
        if r['generation_time_ms'] > 0:
            hourly[hour_key]['gen_time_sum'] += r['generation_time_ms']
            hourly[hour_key]['gen_time_count'] += 1
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['hour', 'total_cost_usd', 'request_count', 'prompt_tokens', 
                        'completion_tokens', 'reasoning_tokens', 'cached_tokens', 
                        'total_tokens', 'avg_gen_time_ms'])
        
        for hour in sorted(hourly.keys()):
            data = hourly[hour]
            total_tokens = data['tokens_prompt'] + data['tokens_completion'] + data['tokens_reasoning']
            avg_gen_time = data['gen_time_sum'] / data['gen_time_count'] if data['gen_time_count'] > 0 else 0
            writer.writerow([
                hour.strftime('%Y-%m-%d %H:%M:%S'),
                round(data['cost_total'], 4),
                data['requests'],
                data['tokens_prompt'],
                data['tokens_completion'],
                data['tokens_reasoning'],
                data['tokens_cached'],
                total_tokens,
                round(avg_gen_time, 0)
            ])
    
    print(f"\n✅ Hourly summary exported to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Analyze OpenRouter usage CSV')
    parser.add_argument('csv_file', help='Path to the CSV file')
    parser.add_argument('--export', '-e', metavar='OUTPUT', 
                        help='Export hourly summary to CSV')
    parser.add_argument('--model', '-m', action='store_true',
                        help='Show model breakdown')
    parser.add_argument('--provider', '-p', action='store_true',
                        help='Show provider breakdown')
    
    args = parser.parse_args()
    
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"❌ Error: File not found: {csv_path}")
        sys.exit(1)
    
    print(f"📂 Loading: {csv_path}")
    records = load_data(csv_path)
    
    if not records:
        print("❌ No valid records found!")
        sys.exit(1)
    
    dates = [r['created_at'] for r in records]
    print(f"✅ Loaded {len(records)} records")
    print(f"📅 Date range: {min(dates).date()} to {max(dates).date()}")
    
    # Always show these
    cost_efficiency_metrics(records)
    hourly_analysis(records)
    daily_summary(records)
    
    # Optional breakdowns
    if args.model:
        model_analysis(records)
    
    if args.provider:
        provider_analysis(records)
    
    # Export if requested
    if args.export:
        export_hourly(records, args.export)


if __name__ == '__main__':
    main()
