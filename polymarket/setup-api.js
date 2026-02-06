const { ClobClient } = require("@polymarket/clob-client");
const { Wallet } = require("@ethersproject/wallet");
const fs = require("fs");

const host = 'https://clob.polymarket.com';
const wallet = JSON.parse(fs.readFileSync('./wallet.json', 'utf8'));

async function setupApi() {
  try {
    console.log("Deriving API credentials...");
    
    const signer = new Wallet(wallet.privateKey);
    const clobClient = new ClobClient(host, 137, signer, null, 1, wallet.funder);
    
    const creds = await clobClient.deriveApiKey();
    console.log("Raw response:", creds);
    
    // The derive might return different field names
    const config = {
      host,
      chainId: 137,
      signatureType: 1,
      funder: wallet.funder,
      apiKey: creds.apiKey || creds.key,
      secret: creds.secret,
      passphrase: creds.passphrase
    };
    
    fs.writeFileSync("./config.json", JSON.stringify(config, null, 2));
    console.log("\n✅ Saved to config.json");
    
    // Test the connection
    console.log("\nTesting API connection...");
    const testClient = new ClobClient(host, 137, signer, creds, 1, wallet.funder);
    const markets = await testClient.getMarkets();
    console.log("✅ Connection works! Found", markets.length, "markets");
    
  } catch (err) {
    console.error("\n❌ Error:", err.message);
    if (err.response?.data) console.error("Response:", err.response.data);
  }
}

setupApi();
