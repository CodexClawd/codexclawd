const https = require('https');
const fs = require('fs');

// Binance API for BTC/USDT 15-minute candles
const BINANCE_API = 'api.binance.com';

function binanceRequest(path) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: BINANCE_API,
      path: path,
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    };
    
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          reject(new Error('Failed to parse response'));
        }
      });
    });
    
    req.on('error', reject);
    req.end();
  });
}

async function fetch15MinData(limit = 500) {
  console.log(`📊 Fetching ${limit} candles of BTC/USDT 15-min data...\n`);
  
  try {
    // Get 15-minute candles (interval=15m)
    // Format: [[timestamp, open, high, low, close, volume, ...], ...]
    const candles = await binanceRequest(`/api/v3/klines?symbol=BTCUSDT&interval=15m&limit=${limit}`);
    
    console.log(`✅ Fetched ${candles.length} candles`);
    
    // Transform to readable format
    const formatted = candles.map(c => ({
      timestamp: new Date(c[0]).toISOString(),
      open: parseFloat(c[1]),
      high: parseFloat(c[2]),
      low: parseFloat(c[3]),
      close: parseFloat(c[4]),
      volume: parseFloat(c[5]),
      quoteVolume: parseFloat(c[7]),
      trades: c[8]
    }));
    
    // Save raw data
    fs.writeFileSync('./btc-15min-data.json', JSON.stringify(formatted, null, 2));
    console.log(`✅ Saved to btc-15min-data.json`);
    
    // Quick stats
    const prices = formatted.map(c => c.close);
    const max = Math.max(...prices);
    const min = Math.min(...prices);
    const avg = prices.reduce((a, b) => a + b, 0) / prices.length;
    
    console.log(`\n📈 Quick Stats:`);
    console.log(`   Time range: ${formatted[0].timestamp} → ${formatted[formatted.length-1].timestamp}`);
    console.log(`   Price range: $${min.toFixed(2)} - $${max.toFixed(2)}`);
    console.log(`   Average: $${avg.toFixed(2)}`);
    console.log(`   Latest close: $${formatted[formatted.length-1].close.toFixed(2)}`);
    
    return formatted;
    
  } catch (err) {
    console.error(`❌ Error:`, err.message);
  }
}

fetch15MinData();
