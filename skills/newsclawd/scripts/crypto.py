#!/usr/bin/env python3
"""NewsClawd - Crypto price monitoring with Binance API"""

import requests
import json
import sys
from datetime import datetime

def get_price(symbol):
    """Get current price from Binance"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol.upper()}"
        r = requests.get(url, timeout=10)
        data = r.json()
        return {
            'price': float(data['lastPrice']),
            'change_24h': float(data['priceChangePercent']),
            'high': float(data['highPrice']),
            'low': float(data['lowPrice']),
            'volume': float(data['volume'])
        }
    except Exception as e:
        return None

def check_alerts(symbol, above=None, below=None):
    """Check if price triggers any alerts"""
    data = get_price(symbol)
    if not data:
        return None
    
    alerts = []
    price = data['price']
    
    if above and price >= above:
        alerts.append(f"🚀 {symbol} ABOVE ${above:,.2f} (now ${price:,.2f})")
    
    if below and price <= below:
        alerts.append(f"📉 {symbol} BELOW ${below:,.2f} (now ${price:,.2f})")
    
    return {
        'triggered': len(alerts) > 0,
        'alerts': alerts,
        'data': data
    }

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', required=True)
    parser.add_argument('--above', type=float)
    parser.add_argument('--below', type=float)
    parser.add_argument('--format', choices=['json', 'text'], default='text')
    args = parser.parse_args()
    
    data = get_price(args.symbol)
    if not data:
        print(f"❌ Failed to fetch price for {args.symbol}", file=sys.stderr)
        sys.exit(1)
    
    if args.format == 'json':
        print(json.dumps(data))
        sys.exit(0)
    
    # Check alerts
    result = check_alerts(args.symbol, args.above, args.below)
    
    if result['triggered']:
        for alert in result['alerts']:
            print(f"🚨 NewsClawd Alert: {alert}")
    
    # Always show current price
    print(f"\n📊 {args.symbol}")
    print(f"   Price: ${data['price']:,.2f}")
    print(f"   24h Change: {data['change_24h']:+.2f}%")
    print(f"   High/Low: ${data['high']:,.2f} / ${data['low']:,.2f}")
    print(f"   Volume: {data['volume']:,.4f}")
    print(f"   Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

if __name__ == '__main__':
    main()
