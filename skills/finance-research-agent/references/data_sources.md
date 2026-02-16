# Data Sources

This document describes all data sources available to the finance-research-agent, including API endpoints, rate limits, authentication requirements, and usage patterns.

## Stock/Equity Data

### Yahoo Finance (yfinance)

**Provider:** Yahoo (free, no auth required)

**Endpoints used:**
- Historical data: `yf.download(tickers, period, interval)`
- Current info: `yf.Ticker(ticker).info`
- Options chain: `yf.Ticker(ticker).options`

**Rate limits:** ~2 requests/sec; be mindful with batch downloads

**Setup:**
```bash
pip install yfinance
```

**Examples:**
```python
import yfinance as yf

# 1-month daily history
data = yf.download("AAPL", period="1mo", interval="1d")

# Current fundamentals
ticker = yf.Ticker("MSFT")
info = ticker.info  # dict with market cap, P/E, etc.
```

**Common pitfalls:**
- Ticker format: use Yahoo's symbol (e.g., `^GSPC` for S&P 500)
- Periods: `1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max`
- Intervals: `1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo`

### Alpha Vantage (optional)

**Provider:** Alpha Vantage (free tier 5 req/min, paid tiers available)

**Setup:** Requires API key from alphavantage.co

**Use case:** More comprehensive fundamental data, FX, crypto (alternatives to Yahoo)

## Cryptocurrency Data

### CoinGecko API

**Provider:** CoinGecko (free, 10-50 req/min depending on plan)

**Base URL:** `https://api.coingecko.com/api/v3`

**Key endpoints:**
- `/coins/{id}/market_chart` — historical prices
- `/coins/{id}` — current data (price, market cap, volume)
- `/coins/markets` — list all coins with current data

**Setup:**
```bash
pip install pycoingecko
```

**Examples:**
```python
from pycoingecko import CoinGeckoAPI
cg = CoinGeckoAPI()

# Bitcoin historical 90d
data = cg.get_coin_market_chart_by_id('bitcoin', vs_currency='usd', days=90)

# Current price of ETH
eth = cg.get_price('ethereum', vs_currencies='usd', include_24hr_vol=True)
```

**IDs:** Use CoinGecko coin IDs (e.g., 'bitcoin', 'ethereum', not 'BTC', 'ETH')

**Limits:** Free tier ~10-50 calls/minute; cache aggressively

## Macroeconomic Data

### FRED API

**Provider:** Federal Reserve Economic Data (free, no auth required but rate-limited)

**Base URL:** `https://api.stlouisfed.org/fred`

**Setup:**
```bash
pip install fredapi
```

**Examples:**
```python
from fredapi import Fred
fred = Fred(api_key='YOUR_KEY')  # optional but recommended

# Get 10-year Treasury yield
series = fred.get_series('DGS10')

# Observe latest CPI
cpi = fred.get_series('CPIAUCSL')
```

**Common series IDs:**
- `DGS10` — 10-Year Treasury Yield
- `FEDFUNDS` — Federal Funds Effective Rate
- `CPIAUCSL` — Consumer Price Index (All Urban Consumers)
- `UNRATE` — Unemployment Rate
- `GDP` — Gross Domestic Product
- `ICSA` — Initial Jobless Claims

**Note:** FRED updates with lag (some series weekly/monthly)

## News Data

### Google News RSS (free, no auth)

**Libraries:** `feedparser`

**RSS endpoint:**
```
https://news.google.com/rss/search?q={QUERY}&hl=en-US&gl=US&ceid=US:en
```

**Example:**
```python
import feedparser

def search_news(query, max_results=10):
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    return feed.entries[:max_results]
```

**Alternative (Better):** NewsAPI (free tier 100 req/day)
```python
# Requires API key from newsapi.org
import requests
response = requests.get(
    "https://newsapi.org/v2/everything",
    params={"q": "Tesla", "apiKey": KEY, "from": "2025-02-14"}
)
```

### Crypto-specific News

CryptoCompare, CryptoNews, or CoinDesk RSS feeds.

## Polymarket

**Provider:** Polymarket (no public API documented, but internal GraphQL endpoints exist)

**Current approach (as of 2026-02):**
- Manual tracking via UI scraping
- Monitor specific markets: US-Iran strike dates (Feb 9, Feb 28)
- Store positions in `memory/polymarket_positions.md`

**Future integration:** Build a `polymarket` skill that:
- Authenticates with wallet signature
- Queries GraphQL for markets and positions
- Subscribes to event updates (optional)

**Schema (expected):**
```json
{
  "market": {
    "id": "market-id",
    "question": "Will US attack Iran before March 1?",
    "endDate": "2026-02-28T23:59:59Z",
    "prices": {"Yes": 0.42, "No": 0.58}
  }
}
```

## Usage Patterns

### Caching

All data sources should be cached to respect rate limits:

```python
import time
from functools import lru_cache

@lru_cache(maxsize=128)
def fetch_historical(symbol, period, interval):
    # fetch logic
    pass

# Or disk-based cache for expensive queries
from diskcache import Cache
cache = Cache("cache_dir")
```

### Error Handling

- Implement retries with exponential backoff
- Handle API downtime gracefully (fallback to cached data)
- Log all errors for debugging

### Data Normalization

Convert all data to pandas DataFrames with consistent columns:
- `timestamp` (datetime)
- `open`, `high`, `low`, `close` (float)
- `volume` (integer)
- `symbol` (string)

This simplifies downstream analysis.

## Configuration

Set these environment variables (or in `config.yaml`):

```bash
# Optional API keys (only needed if using paid tiers)
ALPHAVANTAGE_KEY=your_key
FRED_API_KEY=your_key
NEWSAPI_KEY=your_key
COINGECKO_PRO_KEY=your_key  # for higher rate limits
```

## Further Reading

- `technical_indicators.md` — formulas and pandas implementation
- `polymarket_schema.md` — market data structure
- `report_builder.py` — how reports use this data
