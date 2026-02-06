const { ClobClient } = require("@polymarket/clob-client");
const { Wallet } = require("@ethersproject/wallet");
const fs = require("fs");

const config = JSON.parse(fs.readFileSync('./config.json', 'utf8'));
const wallet = JSON.parse(fs.readFileSync('./wallet.json', 'utf8'));

async function findMarkets() {
  try {
    const signer = new Wallet(wallet.privateKey);
    const creds = { apiKey: config.apiKey, secret: config.secret, passphrase: config.passphrase };
    const client = new ClobClient(config.host, config.chainId, signer, creds, config.signatureType, config.funder);
    
    console.log("🔍 Searching for your markets...\n");
    
    // Get all markets
    const markets = await client.getMarkets();
    console.log(`Found ${markets?.length || 0} total markets\n`);
    
    // Search for Iran-related markets
    const searchTerms = ['iran', 'strike', 'us strikes'];
    const matches = [];
    
    for (const market of markets || []) {
      const desc = (market.description || market.question || '').toLowerCase();
      if (searchTerms.some(term => desc.includes(term))) {
        matches.push({
          question: market.question,
          conditionId: market.conditionId,
          tokenIds: market.tokens?.map(t => ({ 
            tokenId: t.token_id, 
            outcome: t.outcome 
          }))
        });
      }
    }
    
    if (matches.length === 0) {
      console.log("No Iran markets found in active markets.");
      console.log("Your positions might be on older markets not in the active list.");
      console.log("\nTrying to fetch specific markets by URL...");
      
      // Try to get markets by known condition IDs from Polymarket URLs
      // Feb 9 market: https://polymarket.com/event/us-strikes-iran-by/us-strikes-iran-by-february-9-2026-113-751
      // Feb 28 market: https://polymarket.com/event/us-strikes-iran-by/us-strikes-iran-by-february-28-2026...
      
    } else {
      console.log(`Found ${matches.length} matching markets:\n`);
      matches.forEach((m, i) => {
        console.log(`${i + 1}. ${m.question}`);
        console.log(`   Condition ID: ${m.conditionId}`);
        console.log(`   Tokens:`, m.tokenIds);
        console.log();
      });
    }
    
    // Also check your positions directly
    console.log("📊 Checking your positions...");
    try {
      const positions = await client.getPositions();
      console.log("Positions:", JSON.stringify(positions, null, 2));
    } catch (e) {
      console.log("Could not fetch positions:", e.message);
    }
    
  } catch (err) {
    console.error("❌ Error:", err.message);
    console.error(err);
  }
}

findMarkets();
