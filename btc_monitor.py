#!/usr/bin/env python3
"""
BTC Price Monitor
Alerts when BTC drops 5% or more from starting price
Checks every 5 minutes
"""

import requests
import json
import time
from datetime import datetime

# Config
SYMBOL = "BTCUSDT"
CHECK_INTERVAL = 300  # 5 minutes
DROP_THRESHOLD = 0.05  # 5%
LOG_FILE = "btc_alerts.log"

def get_btc_price():
    """Fetch current BTC price from Binance"""
    try:
        response = requests.get(
            "https://api.binance.com/api/v3/ticker/price",
            params={"symbol": SYMBOL},
            timeout=10
        )
        response.raise_for_status()
        return float(response.json()["price"])
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None

def log_alert(start_price, current_price, drop_pct):
    """Log price drop alert"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = (
        f"[{timestamp}] ALERT: BTC dropped {drop_pct:.2f}%\n"
        f"  Start: ${start_price:,.2f}\n"
        f"  Current: ${current_price:,.2f}\n"
        f"  Diff: ${current_price - start_price:,.2f}\n"
    )
    print(message)
    with open(LOG_FILE, "a") as f:
        f.write(message + "\n")

def main():
    print("🦞 BTC Price Monitor Started")
    print(f"Checking every {CHECK_INTERVAL//60} minutes for {DROP_THRESHOLD*100}%+ drops\n")
    
    # Get starting price
    start_price = get_btc_price()
    if not start_price:
        print("Failed to get initial price. Exiting.")
        return
    
    print(f"Starting price: ${start_price:,.2f}")
    print(f"Alert if price drops below ${start_price * (1 - DROP_THRESHOLD):,.2f}\n")
    print("-" * 50)
    
    alerted = False
    
    while True:
        time.sleep(CHECK_INTERVAL)
        
        current_price = get_btc_price()
        if not current_price:
            continue
        
        # Calculate drop percentage
        drop_pct = (start_price - current_price) / start_price
        
        # Print status
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] BTC: ${current_price:,.2f} ({drop_pct*100:+.2f}%)")
        
        # Check if dropped 5% or more
        if drop_pct >= DROP_THRESHOLD and not alerted:
            log_alert(start_price, current_price, drop_pct)
            alerted = True  # Only alert once per drop
        
        # Reset alert if price recovers
        if drop_pct < DROP_THRESHOLD * 0.5:  # Recovered to < 2.5% drop
            alerted = False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Monitor stopped")
