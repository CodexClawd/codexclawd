#!/usr/bin/env python3
"""Daily crypto price fetcher + portfolio tracker"""

import sys
import json
import requests
from datetime import datetime

sys.path.insert(0, '/home/boss/.openclaw/workspace/venv/lib/python3.12/site-packages')

BINANCE_URL = "https://api.binance.com/api/v3/ticker/24hr"
PORTFOLIO_FILE = '/home/boss/.openclaw/workspace/portfolio.json'
PORTFOLIO_HISTORY_FILE = '/home/boss/.openclaw/workspace/portfolio_history.json'

def load_portfolio_history():
    """Load portfolio history for daily change calc"""
    try:
        with open(PORTFOLIO_HISTORY_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'last_value': 0, 'last_date': '', 'history': []}

def save_portfolio_history(value):
    """Save today's portfolio value"""
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    history = load_portfolio_history()
    history['last_value'] = value
    history['last_date'] = today
    history['history'].append({'date': today, 'value': value})
    
    # Keep last 30 days
    if len(history['history']) > 30:
        history['history'] = history['history'][-30:]
    
    with open(PORTFOLIO_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def calculate_portfolio_change(current_value):
    """Calculate daily change vs yesterday"""
    history = load_portfolio_history()
    last_value = history.get('last_value', 0)
    
    if last_value > 0 and last_value != current_value:
        change = current_value - last_value
        change_pct = (change / last_value) * 100
        return change, change_pct
    
    return 0, 0

def load_portfolio():
    """Portfolio data removed per user request"""
    return {'holdings': {}, 'stablecoins': {}, 'total_value': 0}

def fetch_prices():
    """Fetch prices from Binance"""
    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT']
    prices = {}
    
    for symbol in symbols:
        try:
            response = requests.get(f"{BINANCE_URL}?symbol={symbol}", timeout=10)
            data = response.json()
            prices[symbol.replace('USDT', '')] = {
                'price': float(data['lastPrice']),
                'change_24h': float(data['priceChangePercent']),
                'high': float(data['highPrice']),
                'low': float(data['lowPrice']),
            }
        except Exception as e:
            prices[symbol.replace('USDT', '')] = {'error': str(e)}
    
    return prices

def load_portfolio():
    """Load portfolio data"""
    try:
        with open(PORTFOLIO_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'holdings': {}, 'stablecoins': {}}

def calculate_portfolio(prices, portfolio):
    """Calculate portfolio summary - uses total_value from file"""
    crypto_value = 0
    holdings_value = {}
    
    # Get crypto holdings from nested structure
    crypto_data = portfolio.get('holdings', {}).get('Crypto', {})
    for coin, data in crypto_data.items():
        if coin in prices and 'price' in prices[coin]:
            amount = data.get('amount', 0)
            current_price = prices[coin]['price']
            value_eur = data.get('value_eur', 0)
            
            holdings_value[coin] = {
                'amount': amount,
                'value': value_eur,
                'current_price': current_price
            }
            crypto_value += value_eur
    
    # Get total from file (includes all asset classes)
    total_value = portfolio.get('total_value', 0)
    
    # Get breakdown by category
    categories = {}
    for category, items in portfolio.get('holdings', {}).items():
        cat_value = sum(v.get('value_eur', 0) for v in items.values() if isinstance(v, dict))
        categories[category] = cat_value
    
    # Add stablecoins
    stablecoins = portfolio.get('holdings', {}).get('Stablecoins', {})
    stable_value = sum(v.get('value_eur', 0) for v in stablecoins.values() if isinstance(v, dict))
    
    # Add cash
    cash = portfolio.get('holdings', {}).get('Cash', {})
    cash_value = sum(v.get('value_eur', 0) for v in cash.values() if isinstance(v, dict))
    
    return {
        'holdings': holdings_value,
        'crypto_value': crypto_value,
        'total_value': total_value,
        'categories': categories,
        'stable_value': stable_value,
        'cash_value': cash_value
    }

def format_message(prices, portfolio_data):
    """Format the full message"""
    now = datetime.now().strftime('%H:%M')
    
    # Calculate portfolio daily change
    total_value = portfolio_data['total_value']
    change, change_pct = calculate_portfolio_change(total_value)
    save_portfolio_history(total_value)
    
    # Portfolio change emoji
    if change > 0:
        port_emoji = "🟢"
    elif change < 0:
        port_emoji = "🔴"
    else:
        port_emoji = "⚪"
    
    lines = [
        f"📊 **Daily Crypto Update - {now}**\n",
        "*Market Prices:*",
    ]
    
    # Market prices section
    for coin, data in prices.items():
        if 'error' in data:
            lines.append(f"❌ {coin}: error")
        else:
            emoji = "🟢" if data['change_24h'] >= 0 else "🔴"
            lines.append(
                f"{emoji} **{coin}**: ${data['price']:,.2f} "
                f"({data['change_24h']:+.2f}%)"
            )
    
    # Portfolio section - personal data removed
    lines.append("\n*Portfolio tracking disabled*")
    
    lines.append("\n🦞 BRUTUS")
    return '\n'.join(lines)

def send_to_telegram(message):
    """Send message via Pinger Bot (@brutusclawdbot)"""
    import subprocess
    import json
    
    # Load pinger bot config
    try:
        with open('/home/boss/.openclaw/workspace/bot_config.json', 'r') as f:
            config = json.load(f)
        pinger_token = config['pinger_bot']['token']
        chat_id = config['pinger_bot']['chat_id']
    except:
        # Fallback to main bot
        pinger_token = "8254596590:AAGTd9-fEQeGjQeLOSRUdaFyiPgtoqMSG1c"
        chat_id = "7359674814"
    
    # Use curl to send via bot API directly
    import urllib.request
    import urllib.parse
    
    url = f"https://api.telegram.org/bot{pinger_token}/sendMessage"
    data = urllib.parse.urlencode({
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }).encode()
    
    try:
        req = urllib.request.Request(url, data=data, method='POST')
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status == 200
    except Exception as e:
        print(f"Failed to send: {e}")
        # Fallback: print to stdout
        print(message)
        return False

if __name__ == '__main__':
    print("Fetching crypto prices...")
    prices = fetch_prices()
    
    print("Loading portfolio...")
    portfolio = load_portfolio()
    portfolio_data = calculate_portfolio(prices, portfolio)
    
    message = format_message(prices, portfolio_data)
    print(message)
    
    print("\nSending to Telegram...")
    if send_to_telegram(message):
        print("✅ Message sent!")
    else:
        print("❌ Failed to send")
