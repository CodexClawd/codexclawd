const fs = require('fs');

const dump = JSON.parse(fs.readFileSync('./api-dump.json', 'utf8'));
const markets = dump.data?.markets?.data || dump.data?.markets || [];

console.log("🔍 Searching for BTC/Crypto markets...\n");

const cryptoMarkets = markets.filter(m => {
  const text = (m.question + ' ' + (m.description || '')).toLowerCase();
  return text.includes('btc') || text.includes('bitcoin') || 
         text.includes('eth') || text.includes('ethereum') ||
         text.includes('crypto') || text.includes('blur') ||
         text.includes('price of $');
});

console.log(`Found ${cryptoMarkets.length} crypto-related markets\n`);

// Categorize by type
const btcMarkets = [];
const ethMarkets = [];
const otherCrypto = [];

const timeframes = {
  '15m': [],
  '1h': [],
  '4h': [],
  '1d': [],
  'multi-day': []
};

cryptoMarkets.forEach(m => {
  const text = (m.question + ' ' + (m.description || '')).toLowerCase();
  
  // Check for BTC
  if (text.includes('btc') || text.includes('bitcoin')) {
    btcMarkets.push(m);
  } else if (text.includes('eth') || text.includes('ethereum')) {
    ethMarkets.push(m);
  } else {
    otherCrypto.push(m);
  }
  
  // Try to determine timeframe from description
  if (text.includes('1 minute') || text.includes('1m')) {
    timeframes['15m'].push(m); // Closest to 15m we have
  } else if (text.includes('hour')) {
    timeframes['1h'].push(m);
  } else if (text.includes('4 hour') || text.includes('4h')) {
    timeframes['4h'].push(m);
  } else if (text.includes('day') && !text.includes('week') && !text.includes('month')) {
    timeframes['1d'].push(m);
  } else {
    timeframes['multi-day'].push(m);
  }
});

console.log("=== BTC Markets ===");
btcMarkets.forEach((m, i) => {
  console.log(`${i + 1}. ${m.question}`);
  console.log(`   End: ${m.end_date_iso}`);
  console.log(`   Tokens:`, m.tokens?.map(t => `${t.outcome}: ${t.price}`));
  console.log();
});

console.log("\n=== ETH Markets ===");
ethMarkets.forEach((m, i) => {
  console.log(`${i + 1}. ${m.question}`);
  console.log(`   End: ${m.end_date_iso}`);
  console.log(`   Tokens:`, m.tokens?.map(t => `${t.outcome}: ${t.price}`));
  console.log();
});

console.log("\n=== Timeframe Breakdown ===");
console.log(`15m-style (1-min candles): ${timeframes['15m'].length}`);
console.log(`Hourly: ${timeframes['1h'].length}`);
console.log(`4-hour: ${timeframes['4h'].length}`);
console.log(`Daily: ${timeframes['1d'].length}`);
console.log(`Multi-day: ${timeframes['multi-day'].length}`);

// Save extracted data
const extracted = {
  btc: btcMarkets,
  eth: ethMarkets,
  other: otherCrypto,
  all: cryptoMarkets,
  timeframes: timeframes
};

fs.writeFileSync('./crypto-markets.json', JSON.stringify(extracted, null, 2));
console.log("\n✅ Saved to crypto-markets.json");
