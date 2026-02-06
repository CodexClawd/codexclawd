const { ClobClient } = require("@polymarket/clob-client");
const { Wallet } = require("@ethersproject/wallet");
const fs = require("fs");

const config = JSON.parse(fs.readFileSync('./config.json', 'utf8'));
const wallet = JSON.parse(fs.readFileSync('./wallet.json', 'utf8'));
const PRICE_FILE = './price_history.json';
const ALERT_THRESHOLD = 0.05; // 5%

// Your US-Iran markets (you'll need to update these when you enter new positions)
const TRACKED_MARKETS = [
  {
    name: "US Strikes Iran by Feb 9, 2026",
    conditionId: "0x0c2b0e831227f6a80373892b6cb8e89c1cd4f3b5b0b6a3c6e9d8f7a6b5c4d3e2", // Placeholder - update with real ID
    tokenId: null // Will be fetched
  },
  {
    name: "US Strikes Iran by Feb 28, 2026", 
    conditionId: "0x1d3c1f942338g7b914849a3c7da0e4f2de5g4c6c1c7b4d7f0a8b7c6d5e4f3g1", // Placeholder - update with real ID
    tokenId: null
  }
];

async function getPriceHistory() {
  if (!fs.existsSync(PRICE_FILE)) return {};
  return JSON.parse(fs.readFileSync(PRICE_FILE, 'utf8'));
}

function savePriceHistory(history) {
  fs.writeFileSync(PRICE_FILE, JSON.stringify(history, null, 2));
}

async function checkPrices() {
  try {
    const signer = new Wallet(wallet.privateKey);
    const creds = { apiKey: config.apiKey, secret: config.secret, passphrase: config.passphrase };
    const client = new ClobClient(config.host, config.chainId, signer, creds, config.signatureType, config.funder);
    
    console.log("🔍 Checking Polymarket prices...\n");
    
    const history = await getPriceHistory();
    const alerts = [];
    const timestamp = new Date().toISOString();
    
    for (const market of TRACKED_MARKETS) {
      try {
        // Get market orderbook for YES token
        if (!market.tokenId) {
          console.log(`⚠️  Need token ID for: ${market.name}`);
          continue;
        }
        
        const orderbook = await client.getOrderBook(market.tokenId);
        const bestBid = orderbook.bids?.[0]?.price || 0;
        const bestAsk = orderbook.asks?.[0]?.price || 0;
        const midPrice = bestBid && bestAsk ? (bestBid + bestAsk) / 2 : bestBid || bestAsk;
        
        const prevPrice = history[market.name]?.price;
        const change = prevPrice ? ((midPrice - prevPrice) / prevPrice) : 0;
        const changePct = (change * 100).toFixed(2);
        
        // Log current price
        console.log(`${market.name}:`);
        console.log(`  Price: ${(midPrice * 100).toFixed(1)}% (was: ${prevPrice ? (prevPrice * 100).toFixed(1) : 'N/A'}%)`);
        console.log(`  Change: ${change > 0 ? '+' : ''}${changePct}%`);
        
        // Check for alert
        if (prevPrice && Math.abs(change) >= ALERT_THRESHOLD) {
          alerts.push({
            market: market.name,
            oldPrice: prevPrice,
            newPrice: midPrice,
            change: change,
            changePct: changePct
          });
        }
        
        // Update history
        history[market.name] = {
          price: midPrice,
          timestamp: timestamp,
          changeFromLast: change
        };
        
      } catch (err) {
        console.error(`  ❌ Error checking ${market.name}:`, err.message);
      }
    }
    
    savePriceHistory(history);
    
    // Output alerts for notification system
    if (alerts.length > 0) {
      console.log("\n🚨 PRICE ALERTS:");
      alerts.forEach(a => {
        console.log(`\n⚠️  ${a.market}`);
        console.log(`   Changed ${a.change > 0 ? '↑' : '↓'} ${Math.abs(a.change * 100).toFixed(1)}%`);
        console.log(`   ${(a.oldPrice * 100).toFixed(1)}% → ${(a.newPrice * 100).toFixed(1)}%`);
      });
      
      // Write alerts file for external notification
      fs.writeFileSync('./alerts.json', JSON.stringify({ alerts, timestamp }, null, 2));
      process.exit(1); // Non-zero exit to trigger notification
    } else {
      console.log("\n✅ No significant price changes");
      process.exit(0);
    }
    
  } catch (err) {
    console.error("❌ Fatal error:", err.message);
    process.exit(2);
  }
}

// If run directly
checkPrices();
