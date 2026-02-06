// Use Gamma API to find market info - fixed version
const https = require('https');
const fs = require('fs');

const GAMMA_API = 'gamma-api.polymarket.com';

function gammaRequest(path) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: GAMMA_API,
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

async function searchMarkets() {
  try {
    console.log("🔍 Searching Gamma API for 2026 markets...\n");
    
    // Try to get events ending in 2026
    const results = await gammaRequest('/events?end_date_gte=2026-01-01&limit=50');
    
    if (Array.isArray(results) && results.length > 0) {
      console.log(`Found ${results.length} events\n`);
      
      // Filter for Iran-related
      const iranEvents = results.filter(e => {
        const text = (e.title + ' ' + (e.description || '')).toLowerCase();
        return text.includes('iran') || text.includes('strikes');
      });
      
      if (iranEvents.length > 0) {
        console.log(`\n✅ Found ${iranEvents.length} Iran-related events:\n`);
        printEvents(iranEvents);
      } else {
        console.log("\n❌ No Iran events found in 2026.");
        console.log("Showing first 5 events from 2026:\n");
        printEvents(results.slice(0, 5));
      }
    } else {
      console.log("No 2026 events found. API might not index future markets yet.");
      console.log("\nResponse sample:", JSON.stringify(results, null, 2).substring(0, 500));
    }
    
  } catch (err) {
    console.error("❌ Error:", err.message);
  }
}

function printEvents(events) {
  events.forEach((e, i) => {
    console.log(`${i + 1}. ${e.title || e.question || 'Untitled'}`);
    console.log(`   Slug: ${e.slug || 'N/A'}`);
    console.log(`   Condition ID: ${e.conditionId || 'N/A'}`);
    
    if (e.markets && e.markets.length > 0) {
      e.markets.forEach((m, j) => {
        console.log(`   Market ${j + 1}: ${m.question || m.title}`);
        if (m.tokens) {
          m.tokens.forEach(t => {
            console.log(`      Token [${t.outcome}]: ${t.token_id}`);
          });
        }
      });
    }
    console.log();
  });
  
  fs.writeFileSync('./markets-found.json', JSON.stringify(events, null, 2));
  console.log("✅ Saved to markets-found.json");
}

searchMarkets();
