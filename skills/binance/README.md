# Binance Skill for OpenClaw

## Setup

1. Get API keys from Binance:
   - Go to https://www.binance.com/en/my/settings/api-management
   - Create new API key (restrict to read-only for safety)
   - Add your IP to whitelist

2. Add to your `.bashrc` or export directly:
   ```bash
   export BINANCE_API_KEY="your_api_key_here"
   export BINANCE_SECRET_KEY="your_secret_key_here"
   ```

## Usage

```python
from binance.client import Client

client = Client(api_key, api_secret)

# Get account info
account = client.get_account()

# Get current price
ticker = client.get_symbol_ticker(symbol="BTCUSDT")
```

## Test Script

Run `python3 test_binance.py` to verify connection.
