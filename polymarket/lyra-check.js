// Lyra Protocol on Arbitrum
const https = require('https');

const LYRA_SUBGRAPH = 'api.thegraph.com/subgraphs/name/lyra-finance/lyra-arbitrum-mainnet';

async function queryLyra(query) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({ query });
    
    const options = {
      hostname: 'api.thegraph.com',
      path: '/subgraphs/name/lyra-finance/lyra-arbitrum-mainnet',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': data.length
      }
    };
    
    const req = https.request(options, (res) => {
      let response = '';
      res.on('data', chunk => response += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(response));
        } catch (e) {
          reject(e);
        }
      });
    });
    
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

async function getLyraOptions() {
  console.log("🔍 Fetching Lyra options markets...\n");
  
  const query = `
    {
      markets(first: 20) {
        id
        baseAsset {
          symbol
        }
        quoteAsset {
          symbol
        }
        strikePrice
        expiry
        isCall
        isSystemTrade
        isBaseCollateral
        longScaleFactor
        shortScaleFactor
      }
    }
  `;
  
  try {
    const data = await queryLyra(query);
    console.log('Response:', JSON.stringify(data, null, 2).substring(0, 500));
    
    const markets = data.data?.markets || [];
    console.log(`✅ Found ${markets.length} markets`);
    
    markets.forEach((m, i) => {
      const asset = m.baseAsset?.symbol || 'Unknown';
      const type = m.isCall ? 'CALL' : 'PUT';
      const strike = parseFloat(m.strikePrice).toFixed(2);
      const expiry = new Date(parseInt(m.expiry) * 1000).toISOString();
      
      console.log(`${i + 1}. ${asset} ${type} @ $${strike}`);
      console.log(`   Expiry: ${expiry}`);
      console.log();
    });
    
    return markets;
  } catch (err) {
    console.error('❌ Lyra error:', err.message);
  }
}

getLyraOptions();
