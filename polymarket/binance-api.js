// Binance API Integration Module
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');

class BinanceAPI {
  constructor(configPath = './binance-config.json') {
    this.baseURL = 'api.binance.com';
    this.config = null;
    
    if (fs.existsSync(configPath)) {
      this.config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    } else {
      throw new Error('Binance config not found. Run: node setup-binance.js');
    }
  }
  
  // Sign request with HMAC SHA256
  sign(queryString) {
    return crypto
      .createHmac('sha256', this.config.secretKey)
      .update(queryString)
      .digest('hex');
  }
  
  // Make authenticated request
  async request(endpoint, params = {}, method = 'GET') {
    const timestamp = Date.now();
    let queryString = `timestamp=${timestamp}`;
    
    // Add params
    Object.keys(params).forEach(key => {
      queryString += `&${key}=${params[key]}`;
    });
    
    const signature = this.sign(queryString);
    const path = `${endpoint}?${queryString}&signature=${signature}`;
    
    return new Promise((resolve, reject) => {
      const options = {
        hostname: this.baseURL,
        path: path,
        method: method,
        headers: {
          'X-MBX-APIKEY': this.config.apiKey,
          'Content-Type': 'application/json'
        }
      };
      
      const req = https.request(options, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          try {
            const parsed = JSON.parse(data);
            if (parsed.code) reject(new Error(parsed.msg));
            else resolve(parsed);
          } catch (e) {
            resolve(data);
          }
        });
      });
      
      req.on('error', reject);
      req.end();
    });
  }
  
  // Public request (no auth needed)
  async publicRequest(endpoint, params = {}) {
    const queryString = Object.keys(params)
      .map(key => `${key}=${params[key]}`)
      .join('&');
    
    const path = queryString ? `${endpoint}?${queryString}` : endpoint;
    
    return new Promise((resolve, reject) => {
      const options = {
        hostname: this.baseURL,
        path: path,
        method: 'GET'
      };
      
      const req = https.request(options, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          try {
            resolve(JSON.parse(data));
          } catch (e) {
            resolve(data);
          }
        });
      });
      
      req.on('error', reject);
      req.end();
    });
  }
  
  // ===== PUBLIC ENDPOINTS =====
  
  // Get current price
  async getPrice(symbol) {
    const data = await this.publicRequest('/api/v3/ticker/price', { symbol });
    return parseFloat(data.price);
  }
  
  // Get 24hr stats
  async get24hrStats(symbol) {
    return await this.publicRequest('/api/v3/ticker/24hr', { symbol });
  }
  
  // Get order book
  async getOrderBook(symbol, limit = 10) {
    return await this.publicRequest('/api/v3/depth', { symbol, limit });
  }
  
  // Get recent trades
  async getRecentTrades(symbol, limit = 50) {
    return await this.publicRequest('/api/v3/trades', { symbol, limit });
  }
  
  // Get klines/candles
  async getKlines(symbol, interval = '15m', limit = 100) {
    // intervals: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
    const data = await this.publicRequest('/api/v3/klines', { 
      symbol, 
      interval, 
      limit 
    });
    
    return data.map(c => ({
      timestamp: c[0],
      open: parseFloat(c[1]),
      high: parseFloat(c[2]),
      low: parseFloat(c[3]),
      close: parseFloat(c[4]),
      volume: parseFloat(c[5]),
      closeTime: c[6],
      quoteVolume: parseFloat(c[7]),
      trades: c[8]
    }));
  }
  
  // ===== PRIVATE ENDPOINTS (require API key) =====
  
  // Get account info
  async getAccount() {
    return await this.request('/api/v3/account');
  }
  
  // Get balances
  async getBalances() {
    const account = await this.getAccount();
    return account.balances.filter(b => 
      parseFloat(b.free) > 0 || parseFloat(b.locked) > 0
    );
  }
  
  // Get open orders
  async getOpenOrders(symbol) {
    const params = symbol ? { symbol } : {};
    return await this.request('/api/v3/openOrders', params);
  }
  
  // Place market order
  async placeMarketOrder(symbol, side, quoteOrderQty) {
    // side: BUY or SELL
    // quoteOrderQty: amount in quote asset (e.g., USDT)
    return await this.request('/api/v3/order', {
      symbol,
      side,
      type: 'MARKET',
      quoteOrderQty
    }, 'POST');
  }
  
  // Place limit order
  async placeLimitOrder(symbol, side, quantity, price) {
    return await this.request('/api/v3/order', {
      symbol,
      side,
      type: 'LIMIT',
      quantity,
      price,
      timeInForce: 'GTC'
    }, 'POST');
  }
  
  // Cancel order
  async cancelOrder(symbol, orderId) {
    return await this.request('/api/v3/order', {
      symbol,
      orderId
    }, 'DELETE');
  }
  
  // Get order status
  async getOrder(symbol, orderId) {
    return await this.request('/api/v3/order', { symbol, orderId });
  }
  
  // Get trade history
  async getMyTrades(symbol, limit = 50) {
    return await this.request('/api/v3/myTrades', { symbol, limit });
  }
}

module.exports = BinanceAPI;
