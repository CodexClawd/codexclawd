const { ClobClient } = require("@polymarket/clob-client");
const { Wallet } = require("@ethersproject/wallet");
const fs = require("fs");

const config = JSON.parse(fs.readFileSync('./config.json', 'utf8'));
const wallet = JSON.parse(fs.readFileSync('./wallet.json', 'utf8'));

async function dumpApiData() {
  try {
    const signer = new Wallet(wallet.privateKey);
    const creds = { apiKey: config.apiKey, secret: config.secret, passphrase: config.passphrase };
    const client = new ClobClient(config.host, config.chainId, signer, creds, config.signatureType, config.funder);
    
    console.log("📊 Dumping all available CLOB API data...\n");
    const dump = {
      timestamp: new Date().toISOString(),
      wallet: config.funder,
      data: {}
    };
    
    // 1. Try to get markets
    console.log("1. Fetching markets...");
    try {
      const markets = await client.getMarkets();
      dump.data.markets = markets;
      console.log(`   ✅ Found ${markets?.length || 0} markets`);
    } catch (e) {
      console.log(`   ❌ Error: ${e.message}`);
      dump.data.marketsError = e.message;
    }
    
    // 2. Try to get trades
    console.log("2. Fetching trade history...");
    try {
      const trades = await client.getTradeHistory();
      dump.data.trades = trades;
      console.log(`   ✅ Found ${trades?.length || 0} trades`);
    } catch (e) {
      console.log(`   ❌ Error: ${e.message}`);
      dump.data.tradesError = e.message;
    }
    
    // 3. Try to get orders
    console.log("3. Fetching open orders...");
    try {
      const orders = await client.getOpenOrders();
      dump.data.orders = orders;
      console.log(`   ✅ Found ${orders?.length || 0} open orders`);
    } catch (e) {
      console.log(`   ❌ Error: ${e.message}`);
      dump.data.ordersError = e.message;
    }
    
    // 4. Try to get positions
    console.log("4. Fetching positions...");
    try {
      // Try different methods that might exist
      let positions = null;
      if (client.getPositions) {
        positions = await client.getPositions();
      } else if (client.getBalance) {
        positions = await client.getBalance();
      }
      dump.data.positions = positions;
      console.log(`   ✅ Found positions:`, positions ? JSON.stringify(positions).substring(0, 100) : 'null');
    } catch (e) {
      console.log(`   ❌ Error: ${e.message}`);
      dump.data.positionsError = e.message;
    }
    
    // 5. Get last trade price for a sample token if available
    console.log("5. Checking for sample market data...");
    if (dump.data.markets && dump.data.markets.length > 0) {
      const sampleMarket = dump.data.markets[0];
      console.log(`   Sample market: ${sampleMarket.question || sampleMarket.title || 'N/A'}`);
      
      if (sampleMarket.tokens && sampleMarket.tokens[0]) {
        const tokenId = sampleMarket.tokens[0].token_id;
        console.log(`   Trying to get orderbook for token: ${tokenId}`);
        
        try {
          const orderbook = await client.getOrderBook(tokenId);
          dump.data.sampleOrderbook = orderbook;
          console.log(`   ✅ Got orderbook`);
        } catch (e) {
          console.log(`   ❌ Error: ${e.message}`);
        }
      }
    }
    
    // Save everything
    fs.writeFileSync('./api-dump.json', JSON.stringify(dump, null, 2));
    console.log("\n✅ All data saved to api-dump.json");
    
    // Also save a summary
    const summary = {
      timestamp: dump.timestamp,
      wallet: config.funder,
      marketsCount: dump.data.markets?.length || 0,
      tradesCount: dump.data.trades?.length || 0,
      ordersCount: dump.data.orders?.length || 0,
      hasPositions: dump.data.positions !== null,
      errors: Object.keys(dump.data).filter(k => k.includes('Error'))
    };
    
    fs.writeFileSync('./api-summary.json', JSON.stringify(summary, null, 2));
    console.log("✅ Summary saved to api-summary.json");
    console.log("\n📈 Summary:", JSON.stringify(summary, null, 2));
    
  } catch (err) {
    console.error("❌ Fatal error:", err.message);
    console.error(err);
  }
}

dumpApiData();
