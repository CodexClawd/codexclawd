#!/usr/bin/env node
// Manual price update script - Flo reports prices, we track changes
const fs = require('fs');

const DATA_FILE = './price-tracker.json';
const ALERT_THRESHOLD = 0.05; // 5%

function loadData() {
  return JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
}

function saveData(data) {
  fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
}

function formatPrice(p) {
  return p ? `${(p * 100).toFixed(1)}%` : 'N/A';
}

function updatePrice(marketName, newPrice) {
  const data = loadData();
  const market = data.markets[marketName];
  
  if (!market) {
    console.log(`❌ Market not found: ${marketName}`);
    return;
  }
  
  const oldPrice = market.currentPrice;
  market.previousPrice = oldPrice;
  market.currentPrice = newPrice;
  
  let change = null;
  let alert = false;
  
  if (oldPrice !== null) {
    change = (newPrice - oldPrice) / oldPrice;
    market.lastChange = change;
    
    if (Math.abs(change) >= ALERT_THRESHOLD) {
      alert = true;
    }
  }
  
  // Calculate portfolio value
  const portfolioValue = newPrice * market.positions.contracts;
  const profit = portfolioValue - market.positions.totalCost;
  
  // Log history
  data.history.push({
    timestamp: new Date().toISOString(),
    market: marketName,
    price: newPrice,
    change: change,
    portfolioValue,
    profit
  });
  
  data.lastUpdated = new Date().toISOString();
  saveData(data);
  
  // Output
  console.log(`\n📊 ${marketName}`);
  console.log(`   Price: ${formatPrice(oldPrice)} → ${formatPrice(newPrice)}`);
  
  if (change !== null) {
    const arrow = change > 0 ? '↑' : '↓';
    const color = Math.abs(change) >= ALERT_THRESHOLD ? '🚨' : '';
    console.log(`   Change: ${color} ${arrow} ${(Math.abs(change) * 100).toFixed(1)}% ${color}`);
  }
  
  console.log(`   Portfolio: $${portfolioValue.toFixed(2)} (profit: $${profit.toFixed(2)})`);
  
  if (alert) {
    console.log(`\n⚠️  ALERT: Price moved ${Math.abs(change * 100).toFixed(1)}%!`);
    // Write alert file for notification
    fs.writeFileSync('./alert.txt', 
      `🚨 POLYMARKET ALERT\n\n` +
      `${marketName}\n` +
      `Price: ${formatPrice(oldPrice)} → ${formatPrice(newPrice)}\n` +
      `Change: ${change > 0 ? '+' : ''}${(change * 100).toFixed(1)}%\n\n` +
      `URL: ${market.url}`
    );
  }
}

// CLI usage
const args = process.argv.slice(2);
if (args.length < 2) {
  console.log('Usage: node manual-tracker.js <market> <price>');
  console.log('\nMarkets:');
  console.log('  feb9  - US Strikes Iran by Feb 9, 2026');
  console.log('  feb28 - US Strikes Iran by Feb 28, 2026');
  console.log('\nExample: node manual-tracker.js feb9 0.12');
  process.exit(1);
}

const marketKey = args[0].toLowerCase();
const price = parseFloat(args[1]);

const marketMap = {
  'feb9': 'US Strikes Iran by Feb 9, 2026',
  'feb28': 'US Strikes Iran by Feb 28, 2026'
};

const marketName = marketMap[marketKey];
if (!marketName) {
  console.log(`❌ Unknown market: ${marketKey}`);
  console.log('Use: feb9 or feb28');
  process.exit(1);
}

if (isNaN(price) || price < 0 || price > 1) {
  console.log('❌ Price must be between 0 and 1 (e.g., 0.12 for 12%)');
  process.exit(1);
}

updatePrice(marketName, price);
