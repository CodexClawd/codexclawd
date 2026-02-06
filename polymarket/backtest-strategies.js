const fs = require('fs');

const data = JSON.parse(fs.readFileSync('./btc-15min-data.json', 'utf8'));

console.log("📊 BTC/USDT 15-Minute Strategy Backtest\n");
console.log(`Total candles: ${data.length}`);
console.log(`Period: ${data[0].timestamp} → ${data[data.length-1].timestamp}\n`);

// Strategy 1: Simple momentum (3-candle trend)
function momentumStrategy() {
  console.log("=== Strategy 1: 3-Candle Momentum ===");
  let wins = 0, losses = 0;
  
  for (let i = 3; i < data.length - 1; i++) {
    const prev3 = [data[i-3], data[i-2], data[i-1]];
    const current = data[i];
    const next = data[i+1];
    
    // Check for 3 consecutive up/down candles
    const upTrend = prev3.every(c => c.close > c.open);
    const downTrend = prev3.every(c => c.close < c.open);
    
    if (upTrend || downTrend) {
      const direction = upTrend ? 'UP' : 'DOWN';
      const nextMove = next.close > current.close ? 'UP' : 'DOWN';
      
      if (direction === nextMove) wins++;
      else losses++;
    }
  }
  
  const total = wins + losses;
  const winRate = total > 0 ? (wins / total * 100).toFixed(1) : 0;
  console.log(`Signals: ${total}`);
  console.log(`Win rate: ${winRate}% (${wins}/${total})`);
  console.log();
}

// Strategy 2: Breakout (break previous candle high/low)
function breakoutStrategy() {
  console.log("=== Strategy 2: Breakout Trading ===");
  let wins = 0, losses = 0;
  
  for (let i = 2; i < data.length - 1; i++) {
    const prev = data[i-1];
    const current = data[i];
    const next = data[i+1];
    
    // Break above previous high = BUY
    // Break below previous low = SELL
    const breakHigh = current.close > prev.high;
    const breakLow = current.close < prev.low;
    
    if (breakHigh) {
      const nextMove = next.close > current.close ? 'UP' : 'DOWN';
      if (nextMove === 'UP') wins++;
      else losses++;
    } else if (breakLow) {
      const nextMove = next.close < current.close ? 'DOWN' : 'UP';
      if (nextMove === 'DOWN') wins++;
      else losses++;
    }
  }
  
  const total = wins + losses;
  const winRate = total > 0 ? (wins / total * 100).toFixed(1) : 0;
  console.log(`Signals: ${total}`);
  console.log(`Win rate: ${winRate}% (${wins}/${total})`);
  console.log();
}

// Strategy 3: Range reversal (RSI-style overbought/oversold)
function rangeReversalStrategy() {
  console.log("=== Strategy 3: Range Reversal ===");
  let wins = 0, losses = 0;
  
  // Calculate rolling 20-candle high/low
  for (let i = 20; i < data.length - 1; i++) {
    const range = data.slice(i-20, i);
    const highs = range.map(c => c.high);
    const lows = range.map(c => c.low);
    const rangeHigh = Math.max(...highs);
    const rangeLow = Math.min(...lows);
    
    const current = data[i];
    const next = data[i+1];
    
    // Near top of range = SELL (expect reversal down)
    // Near bottom of range = BUY (expect reversal up)
    const nearTop = current.close > rangeHigh * 0.995;
    const nearBottom = current.close < rangeLow * 1.005;
    
    if (nearTop) {
      const nextMove = next.close < current.close ? 'DOWN' : 'UP';
      if (nextMove === 'DOWN') wins++;
      else losses++;
    } else if (nearBottom) {
      const nextMove = next.close > current.close ? 'UP' : 'DOWN';
      if (nextMove === 'UP') wins++;
      else losses++;
    }
  }
  
  const total = wins + losses;
  const winRate = total > 0 ? (wins / total * 100).toFixed(1) : 0;
  console.log(`Signals: ${total}`);
  console.log(`Win rate: ${winRate}% (${wins}/${total})`);
  console.log();
}

// Strategy 4: Volatility squeeze (low vol followed by breakout)
function volatilitySqueezeStrategy() {
  console.log("=== Strategy 4: Volatility Squeeze ===");
  let wins = 0, losses = 0;
  
  for (let i = 5; i < data.length - 1; i++) {
    const prev5 = data.slice(i-5, i);
    const current = data[i];
    const next = data[i+1];
    
    // Calculate average range of last 5 candles
    const ranges = prev5.map(c => c.high - c.low);
    const avgRange = ranges.reduce((a, b) => a + b, 0) / ranges.length;
    const currentRange = current.high - current.low;
    
    // Squeeze = current range < 50% of average
    const squeeze = currentRange < avgRange * 0.5;
    
    if (squeeze) {
      // Buy if breakout up, sell if breakout down
      const breakoutUp = current.close > prev5[4].high;
      const breakoutDown = current.close < prev5[4].low;
      
      if (breakoutUp) {
        const nextMove = next.close > current.close ? 'UP' : 'DOWN';
        if (nextMove === 'UP') wins++;
        else losses++;
      } else if (breakoutDown) {
        const nextMove = next.close < current.close ? 'DOWN' : 'UP';
        if (nextMove === 'DOWN') wins++;
        else losses++;
      }
    }
  }
  
  const total = wins + losses;
  const winRate = total > 0 ? (wins / total * 100).toFixed(1) : 0;
  console.log(`Signals: ${total}`);
  console.log(`Win rate: ${winRate}% (${wins}/${total})`);
  console.log();
}

// Run all strategies
momentumStrategy();
breakoutStrategy();
rangeReversalStrategy();
volatilitySqueezeStrategy();

console.log("\n⚠️  Note: These are simple naive strategies for demonstration.");
console.log("Real backtesting requires more data, fees, slippage modeling.");
