"""
finance-research-agent API

This module provides the core functions for the finance-research-agent skill.
All functions are designed to be imported and used by the agent's decision logic.

Key patterns:
- Always return pandas DataFrames or dictionaries with consistent keys
- Handle errors gracefully (return empty/None with logged error)
- Cache results when possible (decorate with @lru_cache or diskcache)
- Use UTC timestamps for all time-sensitive data
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import logging

logger = logging.getLogger(__name__)

# === Market Data ===

def fetch_historical(symbol: str, period: str = "1mo", interval: str = "1d", source: str = "yahoo") -> pd.DataFrame:
    """
    Fetch historical OHLCV data for a symbol.

    Args:
        symbol: Ticker symbol (e.g., 'AAPL', 'BTC-USD', '^GSPC')
        period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
        interval: Data interval ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
        source: Data source ('yahoo', 'polygon', 'alphavantage')

    Returns:
        DataFrame with columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'symbol']
    """
    try:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            logger.warning(f"No data returned for {symbol}")
            return pd.DataFrame()

        # Normalize columns
        df = df.reset_index()
        df = df.rename(columns={
            'Date': 'timestamp',
            'Datetime': 'timestamp',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })

        # Add symbol column
        df['symbol'] = symbol

        # Ensure types
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'symbol']].copy()

    except Exception as e:
        logger.error(f"Error fetching historical data for {symbol}: {e}")
        return pd.DataFrame()


def fetch_current(symbol: str, source: str = "yahoo") -> Dict[str, Any]:
    """
    Fetch current quote data for a symbol.

    Args:
        symbol: Ticker symbol
        source: Data source ('yahoo', 'coingecko')

    Returns:
        Dictionary with keys: ['price', 'change', 'change_percent', 'volume', 'market_cap', 'timestamp']
    """
    try:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        info = ticker.info

        result = {
            'symbol': symbol,
            'price': info.get('regularMarketPrice') or info.get('currentPrice'),
            'change': info.get('regularMarketChange'),
            'change_percent': info.get('regularMarketChangePercent'),
            'volume': info.get('regularMarketVolume'),
            'market_cap': info.get('marketCap'),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

        # Clean None values
        return {k: v for k, v in result.items() if v is not None}

    except Exception as e:
        logger.error(f"Error fetching current data for {symbol}: {e}")
        return {}


def fetch_crypto_historical(coin_id: str, days: int = 90, vs_currency: str = "usd") -> pd.DataFrame:
    """
    Fetch cryptocurrency historical data from CoinGecko.

    Args:
        coin_id: CoinGecko coin ID (e.g., 'bitcoin', 'ethereum')
        days: Number of days of history (max 365 for free tier)
        vs_currency: Quote currency (default 'usd')

    Returns:
        DataFrame with columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'symbol']
    """
    try:
        from pycoingecko import CoinGeckoAPI
        cg = CoinGeckoAPI()

        data = cg.get_coin_market_chart_by_id(coin_id, vs_currency=vs_currency, days=days)

        prices = data['prices']  # [[timestamp, price], ...]
        volumes = data['total_volumes']  # [[timestamp, volume], ...]

        df = pd.DataFrame(prices, columns=['timestamp', 'close'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['volume'] = [v[1] for v in volumes]

        # CoinGecko only gives closing price per day/hour.
        # Estimate O/H/L from intraday volatility if needed.
        df['open'] = df['close'].shift(1)
        df['high'] = df['close'] * 1.002  # rough estimate
        df['low'] = df['close'] * 0.998

        df['symbol'] = coin_id
        return df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'symbol']].copy()

    except Exception as e:
        logger.error(f"Error fetching crypto data for {coin_id}: {e}")
        return pd.DataFrame()


# === Technical Analysis ===

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index.

    Args:
        prices: Series of closing prices
        period: RSI period (default 14)

    Returns:
        Series of RSI values (0-100)
    """
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    Returns:
        Dict with keys: 'macd', 'signal', 'histogram'
    """
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }


def calculate_sma(prices: pd.Series, window: int) -> pd.Series:
    """Simple Moving Average."""
    return prices.rolling(window=window).mean()


def calculate_ema(prices: pd.Series, window: int) -> pd.Series:
    """Exponential Moving Average."""
    return prices.ewm(span=window, adjust=False).mean()


def calculate_bollinger_bands(prices: pd.Series, window: int = 20, num_std: float = 2.0) -> Dict[str, pd.Series]:
    """
    Bollinger Bands: SMA ± (std * num_std)
    """
    sma = calculate_sma(prices, window)
    std = prices.rolling(window=window).std()
    upper = sma + (std * num_std)
    lower = sma - (std * num_std)

    return {
        'middle': sma,
        'upper': upper,
        'lower': lower,
        'width': (upper - lower) / sma
    }


def detect_candlestick_patterns(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Detect common candlestick patterns (doji, hammer, engulfing, etc.)

    Args:
        df: DataFrame with columns ['open', 'high', 'low', 'close']

    Returns:
        List of pattern detections with date and pattern name
    """
    patterns = []

    # Simple doji detection
    body = abs(df['close'] - df['open'])
    range_ = df['high'] - df['low']
    doji_condition = (body / range_ < 0.1) & (range_ > 0)
    if doji_condition.any():
        for idx in df[doji_condition].index:
            patterns.append({
                'date': df.loc[idx, 'timestamp'],
                'pattern': 'doji',
                'confidence': 0.7
            })

    # Hammer (simple version)
    lower_shadow = df[['open', 'close']].min(axis=1) - df['low']
    upper_shadow = df['high'] - df[['open', 'close']].max(axis=1)
    body = abs(df['close'] - df['open'])
    hammer_condition = (lower_shadow > 2 * body) & (upper_shadow < body * 0.25)
    if hammer_condition.any():
        for idx in df[hammer_condition].index:
            patterns.append({
                'date': df.loc[idx, 'timestamp'],
                'pattern': 'hammer',
                'confidence': 0.6
            })

    return patterns


