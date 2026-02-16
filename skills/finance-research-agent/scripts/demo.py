#!/usr/bin/env python3
"""
Demo script showing typical finance-research-agent usage.

Usage:
    python demo.py snapshot AAPL
    python demo.py news NVDA
    python demo.py report BTC --days 90
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from finance_api import (
    fetch_historical, fetch_current, fetch_crypto_historical,
    calculate_rsi, calculate_macd, calculate_sma,
    scan_news, aggregate_sentiment,
    generate_snapshot_report, check_alerts
)
import pandas as pd
from datetime import datetime


def demo_snapshot(symbol: str):
    """Generate a quick snapshot report."""
    print(f"=== Generating snapshot for {symbol} ===")

    # Fetch current data
    current = fetch_current(symbol)
    print(f"Current price: ${current.get('price', 'N/A'):,.2f}")
    print(f"Change: {current.get('change_percent', 'N/A')}%")

    # RSI
    df = fetch_historical(symbol, period="1mo", interval="1d")
    if not df.empty:
        rsi = calculate_rsi(df['close'], period=14).iloc[-1]
        print(f"RSI(14): {rsi:.1f}")

    # News
    articles = scan_news(symbol, hours_back=24, max_results=5)
    sentiment = aggregate_sentiment(articles)
    print(f"News sentiment: {sentiment['overall']} ({sentiment['total']} articles)")

    # Generate report
    if symbol in ['bitcoin', 'ethereum'] or symbol.endswith('-USD'):
        # Crypto
        report = generate_snapshot_report(symbol.replace('-USD', ''), output_dir="memory/reports/")
    else:
        report = generate_snapshot_report(symbol, output_dir="memory/reports/")

    print(f"Report saved to: {report}")


def demo_news(query: str):
    """Scan and analyze news."""
    print(f"=== News scan for '{query}' ===")

    articles = scan_news(query, hours_back=24, max_results=10)
    sentiment = aggregate_sentiment(articles)

    print(f"Found {sentiment['total']} articles")
    print(f"Sentiment: {sentiment['overall']}")
    print(f"  Positive: {sentiment['positive']}")
    print(f"  Negative: {sentiment['negative']}")
    print(f"  Neutral: {sentiment['neutral']}")

    print("\nTop headlines:")
    for i, article in enumerate(sentiment['articles'][:5], 1):
        print(f"{i}. {article['title']} ({article['source']})")
        print(f"   {article['url']}\n")


def demo_technical(symbol: str, days: int = 90):
    """Show technical analysis."""
    print(f"=== Technical analysis for {symbol} ===")

    df = fetch_historical(symbol, period=f"{days}d", interval="1d")
    if df.empty:
        print("No data available")
        return

    close = df['close']

    # Indicators
    rsi = calculate_rsi(close, period=14).iloc[-1]
    macd = calculate_macd(close)
    sma_50 = calculate_sma(close, 50).iloc[-1] if len(close) >= 50 else None
    sma_200 = calculate_sma(close, 200).iloc[-1] if len(close) >= 200 else None

    print(f"Price: ${close.iloc[-1]:,.2f}")
    print(f"RSI(14): {rsi:.1f}")
    print(f"SMA 50: ${sma_50:,.2f}" if sma_50 else "SMA 50: insufficient data")
    print(f"SMA 200: ${sma_200:,.2f}" if sma_200 else "SMA 200: insufficient data")
    print(f"MACD: {macd['macd'].iloc[-1]:.2f} (signal: {macd['signal'].iloc[-1]:.2f})")

    # Trend
    if sma_50 and sma_200:
        trend = "Bullish" if sma_50 > sma_200 else "Bearish"
        print(f"Trend (50 vs 200 SMA): {trend}")


def demo_watchlist():
    """Check configured watchlist alerts."""
    print("=== Watchlist Alerts ===")

    watchlist = [
        {
            'symbol': 'BTC-USD',
            'alerts': [
                {'type': 'price_above', 'value': 100000},
                {'type': 'rsi_below', 'value': 30},
                {'type': 'volume_spike', 'multiple': 2.0}
            ]
        },
        {
            'symbol': 'AAPL',
            'alerts': [
                {'type': 'price_below', 'value': 200},
                {'type': 'rsi_above', 'value': 70}
            ]
        }
    ]

    triggered = check_alerts(watchlist)
    if triggered:
        print("⚠️ ALERTS TRIGGERED:")
        for alert in triggered:
            print(f"  • {alert['message']}")
    else:
        print("✅ No alerts triggered")


def demo_crypto(coin: str, days: int = 90):
    """Crypto-specific analysis."""
    print(f"=== {coin.upper()} Analysis ===")

    # Map symbol to CoinGecko ID
    coin_map = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'SOL': 'solana',
        'DOGE': 'dogecoin',
        'ADA': 'cardano',
        'AVAX': 'avalanche-2'
    }
    coin_id = coin_map.get(coin.upper(), coin.lower())

    df = fetch_crypto_historical(coin_id, days=days)
    if df.empty:
        print(f"No data for {coin}")
        return

    current_price = df['close'].iloc[-1]
    rsi = calculate_rsi(df['close'], period=14).iloc[-1]
    sma_20 = calculate_sma(df['close'], 20).iloc[-1] if len(df) >= 20 else None

    print(f"Current: ${current_price:,.2f}")
    print(f"RSI(14): {rsi:.1f}")
    print(f"SMA 20: ${sma_20:,.2f}" if sma_20 else "")

    # Dominance check (needs market cap data from CoinGecko)
    print("\n(Use 'demoreport' for full analysis with charts)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Demo usage:")
        print("  python demo.py snapshot <SYMBOL>")
        print("  python demo.py news <QUERY>")
        print("  python demo.py technical <SYMBOL> [days]")
        print("  python demo.py crypto <COIN> [days]")
        print("  python demo.py watchlist")
        print("  python demo.py demoreport <SYMBOL>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "snapshot":
        symbol = sys.argv[2] if len(sys.argv) > 2 else "AAPL"
        demo_snapshot(symbol)

    elif command == "news":
        query = sys.argv[2] if len(sys.argv) > 2 else "finance"
        demo_news(query)

    elif command == "technical":
        symbol = sys.argv[2] if len(sys.argv) > 2 else "AAPL"
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 90
        demo_technical(symbol, days)

    elif command == "crypto":
        coin = sys.argv[2] if len(sys.argv) > 2 else "BTC"
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 90
        demo_crypto(coin, days)

    elif command == "watchlist":
        demo_watchlist()

    elif command == "demoreport":
        symbol = sys.argv[2] if len(sys.argv) > 2 else "AAPL"
        report = generate_snapshot_report(symbol)
        print(f"Report: {report}")

    else:
        print(f"Unknown command: {command}")
