# Binance API Integration

Full Binance API integration for Brutus with secure credential storage.

## Quick Start

```bash
cd /home/boss/.openclaw/workspace/polymarket

# 1. Setup credentials
node setup-binance.js

# 2. Test with price check
node crypto-tools.js price BTCUSDT

# 3. Check your balance
node crypto-tools.js balance
```

## Files

| File | Purpose |
|------|---------|
| `setup-binance.js` | Interactive setup for API credentials |
| `binance-api.js` | Core API client class |
| `crypto-tools.js` | CLI tool for common operations |
| `binance-config.json` | Your credentials (gitignored) |

## Available Commands

### Price & Market Data
```bash
node crypto-tools.js price                    # BTC price
node crypto-tools.js price ETHUSDT           # Any pair
node crypto-tools.js stats BTCUSDT           # 24h stats
node crypto-tools.js book BTCUSDT            # Order book
```

### Account Operations
```bash
node crypto-tools.js balance                 # Your balances
node crypto-tools.js orders BTCUSDT          # Open orders
node crypto-tools.js history BTCUSDT         # Trade history
```

### Trading (requires trading permissions)
```bash
node crypto-tools.js buy BTCUSDT 100         # Buy $100 of BTC
node crypto-tools.js sell BTCUSDT 0.001      # Sell 0.001 BTC
```

## API Security

### Storage Method
API keys stored in `binance-config.json`:
```json
{
  "apiKey": "your_key_here",
  "secretKey": "your_secret_here",
  "permissions": "read-only",
  "createdAt": "2026-02-06T12:00:00Z"
}
```

### Security Features
- ✅ File is gitignored (never committed)
- ✅ HMAC SHA256 signatures for all private requests
- ✅ Timestamps prevent replay attacks
- ✅ IP whitelist supported

### Recommended Binance Settings
1. **Create API Key** at: https://www.binance.com/en/my/settings/api-management
2. **Permissions:**
   - ✅ Enable Reading
   - ✅ Enable Spot & Margin Trading (if trading)
   - ❌ **DISABLE Withdrawals** (safety)
3. **IP Whitelist:** Add your server IP
4. **Save keys** and run `node setup-binance.js`

## Programmatic Usage

```javascript
const BinanceAPI = require('./binance-api.js');

const api = new BinanceAPI();

// Get price
const price = await api.getPrice('BTCUSDT');

// Get candles
const candles = await api.getKlines('BTCUSDT', '15m', 100);

// Get balances
const balances = await api.getBalances();

// Place order (if trading enabled)
const order = await api.placeMarketOrder('BTCUSDT', 'BUY', 100);
```

## Advanced: Using in Sessions

Now you can ask Brutus to:

> "Check my crypto balance"
> "What's the Bitcoin price?"
> "Show me my open orders on Binance"
> "Buy $50 of Ethereum"

Brutus will use these tools automatically.

## Troubleshooting

**Error: "config not found"**
→ Run `node setup-binance.js` first

**Error: "Invalid API key"**
→ Check keys are correct, not expired

**Error: "IP not whitelisted"**
→ Add your server IP in Binance API settings

**Error: "Insufficient permissions"**
→ Key is read-only, can't trade

---
*Secure, fast, integrated.*