# === News Scanning ===

def scan_news(query: str, hours_back: int = 24, max_results: int = 20) -> List[Dict[str, Any]]:
    """
    Search financial news for a given query.

    Args:
        query: Search term (ticker, company name, topic)
        hours_back: How many hours to look back
        max_results: Maximum number of articles to return

    Returns:
        List of article dicts with keys: ['title', 'url', 'published', 'source', 'snippet']
    """
    try:
        import feedparser
        from datetime import datetime, timedelta

        # Build RSS URL
        encoded_query = query.replace(' ', '+')
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

        feed = feedparser.parse(rss_url)
        cutoff = datetime.utcnow() - timedelta(hours=hours_back)

        articles = []
        for entry in feed.entries[:max_results]:
            published = datetime(*entry.published_parsed[:6]) if entry.get('published_parsed') else None

            if published and published < cutoff:
                continue

            articles.append({
                'title': entry.title,
                'url': entry.link,
                'published': published.isoformat() + 'Z' if published else None,
                'source': entry.source.title if entry.get('source') else 'Unknown',
                'snippet': entry.summary if entry.get('summary') else ''
            })

        return articles

    except Exception as e:
        logger.error(f"Error scanning news for '{query}': {e}")
        return []


def analyze_sentiment(text: str) -> str:
    """
    Simple sentiment analysis (negative, neutral, positive).

    Note: For production use, integrate with a sentiment API (OpenRouter, Anthropic, etc.)
    """
    # Simple keyword-based sentiment (replace with ML model for production)
    positive_words = ['bull', 'gain', 'rise', 'up', 'growth', 'strong', 'buy', 'success', 'profit']
    negative_words = ['bear', 'fall', 'drop', 'down', 'loss', 'weak', 'sell', 'fail', 'crash']

    text_lower = text.lower()
    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)

    if pos_count > neg_count:
        return 'positive'
    elif neg_count > pos_count:
        return 'negative'
    else:
        return 'neutral'


