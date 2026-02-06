# Binance API Integration Setup

## API Key Storage Options

### Option 1: Environment Variables (Most Secure)
Store keys in shell environment, not in files
```bash
export BINANCE_API_KEY="your_api_key"
export BINANCE_SECRET_KEY="your_secret"
```

### Option 2: Config File (Convenient)
Store in `binance-config.json` - already added to .gitignore

### Option 3: OpenClaw Auth Store
Use OpenClaw's built-in auth system if available

## What We'll Build

1. **Secure credential storage**
2. **Account info checker** - balances, positions
3. **Order placement** - buy/sell with safety checks
4. **Price alerts** - monitor and notify on moves
5. **Automated strategies** - grid trading, DCA, etc.

## Security Rules

- NEVER commit API keys to git
- Use read-only keys for price data
- Trading keys only on secure machine
- IP whitelist if possible
- Withdrawal permissions: DISABLED

## Next Steps

Run `node setup-binance.js` to configure credentials
