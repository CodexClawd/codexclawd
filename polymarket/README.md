# Polymarket Tracker Setup - Session Log

**Date:** 2026-02-06
**Session:** Initial setup and data exploration

## What We Built

### 1. API Setup
- Installed `@polymarket/clob-client`
- Generated API credentials for wallet `0x1F13...84e7`
- Files: `config.json`, `wallet.json`

### 2. Manual Price Tracker (Primary Tool)
**File:** `manual-tracker.js`
**Usage:**
```bash
node manual-tracker.js feb9 0.12   # Update Feb 9 market price
node manual-tracker.js feb28 0.30  # Update Feb 28 market price
```
**Features:**
- Tracks price changes
- Alerts on ±5% moves
- Calculates portfolio value
- Saves history to `price-tracker.json`

### 3. API Data Dumper
**File:** `dump-api.js`
Dumps all available CLOB API data to `api-dump.json`

### 4. Crypto Market Extractor
**File:** `extract-crypto.js`
Extracts crypto markets from API dump to `crypto-markets.json`

### 5. Binance 15-Min Scraper
**File:** `binance-scraper.js`
Fetches BTC/USDT 15-minute candles from Binance
```bash
node binance-scraper.js
```
Output: `btc-15min-data.json`

### 6. Strategy Backtester
**File:** `backtest-strategies.js`
Tests 4 strategies on 15-min data:
- 3-Candle Momentum: 49.5% win rate
- Breakout Trading: 42.8% win rate
- Range Reversal: 58.5% win rate ⭐
- Volatility Squeeze: 100% (2 signals only)

## Key Findings

### Polymarket API Limitations
- **CLOB API** only returns historical markets (2021-2023)
- **No 2026 markets indexed yet** — too new
- **Gamma API** same limitation
- **Result:** Must use manual tracking for current positions

### Manual Tracking Required
Your US-Iran positions (Feb 9 & 28) must be tracked manually:
1. You check Polymarket
2. Report prices to Brutus
3. Brutus logs and alerts on ±5% changes

### Data Available
- 1000 historical markets (sports, politics, crypto)
- 500 15-min BTC candles (real-time via Binance)
- 123 crypto-related markets from Polymarket history

## Files Created
```
polymarket/
├── package.json
├── package-lock.json
├── config.json              # API credentials
├── wallet.json              # Wallet config
├── api-dump.json            # Full API dump (~2MB)
├── api-summary.json         # API summary
├── markets-found.json       # Gamma API search results
├── crypto-markets.json      # Extracted crypto markets
├── btc-15min-data.json      # Binance 15-min candles
├── price-tracker.json       # Manual tracking data
├── setup-api.js             # API credential generator
├── dump-api.js              # API data dumper
├── find-markets.js          # Market finder
├── gamma-search.js          # Gamma API searcher
├── extract-crypto.js        # Crypto extractor
├── binance-scraper.js       # Binance data fetcher
├── backtest-strategies.js   # Strategy tester
├── manual-tracker.js        # Main tracking tool
└── README.md                # This file
```

## Next Steps (For Future Sessions)

### Immediate
- [ ] Check Polymarket prices for Feb 9 & 28 markets
- [ ] Run `node manual-tracker.js` to log baseline
- [ ] Set up cron reminders for price checks

### Data Expansion
- [ ] Fetch more Binance history (10k+ candles)
- [ ] Test Range Reversal strategy with proper risk mgmt
- [ ] Explore Hyperliquid/GMX for on-chain perps

### Automation
- [ ] Build alert system for ±5% moves
- [ ] Create portfolio dashboard
- [ ] Add news monitoring for Iran/US developments

## Commands Quick Reference

```bash
cd /home/boss/.openclaw/workspace/polymarket

# Update prices (manual)
node manual-tracker.js feb9 0.12
node manual-tracker.js feb28 0.30

# Fetch fresh Binance data
node binance-scraper.js

# Run backtests
node backtest-strategies.js

# View tracking data
cat price-tracker.json
cat btc-15min-data.json | jq '.[0:5]'
```

## Notes
- The Range Reversal strategy (58.5% win rate) shows promise
- Need more data for robust backtesting
- On-chain binary options (Thales/Lyra) subgraphs currently down
- Binance API provides free 15-min data for strategies

---
*Session saved. Ready for next work.*
