#!/usr/bin/env node
// Crypto toolkit - various useful commands
const BinanceAPI = require('./binance-api.js');

const args = process.argv.slice(2);
const command = args[0];

async function main() {
  try {
    const api = new BinanceAPI();
    
    switch(command) {
      case 'price':
        // node crypto-tools.js price BTCUSDT
        const symbol = args[1] || 'BTCUSDT';
        const price = await api.getPrice(symbol);
        console.log(`${symbol}: $${price.toLocaleString()}`);
        break;
        
      case 'balance':
        // node crypto-tools.js balance
        const balances = await api.getBalances();
        console.log("💰 Balances:\n");
        balances.forEach(b => {
          const total = parseFloat(b.free) + parseFloat(b.locked);
          if (total > 0) {
            console.log(`${b.asset}: ${total.toFixed(8)} (free: ${b.free}, locked: ${b.locked})`);
          }
        });
        break;
        
      case 'stats':
        // node crypto-tools.js stats BTCUSDT
        const statsSymbol = args[1] || 'BTCUSDT';
        const stats = await api.get24hrStats(statsSymbol);
        console.log(`📊 ${statsSymbol} 24h Stats:\n`);
        console.log(`Price: $${parseFloat(stats.lastPrice).toLocaleString()}`);
        console.log(`Change: ${stats.priceChangePercent}%`);
        console.log(`High: $${parseFloat(stats.highPrice).toLocaleString()}`);
        console.log(`Low: $${parseFloat(stats.lowPrice).toLocaleString()}`);
        console.log(`Volume: ${parseFloat(stats.volume).toLocaleString()} ${statsSymbol.replace('USDT', '')}`);
        console.log(`Quote Volume: $${parseFloat(stats.quoteVolume).toLocaleString()}`);
        break;
        
      case 'orders':
        // node crypto-tools.js orders BTCUSDT
        const orderSymbol = args[1];
        if (!orderSymbol) {
          console.log("Usage: node crypto-tools.js orders BTCUSDT");
          process.exit(1);
        }
        const orders = await api.getOpenOrders(orderSymbol);
        if (orders.length === 0) {
          console.log(`No open orders for ${orderSymbol}`);
        } else {
          console.log(`📋 Open orders for ${orderSymbol}:\n`);
          orders.forEach(o => {
            console.log(`${o.side} ${o.type} - ${o.origQty} @ $${o.price} (ID: ${o.orderId})`);
          });
        }
        break;
        
      case 'book':
        // node crypto-tools.js book BTCUSDT
        const bookSymbol = args[1] || 'BTCUSDT';
        const book = await api.getOrderBook(bookSymbol, 5);
        console.log(`📖 Order Book: ${bookSymbol}\n`);
        console.log("Asks (sell):");
        book.asks.slice(0, 5).reverse().forEach(a => {
          console.log(`  $${parseFloat(a[0]).toLocaleString()} - ${a[1]}`);
        });
        console.log("\nBids (buy):");
        book.bids.slice(0, 5).forEach(b => {
          console.log(`  $${parseFloat(b[0]).toLocaleString()} - ${b[1]}`);
        });
        break;
        
      case 'history':
        // node crypto-tools.js history BTCUSDT
        const histSymbol = args[1] || 'BTCUSDT';
        const trades = await api.getMyTrades(histSymbol, 10);
        console.log(`📜 Recent trades for ${histSymbol}:\n`);
        trades.forEach(t => {
          const time = new Date(t.time).toISOString();
          console.log(`${time}: ${t.isBuyer ? 'BUY' : 'SELL'} ${t.qty} @ $${t.price} (fee: ${t.commission} ${t.commissionAsset})`);
        });
        break;
        
      case 'buy':
        // node crypto-tools.js buy BTCUSDT 100
        const buySymbol = args[1];
        const buyAmount = args[2];
        if (!buySymbol || !buyAmount) {
          console.log("Usage: node crypto-tools.js buy BTCUSDT 100");
          process.exit(1);
        }
        console.log(`🛒 Buying ${buyAmount} USDT worth of ${buySymbol}...`);
        const buyResult = await api.placeMarketOrder(buySymbol, 'BUY', buyAmount);
        console.log("✅ Order filled!");
        console.log(`   Executed: ${buyResult.executedQty} @ avg $${buyResult.fills?.[0]?.price || 'N/A'}`);
        console.log(`   Order ID: ${buyResult.orderId}`);
        break;
        
      case 'sell':
        // node crypto-tools.js sell BTCUSDT 0.001
        const sellSymbol = args[1];
        const sellQty = args[2];
        if (!sellSymbol || !sellQty) {
          console.log("Usage: node crypto-tools.js sell BTCUSDT 0.001");
          process.exit(1);
        }
        console.log(`💵 Selling ${sellQty} ${sellSymbol.replace('USDT', '')}...`);
        // Note: SELL with quoteOrderQty sells that much of base asset
        const sellResult = await api.placeMarketOrder(sellSymbol, 'SELL', sellQty);
        console.log("✅ Order filled!");
        console.log(`   Executed: ${sellResult.executedQty}`);
        console.log(`   Order ID: ${sellResult.orderId}`);
        break;
        
      default:
        console.log("🚀 Crypto Tools\n");
        console.log("Commands:");
        console.log("  price [SYMBOL]     - Get current price (default: BTCUSDT)");
        console.log("  balance            - Show account balances");
        console.log("  stats [SYMBOL]     - Show 24h statistics");
        console.log("  orders SYMBOL      - Show open orders");
        console.log("  book [SYMBOL]      - Show order book");
        console.log("  history [SYMBOL]   - Show recent trades");
        console.log("  buy SYMBOL USDT    - Buy with USDT amount");
        console.log("  sell SYMBOL QTY    - Sell quantity of base asset");
        console.log("\nExamples:");
        console.log("  node crypto-tools.js price ETHUSDT");
        console.log("  node crypto-tools.js balance");
        console.log("  node crypto-tools.js buy BTCUSDT 50");
    }
    
  } catch (err) {
    console.error("❌ Error:", err.message);
    if (err.message.includes('config not found')) {
      console.log("\nRun: node setup-binance.js");
    }
  }
}

main();
