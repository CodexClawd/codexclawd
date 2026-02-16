# Technical Indicators Reference

This document provides detailed formulas, interpretation, and pandas implementation for all technical indicators available in the finance-research-agent skill.

## Moving Averages

### Simple Moving Average (SMA)

**Formula:**  
SMA = (Sum of closing prices over N periods) / N

**Interpretation:**
- Trend direction: price above SMA = uptrend
- Support/resistance levels
- Crossover signals (e.g., golden cross: 50 SMA > 200 SMA)

**Pandas code:**
```python
sma = prices.rolling(window=N).mean()
```

### Exponential Moving Average (EMA)

**Formula:**  
EMA = (Close × smoothing) + (Previous EMA × (1 - smoothing))  
where smoothing = 2 / (N + 1)

**Interpretation:** Similar to SMA but gives more weight to recent prices; reacts faster to price changes.

**Pandas code:**
```python
ema = prices.ewm(span=N, adjust=False).mean()
```

---

## Momentum Oscillators

### Relative Strength Index (RSI)

**Formula:**
1. Calculate price changes: delta = close.diff()
2. Separate gains (delta > 0) and losses (delta < 0)
3. Average gain = gain.rolling(window=N).mean()
4. Average loss = (-loss).rolling(window=N).mean()
5. RS = Average gain / Average loss
6. RSI = 100 - (100 / (1 + RS))

**Standard parameters:** N = 14

**Interpretation:**
- >70: Overbought (potential sell)
- <30: Oversold (potential buy)
- Divergences (price makes new high but RSI doesn't) signal weakness

**Pandas code:**
```python
def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi
```

### Moving Average Convergence Divergence (MACD)

**Formula:**
- MACD line = EMA(12) - EMA(26)
- Signal line = EMA(9) of MACD line
- Histogram = MACD - Signal

**Interpretation:**
- Bullish: MACD crosses above signal line
- Bearish: MACD crosses below signal line
- Zero line cross: momentum shifts from negative to positive
- Divergence: price and MACD moving opposite directions

**Pandas code:**
```python
ema_fast = prices.ewm(span=12, adjust=False).mean()
ema_slow = prices.ewm(span=26, adjust=False).mean()
macd = ema_fast - ema_slow
signal = macd.ewm(span=9, adjust=False).mean()
histogram = macd - signal
```

---

## Volatility Indicators

### Bollinger Bands

**Formula:**
- Middle Band = SMA(20)
- Upper Band = SMA(20) + (std(20) × 2)
- Lower Band = SMA(20) - (std(20) × 2)
- Band Width = (Upper - Lower) / Middle

**Interpretation:**
- Squeeze (narrowing bands) → impending volatility expansion
- Price touching upper band → overbought
- Price touching lower band → oversold
- Moving average within bands confirms trend

**Pandas code:**
```python
sma = prices.rolling(window=20).mean()
std = prices.rolling(window=20).std()
upper = sma + (std * 2)
lower = sma - (std * 2)
width = (upper - lower) / sma
```

---

## Volume Indicators

### On-Balance Volume (OBV)

**Formula (cumulative):**
```
If close > previous close: OBV = previous OBV + volume
If close < previous close: OBV = previous OBV - volume
If close == previous close: OBV = previous OBV
```

**Interpretation:**
- Rising OBV with rising price = bullish confirmation
- Falling OBV with rising price = bearish divergence (potential reversal)
- OBV breakouts/breakdowns often precede price moves

**Pandas code:**
```python
def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    price_change = close.diff()
    direction = (price_change > 0).astype(int) - (price_change < 0).astype(int)
    obv_series = (direction * volume).cumsum()
    return obv_series
```

### Volume-Weighted Average Price (VWAP)

**Formula (intraday):**  
VWAP = Σ(Price × Volume) / Σ(Volume)  (from session start)

**Interpretation:**
- Institutional benchmark
- Price above VWAP = buyers in control
- Price below VWAP = sellers in control

**Note:** VWAP resets each trading session. We typically compute on 1-min/5-min intraday data.

---

## Candlestick Patterns

### Doji

**Pattern:** Open ≈ Close (small body), shadows can be long

**Significance:** Indecision; potential reversal when appearing at trend tops/bottoms

**Detection:**
```python
body = abs(close - open)
range_ = high - low
is_doji = (body / range_ < 0.1) & (range_ > 0)
```

### Hammer

**Pattern:** Small body near top, long lower shadow (≥2× body), little/no upper shadow

**Significance:** Bullish reversal when appearing at downtrend bottom

**Detection:**
```python
lower_shadow = min(open, close) - low
upper_shadow = high - max(open, close)
body = abs(close - open)
is_hammer = (lower_shadow > 2 * body) & (upper_shadow < 0.25 * body)
```

### Engulfing

**Pattern:** Current candle's body completely contains previous candle's body

**Significance:**
- Bullish engulfing: downtrend, current candle bullish (close > open)
- Bearish engulfing: uptrend, current candle bearish (close < open)

**Detection:**
```python
prev_body_high = max(prev_open, prev_close)
prev_body_low = min(prev_open, prev_close)
curr_body_high = max(open, close)
curr_body_low = min(open, close)

bullish_engulfing = (curr_body_low < prev_body_low) & (curr_body_high > prev_body_high) & (close > open) & (prev_close < prev_open)
```

---

## Support & Resistance

### Pivot Points (Standard)

**Daily pivots from previous day's HLC:**
```
Pivot (P) = (High + Low + Close) / 3
Support 1 (S1) = (2 × P) - High
Support 2 (S2) = P - (High - Low)
Resistance 1 (R1) = (2 × P) - Low
Resistance 2 (R2) = P + (High - Low)
```

**Interpretation:** Price often reacts at these levels; they act as magnets.

---

## Trend Indicators

### Average Directional Index (ADX)

**Formula:**
1. Calculate +DM and -DM (directional movement)
2. True Range (TR)
3. +DI = ( +DM / TR ) × 100 (smoothed)
4. -DI = ( -DM / TR ) × 100 (smoothed)
5. DX = (|+DI - -DI| / |+DI + -DI|) × 100
6. ADX = EMA of DX

**Interpretation:**
- ADX < 20: weak trend / ranging market
- ADX > 25: strong trend emerging
- ADX > 50: very strong trend
- Use +DI/-DI cross for direction

---

## Multi-Indicator Confirmation

**Best Practice:** Never rely on a single indicator.

| Signal Type | Confirmations Needed |
|-------------|----------------------|
| Uptrend start | Price > SMA(200) + ADX > 25 + MACD bullish cross |
| Overbought | RSI > 70 + price at upper Bollinger Band + volume declining |
| Reversal pattern (hammer) | Appears at support + RSI oversold + bullish engulfing follow-up |

---

## Implementation Notes

- All functions return pandas `Series` aligned with input price index
- NaN values appear for initial periods (warm-up)
- For intraday data, adjust periods accordingly (e.g., RSI(14) on 1h = 14 hours)
- Cache intermediate calculations when building multi-indicator reports

---

## References

- `data_sources.md` — fetching price data
- `report_builder.py` — embedding indicators in reports