def aggregate_sentiment(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate sentiment across multiple articles.
    """
    sentiments = [analyze_sentiment(a['snippet'] + ' ' + a['title']) for a in articles]

    total = len(sentiments)
    positive = sum(1 for s in sentiments if s == 'positive')
    negative = sum(1 for s in sentiments if s == 'negative')
    neutral = total - positive - negative

    return {
        'total': total,
        'positive': positive,
        'negative': negative,
        'neutral': neutral,
        'overall': 'positive' if positive > negative else 'negative' if negative > positive else 'neutral',
        'articles': articles
    }


# === Polymarket Integration ===

def get_polymarket_positions() -> List[Dict[str, Any]]:
    """
    Fetch all active positions from memory/polymarket_positions.md.

    Returns:
        List of position dicts (parsed from markdown file)
    """
    try:
        from pathlib import Path

        pos_file = Path('memory/polymarket_positions.md')
        if not pos_file.exists():
            logger.warning("Polymarket positions file not found")
            return []

        content = pos_file.read_text()
        positions = []

        # Parse simple markdown format:
        # - Market: [question]
        #   - Position: Yes (100 shares @ $0.45)
        current_position = None
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('- Market:'):
                if current_position:
                    positions.append(current_position)
                current_position = {'question': line.replace('- Market:', '').strip(), 'positions': []}
            elif line.startswith('- Position:') and current_position:
                parts = line.replace('- Position:', '').strip()
                # e.g., "Yes (100 shares @ $0.45)"
                current_position['positions'].append(parts)

        if current_position:
            positions.append(current_position)

        return positions

    except Exception as e:
        logger.error(f"Error reading Polymarket positions: {e}")
        return []


def check_polymarket_alerts(threshold_pct: float = 20.0) -> List[Dict[str, Any]]:
    """
    Check if any Polymarket probabilities moved >threshold_pct% since last check.
    Requires storing previous snapshots in memory.
    """
    # TODO: Implement snapshot comparison
    # For now, return empty list
    return []


# === Report Generation ===

def build_report(data: Dict[str, Any], template_path: str, output_path: str) -> str:
    """
    Generate a markdown report from a Jinja2 template.

    Args:
        data: Dictionary of variables to pass to template
        template_path: Path to .md template (in assets/templates/)
        output_path: Where to save the rendered report

    Returns:
        Path to generated report
    """
    try:
        from jinja2 import Environment, FileSystemLoader
        import os

        template_dir = os.path.dirname(template_path)
        template_name = os.path.basename(template_path)

        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(template_name)

        rendered = template.render(**data)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(rendered)

        logger.info(f"Report generated: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Error building report: {e}")
        return ""


def generate_snapshot_report(symbol: str, output_dir: str = "memory/reports/") -> str:
    """
    Quick 1-2 page report for a single ticker.
    """
    # 1. Fetch data
    df = fetch_historical(symbol, period="1mo", interval="1d")
    if df.empty:
        return ""

    current = fetch_current(symbol)
    rsi = calculate_rsi(df['close'], period=14).iloc[-1]
    sma_50 = calculate_sma(df['close'], 50).iloc[-1] if len(df) >= 50 else None
    sma_200 = calculate_sma(df['close'], 200).iloc[-1] if len(df) >= 200 else None

    # 2. Get news
    articles = scan_news(symbol, hours_back=48, max_results=10)
    sentiment = aggregate_sentiment(articles)

    # 3. Build report
    from datetime import datetime
    data = {
        'symbol': symbol,
        'date': datetime.utcnow().strftime('%Y-%m-%d'),
        'current_price': current.get('price'),
        'change_pct': current.get('change_percent'),
        'volume': current.get('volume'),
        'market_cap': current.get('market_cap'),
        'rsi': round(rsi, 2),
        'sma_50': round(sma_50, 2) if sma_50 else None,
        'sma_200': round(sma_200, 2) if sma_200 else None,
        'news': sentiment['articles'][:5],
        'sentiment_summary': sentiment['overall']
    }

    output_path = os.path.join(output_dir, f"{symbol}_snapshot_{datetime.utcnow().strftime('%Y%m%d')}.md")
    return build_report(data, "assets/templates/report_snapshot.md", output_path)


# === Alert Manager ===

def check_alerts(watchlist: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Check all alerts in the watchlist and return triggered ones.

    Watchlist format:
    [
        {
            'symbol': 'BTC-USD',
            'alerts': [
                {'type': 'price_above', 'value': 100000},
                {'type': 'rsi_below', 'value': 30},
                {'type': 'volume_spike', 'multiple': 2.0}
            ]
        },
        ...
    ]
    """
    triggered = []

    for item in watchlist:
        symbol = item['symbol']
        current = fetch_current(symbol)
        df = fetch_historical(symbol, period="5d", interval="1d")

        if df.empty:
            continue

        rsi = calculate_rsi(df['close'], period=14).iloc[-1]
        avg_volume = df['volume'].mean()
        current_price = current.get('price')

        for alert in item['alerts']:
            alert_type = alert['type']
            triggered_alert = None

            if alert_type == 'price_above' and current_price and current_price > alert['value']:
                triggered_alert = f"{symbol} price ${current_price:,.2f} above ${alert['value']:,.2f}"

            elif alert_type == 'price_below' and current_price and current_price < alert['value']:
                triggered_alert = f"{symbol} price ${current_price:,.2f} below ${alert['value']:,.2f}"

            elif alert_type == 'rsi_below' and rsi < alert['value']:
                triggered_alert = f"{symbol} RSI {rsi:.1f} below {alert['value']} (oversold)"

            elif alert_type == 'rsi_above' and rsi > alert['value']:
                triggered_alert = f"{symbol} RSI {rsi:.1f} above {alert['value']} (overbought)"

            elif alert_type == 'volume_spike' and current.get('volume', 0) > avg_volume * alert['multiple']:
                triggered_alert = f"{symbol} volume {current['volume']:,} > {alert['multiple']}x average ({avg_volume:,.0f})"

            if triggered_alert:
                triggered.append({
                    'symbol': symbol,
                    'message': triggered_alert,
                    'alert': alert,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })

    return triggered
