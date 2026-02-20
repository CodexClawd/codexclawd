# System Hardening & Fix Plan — 2026-02-19

## Current Issues (Prioritized)

1. **CRITICAL: Brutus packet loss** — 50% packet loss detected on 10.0.0.3 (Brutus) at 14:01 UTC. Mesh degraded.
2. **Polymarket 2026 markets unreachable via API** — CLOB API only returns historical (2021-2023). Manual tracking required for Feb 9/28 markets.
3. **Excessive monitoring chatter** — Hourly mesh checks and digests generate too many messages (user requested silence when healthy).
4. **Worldmonitor project** — Fresh clone, unknown status. Needs inventory and potential setup.

## Plan of Action

### Phase 1: Immediate Mesh Health (Next 30 min)

- [ ] Diagnose Brutus packet loss
  - Check WireGuard interface stats on all nodes (requires SSH to Brutus)
  - Verify MTU settings (common cause of packet loss)
  - Check for firewall/Drop/iptables interference
  - Look for network congestion or route issues
- [ ] Temporary mitigation if needed
  - Adjust MTU on wg0 interfaces (try 1420, 1400)
  - Enable `PersistentKeepalive` if missing
  - Restart WireGuard on Brutus if state corrupted
- [ ] Update mesh check cron to be silent-on-healthy (already done per user request)

### Phase 2: Polymarket Workaround (Next 2 hours)

- [ ] Build a web scraper for Polymarket market pages
  - Use Puppeteer/Playwright to fetch https://polymarket.com/event/btc-updown-15m-1771506900
  - Extract current price/odds from DOM
  - Save to JSON for Brutus to read
- [ ] Integrate scraper into manual-tracker.js flow
  - Option: `node check-polymarket-price.js <eventId>` → outputs current probability
  - Write price to `polymarket/current-price.json`
  - Alert if price crosses threshold
- [ ] Document: API limitation is permanent; scraping is the only automated option

### Phase 3: Worldmonitor Investigation (Next 1 hour)

- [ ] Read worldmonitor/README.md and package.json
- [ ] Identify what the app does (likely a monitoring dashboard)
- [ ] Determine if it's intended to run locally or be deployed
- [ ] Check for `.env` or config files
- [ ] Summarize findings to user for direction

### Phase 4: Long-Term Hardening (This Week)

- [ ] Add mesh latency/ packet-loss trend monitoring
  - Store historical ping results in memory/
  - Alert on degradation >20% increase
- [ ] Harden WireGuard config
  - Ensure `Endpoint` reachable via public IP (no DNS)
  - Set `PersistentKeepalive = 25` on all peers
  - Verify `AllowedIPs = 0.0.0.0/0` only if needed; restrict to 10.0.0.0/24
- [ ] Add automatic mesh repair
  - If node unreachable for 3 consecutive checks, attempt `wg-quick down/up`
  - If fails, send Telegram alert with recovery steps

## Notes on Execution

- I can run local commands on clawd (this host) freely.
- To fix Brutus, I need SSH access to 10.0.0.3 (likely allowed via mesh). I'll attempt direct commands; if sudo needed, I'll request user approval.
- All changes will be documented and committed to workspace for versioning.
- I'll use local Ollama (code:llama on brutus-8gb) for any heavy reasoning if needed, but I can handle this directly.

---

**Status:** Not started. Awaiting user confirmation or green light to proceed.