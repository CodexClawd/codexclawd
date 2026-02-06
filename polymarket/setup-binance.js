const fs = require('fs');
const readline = require('readline');
const crypto = require('crypto');

const CONFIG_FILE = './binance-config.json';
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

console.log("🔐 Binance API Setup\n");
console.log("Get your API keys from: https://www.binance.com/en/my/settings/api-management\n");

function question(prompt) {
  return new Promise(resolve => rl.question(prompt, resolve));
}

async function setup() {
  try {
    const apiKey = await question("Enter Binance API Key: ");
    const secretKey = await question("Enter Binance Secret Key: ");
    
    console.log("\n⚠️  Security Settings:");
    console.log("1. Enable IP whitelist (recommended)");
    console.log("2. DISABLE withdrawal permissions");
    console.log("3. Use 'Enable Spot & Margin Trading' only if needed\n");
    
    const permissions = await question("What permissions does this key have? (read-only/trading): ");
    
    const config = {
      apiKey: apiKey.trim(),
      secretKey: secretKey.trim(),
      permissions: permissions.toLowerCase().includes('trade') ? 'trading' : 'read-only',
      createdAt: new Date().toISOString(),
      testnet: false
    };
    
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2));
    
    // Add to .gitignore if not already there
    const gitignorePath = '../.gitignore';
    if (fs.existsSync(gitignorePath)) {
      const gitignore = fs.readFileSync(gitignorePath, 'utf8');
      if (!gitignore.includes('binance-config.json')) {
        fs.appendFileSync(gitignorePath, '\n# Binance credentials\nbinance-config.json\n');
        console.log("✅ Added binance-config.json to .gitignore");
      }
    }
    
    console.log("\n✅ Binance API configured!");
    console.log(`   Permissions: ${config.permissions}`);
    console.log("   Config saved to: binance-config.json");
    console.log("\n🔒 This file is gitignored and won't be committed.");
    
    // Test the connection
    console.log("\n🧪 Testing connection...");
    await testConnection(config);
    
  } catch (err) {
    console.error("❌ Error:", err.message);
  } finally {
    rl.close();
  }
}

async function testConnection(config) {
  const https = require('https');
  
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.binance.com',
      path: '/api/v3/account?timestamp=' + Date.now(),
      method: 'GET',
      headers: {
        'X-MBX-APIKEY': config.apiKey
      }
    };
    
    // Sign the request
    const queryString = 'timestamp=' + Date.now();
    const signature = crypto
      .createHmac('sha256', config.secretKey)
      .update(queryString)
      .digest('hex');
    
    options.path = `/api/v3/account?${queryString}&signature=${signature}`;
    
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          if (result.balances) {
            console.log("✅ Connection successful!");
            console.log(`   Account has ${result.balances.length} assets`);
            const nonZero = result.balances.filter(b => parseFloat(b.free) > 0 || parseFloat(b.locked) > 0);
            console.log(`   ${nonZero.length} assets with balance`);
          } else if (result.code) {
            console.log("⚠️  API Error:", result.msg);
          }
          resolve();
        } catch (e) {
          console.log("⚠️  Couldn't parse response:", data.substring(0, 100));
          resolve();
        }
      });
    });
    
    req.on('error', (err) => {
      console.log("⚠️  Connection test failed:", err.message);
      resolve();
    });
    
    req.end();
  });
}

setup();
