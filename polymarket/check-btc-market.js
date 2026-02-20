const { ClobClient } = require('@polymarket/clob-client');
const { Wallet } = require('@ethersproject/wallet');
const fs = require('fs');

const config = JSON.parse(fs.readFileSync('./config.json', 'utf8'));
const wallet = JSON.parse(fs.readFileSync('./wallet.json', 'utf8'));

async function checkMarket() {
  try {
    const signer = new Wallet(wallet.privateKey);
    const creds = { apiKey: config.apiKey, secret: config.secret, passphrase: config.passphrase };
    const client = new ClobClient(config.host, config.chainId, signer, creds, config.signatureType, config.funder);

    // Try to get all markets (maybe it includes 2026 markets now)
    console.log('Fetching all markets...');
    const markets = await client.getMarkets();
    console.log(`Total markets: ${markets?.length || 0}`);

    // Look for the BTC market by title or ID if possible
    let targetMarket = null;
    if (markets && markets.length > 0) {
      // Search for BTC related market
      for (const m of markets) {
        if (m.title && m.title.toLowerCase().includes('bitcoin')) {
          console.log(`Found BTC market: ${m.title} (${m.market_id})`);
          console.log('Tokens:', JSON.stringify(m.tokens, null, 2));
        }
      }
    }

    // If we know the token ID directly we could fetch orderbook
    // The market URL has event ID 1771506900. Need to map to token ID.
    // Typically token ID = marketId + '_YES' and marketId + '_NO' but not sure.
    // Try common pattern:
    const possibleTokenIdYes = '1771506900-Yes'; // or '1771506900-YES'
    const possibleTokenIdNo = '1771506900-No';

    // Try fetching orderbook for both
    for (const tokenId of [possibleTokenIdYes, possibleTokenIdNo, '1771506900']) {
      try {
        console.log(`\nTrying orderbook for token: ${tokenId}`);
        const orderbook = await client.getOrderBook(tokenId);
        console.log('Orderbook:', JSON.stringify(orderbook, null, 2));
      } catch (e) {
        // ignore
      }
    }

  } catch (err) {
    console.error('Error:', err.message);
    console.error(err);
  }
}

checkMarket();