// Thales Protocol binary options data
const https = require('https');

const THALES_SUBGRAPH = 'api.thegraph.com/subgraphs/name/thalesmarkets/optimism-main';

async function queryThales(query) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({ query });
    
    const options = {
      hostname: 'api.thegraph.com',
      path: '/subgraphs/name/thalesmarkets/optimism-main',
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

async function getThalesMarkets() {
  console.log("🔍 Fetching Thales binary options markets...\n");
  
  const query = `
    {
      markets(first: 50, orderBy: timestamp, orderDirection: desc) {
        id
        timestamp
        marketType
        asset
        strikePrice
        maturityDate
        expiryDate
        isOpen
        isResolved
        result
        pool
      }
    }
  `;
  
  try {
    const data = await queryThales(query);
    const markets = data.data?.markets || [];
    
    console.log(`✅ Found ${markets.length} markets`);
    
    markets.forEach((m, i) => {
      console.log(`${i + 1}. ${m.asset} @ $${parseFloat(m.strikePrice).toFixed(2)}`);
      console.log(`   Type: ${m.marketType}`);
      console.log(`   Matures: ${new Date(parseInt(m.maturityDate) * 1000).toISOString()}`);
      console.log(`   Open: ${m.isOpen} | Resolved: ${m.isResolved}`);
      console.log();
    });
    
    return markets;
  } catch (err) {
    console.error('❌ Thales error:', err.message);
  }
}

getThalesMarkets();
