#!/usr/bin/env python3
"""Test Binance API connection"""

import os
import sys

# Add venv packages to path
sys.path.insert(0, '/home/boss/.openclaw/workspace/venv/lib/python3.12/site-packages')

from binance.client import Client
from binance.exceptions import BinanceAPIException

def test_binance():
    # Get keys from environment
    api_key = os.environ.get('BINANCE_API_KEY')
    api_secret = os.environ.get('BINANCE_SECRET_KEY')
    
    if not api_key or not api_secret:
        print("❌ ERROR: BINANCE_API_KEY and BINANCE_SECRET_KEY must be set")
        print("")
        print("Set them like this:")
        print("  export BINANCE_API_KEY='your_key_here'")
        print("  export BINANCE_SECRET_KEY='your_secret_here'")
        sys.exit(1)
    
    print("🔑 API Key found (starts with):", api_key[:8], "...")
    print("")
    
    try:
        # Initialize client (testnet=False for production)
        client = Client(api_key, api_secret, testnet=False)
        
        print("📡 Testing connection...")
        print("")
        
        # Test 1: Server time
        server_time = client.get_server_time()
        print(f"✅ Server time: {server_time['serverTime']}")
        
        # Test 2: Get BTC price
        ticker = client.get_symbol_ticker(symbol="BTCUSDT")
        print(f"✅ BTC/USDT Price: ${ticker['price']}")
        
        # Test 3: Get account info (requires valid keys)
        account = client.get_account()
        print(f"✅ Account status: {account['accountType']}")
        print(f"   Can trade: {account['canTrade']}")
        print(f"   Can withdraw: {account['canWithdraw']}")
        
        # Test 4: Show balances > 0
        balances = [b for b in account['balances'] if float(b['free']) > 0 or float(b['locked']) > 0]
        if balances:
            print(f"")
            print(f"💰 Balances with funds:")
            for b in balances[:5]:  # Show first 5
                total = float(b['free']) + float(b['locked'])
                print(f"   {b['asset']}: {total}")
        
        print("")
        print("🎉 All tests passed! Binance API is working.")
        
    except BinanceAPIException as e:
        print(f"❌ Binance API Error: {e}")
        if e.code == -2015:
            print("   → Invalid API key or IP not whitelisted")
        elif e.code == -2014:
            print("   → API key format invalid")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_binance()
