# OpenClaw Mesh Infrastructure Audit Report
**Date:** 2026-03-03
**Auditor:** System Architect Agent (cron: daily-3am-arch-audit)
**Scope:** Full mesh of 4 nodes (Nexus 10.0.0.1, Clawd 10.0.0.2, Brutus 10.0.0.3, Plutos 10.0.0.4)

---

## Executive Summary

**Overall Health Score:** 2/10
**Trend:** ↓ Decreased (from 6/10 on 2026-02-27)

The mesh infrastructure is in **critical condition**. Two of four nodes (Nexus and Brutus) are completely offline and unreachable, representing a total loss of the security hub and the coding inference capacity. The remaining nodes (Clawd, Plutos) are operational but continue to operate with known security exposures. The sentinel monitoring system generated repeated CRITICAL alerts for these outages between 01:45–02:05 UTC.

**Priority Issues:**
1. **Massive node outage** – Nexus and Brutus have been unreachable since at least 01:45 UTC; root cause unknown (likely power, network, or WireGuard failure).
2. **Secret exposure** – `openclaw.json` and systemd unit file contain gateway token and API keys with 0664/0644 permissions (world-readable).
3. **Telegram bot duplication** – OpenClaw gateway running on all nodes with Telegram enabled; receives duplicate updates.
4. **Ollama API exposure** – All inference nodes bind to `0.0.0.0:11434` without firewall or authentication.
5. **Configuration drift** – Missing Ollama models (qwen-coder on Clawd, qwen14b on Plutos), incorrect `config.yaml` host entries, version mismatch (Clawd on 0.15.5 vs others 0.16.1).

---

## Mesh Health

### Connectivity Summary (snapshot 2026-03-03T02:04:56Z)

| Target    | Status | Ping | Ollama API | Latency (ms) | Notes |
|-----------|--------|------|------------|--------------|-------|
| 10.0.0.1  | **DOWN** | –    | –          | –            | Nexus (security hub) unreachable |
| 10.0.0.2  | UP     | ✓    | ✓ (up)     | 0.04         | Clawd (gateway) – healthy |
| 10.0.0.3  | **DOWN** | –    | ✗ (down)   | –            | Brutus (coding) unreachable |
| 10.0.0.4  | UP     | ✓    | ✓ (up)     | 12.7         | Plutos (heavy inference) – healthy |

- **Critical finding**: 50% node loss (Nexus & Brutus) cripples mesh redundancy and splits capabilities.
- **WireGuard**: Interface `wg0` is UP on Clawd and Plutos (confirmed), but peer status cannot be verified without `sudo wg show`. The unreachable nodes likely have WireGuard stopped or underlying network failure.
- **Latency**: On reachable nodes, latency is normal for WireGuard (sub‑30ms).
- **Sentinel alerts**: Continuous CRITICAL alerts generated since at least 01:45 UTC:
  ```
  CRITICAL-MESH-2026-03-03T01:45:12Z-nexus.md
  CRITICAL-MESH-2026-03-03T01:45:12Z-brutus.md
  CRITICAL-OLLAMA-2026-03-03T01:45:12Z-brutus.md
  ```

### Immediate Recovery Actions

1. **Check physical/virtual state** of Nexus and Brutus (power, VM status, console).
2. **If powered on**, check WireGuard status:
   ```bash
   sudo wg show
   sudo systemctl status wg-quick@wg0
   ```
3. **Restart WireGuard** on affected nodes if tunnel down:
   ```bash
   sudo systemctl restart wg-quick@wg0
   ```
4. **Verify network routes** and firewall (ensure not blocking WG UDP port 51820).
5. **Check system logs** for crashes:
   ```bash
   sudo journalctl -u wg-quick@wg0 -b
   sudo dmesg | grep wireguard
   ```

---

## Services

### SSH Daemon

| Node   | Port | Bind Address | Status    | Auth Method |
|--------|------|--------------|-----------|-------------|
| Clawd  | 22   | 0.0.0.0      | active    | keys + pwd? |
| Brutus | 22   | 0.0.0.0      | unreachable | –           |
| Plutos | 22   | 0.0.0.0      | active    | keys + pwd? |
| Nexus  | 22   | 0.0.0.0      | unreachable | –           |

- All reachable nodes expose SSH on all interfaces. **Hardening required**: change to port `2222`, bind to mesh IP only, disable password auth.
- Unreachable nodes cannot be assessed.

### OpenClaw Gateway

| Node   | PID (sample) | Bind Address   | Mode    | Version     |
|--------|--------------|-----------------|---------|-------------|
| Clawd  | 1475912      | 127.0.0.1:18789 | local   | 2026.2.3-1  |
| Brutus | (down)       | –               | –       | –           |
| Plutos | 1031         | 127.0.0.1:18789 | local   | 2026.2.3-1  |
| Nexus  | (down)       | –               | –       | –           |

- **Critical**: Gateway token stored in cleartext in systemd unit file (`~/.config/systemd/user/openclaw-gateway.service`) with 0664 permissions.
- **Critical**: Telegram plugin enabled on all reachable nodes → duplicate polling.
- **Token**: `63a3931e00c32d904c464e7b1f99a64ccf5ecbec1d2cddea` visible to any local user.
- **Configuration**: `gateway.mode=local` and `bind=loopback` is acceptable only if agents are local to each node. However, nodes ARE running agents (`openclaw-node` on Plutos), so this is correct per node. But Telegram duplication remains.

### Ollama API

| Node   | Status  | Models Available (as of 2026-02-27) | Version  | Bind Address |
|--------|---------|--------------------------------------|----------|--------------|
| Clawd  | up      | `mistral:7b-instruct-v0.3-q4_K_M`  | 0.15.5   | 0.0.0.0:11434|
| Brutus | down    | (expected: `qwen2.5-coder:3b`)      | 0.16.1?  | 0.0.0.0:11434|
| Plutos | up      | `llama3.1:8b-instruct-q4_K_M`      | 0.16.1   | 0.0.0.0:11434|
| Nexus  | –       | –                                    | –        | –            |

- **Missing models**: Clawd lacks `qwen2.5-coder:3b`; Plutos lacks `qwen14b` (as per design). This forces fallback to external providers, potentially incurring costs.
- **Version drift**: Clawd on 0.15.5 vs others on 0.16.1 – upgrade to match.
- **No authentication**: Ollama API entirely unauthenticated; reachable from any network interface.
- **Network exposure**: Bound to `0.0.0.0`; combined with lack of firewall, this risks unauthorized use if nodes have public IPs.

---

## Security

### File Permissions – Sensitive Credentials

| File                                          | Perms   | Risk  | Contains |
|-----------------------------------------------|---------|-------|----------|
| `~/.openclaw/openclaw.json`                   | 0664    | HIGH  | Telegram token, NVIDIA/Brave API keys, gateway token |
| `~/.config/systemd/user/openclaw-gateway.service` | 0664 | HIGH  | `OPENCLAW_GATEWAY_TOKEN` in plaintext |
| `~/.openclaw/credentials/*.json`              | (unknown; check) | MED | OAuth tokens |

**Remediation:**

```bash
# 1. Restrict openclaw.json
chmod 600 ~/.openclaw/openclaw.json

# 2. Move gateway token to dedicated env file
mkdir -p ~/.openclaw/conf
cat > ~/.openclaw/conf/gateway.env <<'EOF'
OPENCLAW_GATEWAY_TOKEN=63a3931e00c32d904c464e7b1f99a64ccf5ecbec1d2cddea
EOF
chmod 600 ~/.openclaw/conf/gateway.env

# 3. Remove token from unit file and add EnvironmentFile
sed -i '/Environment=OPENCLAW_GATEWAY_TOKEN/d' ~/.config/systemd/user/openclaw-gateway.service
echo 'EnvironmentFile=%h/.openclaw/conf/gateway.env' >> ~/.config/systemd/user/openclaw-gateway.service
chmod 600 ~/.config/systemd/user/openclaw-gateway.service

# 4. Reload and restart
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway
```

Apply identical steps on **Plutos** (and any other node with gateway). For Brutus and Nexus, bring online first then apply.

### Firewall – Missing Entirely

- No `ufw` or `nftables` observed on reachable nodes. Services (`ssh:22`, `ollama:11434`) are exposed to all interfaces.
- If nodes have public IPs, they are **directly reachable** by the internet.

**Remediation – Deploy host‑based firewall (nftables example):**

```bash
# Create basic filter table
sudo nft add table inet filter
sudo nft 'add chain inet filter input { type filter hook input priority 0; policy drop; }'
sudo nft add rule inet filter input ct state established,related accept
sudo nft add rule inet filter input ip saddr 10.0.0.0/24 tcp dport {22,11434} accept
sudo nft add rule inet filter input lo accept
# Optional: allow ICMP (ping) from mesh only
sudo nft add rule inet filter input ip saddr 10.0.0.0/24 icmp type echo-request accept
# Save and persist
sudo nft list ruleset > /etc/nftables.conf
sudo systemctl enable --now nftables
```

Alternatively, use `ufw`:

```bash
sudo apt-get install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 10.0.0.0/24 to any port 22
sudo ufw allow from 10.0.0.0/24 to any port 11434
sudo ufw --force enable
```

Apply on **Clawd** and **Plutos** immediately. Once Brutus and Nexus are back online, apply there as well.

### Ollama Network Exposure

Even with firewall, Ollama should bind to localhost if only local agents use it. However, agents may be on same host? In current design, each node runs its own agents and its own Ollama, and agents talk to local Ollama via `127.0.0.1`. But `openclaw.json` on Clawd/Plutos references remote Ollama URLs (`10.0.0.x`). That is likely outdated configuration used for remote calls? Actually the providers define:
- `ollama` (Brutus) – baseUrl `10.0.0.3:11434`
- `ollama-plutos` – baseUrl `10.0.0.4:11434`
- `ollama-clawd` – baseUrl `10.0.0.2:11434`

So on Clawd, there is a provider pointing to Brutus (down). That's not causing the exposure but it's unnecessary. The local provider should be used via localhost. Let's check: on Clawd, `ollama-clawd` uses `10.0.0.2`. That's fine. On Plutos, `ollama-plutos` uses `10.0.0.4`. That's fine. On the main openclaw process (gateway on Clawd?), it may use these providers. The exposure is that Ollama on each node is bound to 0.0.0.0, so even if the gateway uses localhost, the Ollama port is open to the world. That's the issue.

**Remediation 1 – Bind Ollama to localhost**:

```bash
# On each inference node (Clawd, Brutus when up, Plutos):
sudo mkdir -p /etc/systemd/system/ollama.service.d
cat | sudo tee /etc/systemd/system/ollama.service.d/override.conf <<'EOF'
[Service]
Environment="OLLAMA_HOST=127.0.0.1"
EOF
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

**Remediation 2 – Adjust openclaw.json providers** (optional if you bind to localhost):

```bash
# Change baseUrl for each provider to localhost on the respective node.
# Example for Clawd (replace "http://10.0.0.2:11434" with "http://127.0.0.1:11434").
# Similarly for Plutos. Remove or comment out provider for Brutus if node is dead.
```

**Remediation 3 – Ensure Ollama version is consistent**:

Clawd is on 0.15.5; others on 0.16.1. Upgrade Clawd:

```bash
# On Clawd
sudo apt-get update
sudo apt-get install -y ollama   # should pull latest; or specific version
# Verify: ollama --version
```

---

## Configuration Drift

### Desired vs Observed

| Component                     | Desired State                                           | Observed (2026-03-03)                               | Severity |
|-------------------------------|---------------------------------------------------------|-----------------------------------------------------|----------|
| **WireGuard (all nodes)**     | wg0 up, peers connected, `/etc/wireguard/wg0.conf` 0600 | Cannot assess (nodes down); Clawd wg0 up but peers unknown | 🔴 Critical (unverified) |
| **SSH**                       | Port `2222`, bind to mesh IP (`10.0.0.x`)              | Port `22`, bind `0.0.0.0` on reachable nodes       | 🔴 Critical |
| **OpenClaw config perms**     | `600` owner‑only                                        | `664` for `openclaw.json` and unit file            | 🔴 Critical |
| **OpenClaw Telegram**         | Enabled **only** on primary gateway (Clawd)            | Enabled on all nodes (duplicate polling)          | 🔴 Critical |
| **Ollama models – Clawd**     | `mistral` **and** `qwen2.5-coder:3b`                   | Only `mistral` present                             | 🔴 Critical |
| **Ollama models – Plutos**    | `llama3.1:8b` **and** `qwen14b`                        | Only `llama3.1:8b` present                          | 🔴 Critical |
| **Ollama version**            | Consistent (latest)                                     | Clawd 0.15.5 vs Plutos 0.16.1                      | 🟡 Medium |
| **Ollama config.yaml**        | Absent or `OLLAMA_HOST=127.0.0.0.1`                     | Clawd & Plutos have `host: 10.0.0.4:11434` (incorrect) | 🔴 Critical |
| **Gateway bind**              | Mesh IP if remote agents; else loopback ok              | Loopback only – acceptable for local agents       | 🟢 OK |

### Configuration File Notes

- **Ollama config.yaml** (Clawd & Plutos): Contains `host: 10.0.0.4:11434`. This is either a relic or misconfiguration; should be removed or set to `0.0.0.0` or `127.0.0.1` via systemd override.
- **OpenClaw providers**: The config references Brutus for `qwen-coder`. Since Brutus is down, any agent requesting that model will fail or fall back. Either remove the provider or bring Brutus back online.

---

## Resource Utilization

Remaining nodes show excellent headroom; offline nodes cannot be assessed.

| Node   | CPU Cores | Memory Total | Used | Load Avg (1m) | Disk Total | Used | FS Use% |
|--------|-----------|--------------|------|---------------|------------|------|---------|
| Clawd  | 8         | 15 GiB       | 1.6 GiB | 0.03        | 464 GiB    | 31 GiB | 7%      |
| Plutos | 8         | 31 GiB       | 2.1 GiB | 0.00        | 464 GiB    | 32 GiB | 7%      |
| Brutus | 6 (down)  | 7.7 GiB      | –    | –             | 232 GiB    | 12 GiB (expected) | 5% (expected) |
| Nexus  | 1 (down)  | 941 MiB      | –    | –             | 9.1 GiB    | 686 MiB (expected) | 8% (expected) |

- No saturation risks on operational nodes.
- CPU idle >98%; memory free >13 GiB on Clawd, >29 GiB on Plutos.

---

## Cost & High Availability

### Single Points of Failure (SPOF)

1. **Telegram/Channel Integration** – Only one gateway should be active for external channels. Currently **multiple active** (not a SPOF but causes duplication). If the designated primary (Clawd) fails, no other gateway will be active (assuming Telegram plugin disabled elsewhere) → loss of channel connectivity.
2. **Node loss** – We have lost 50% of mesh nodes. The remaining nodes are now a single point of failure for their respective roles (gateway, heavy inference). Any further loss would cripple remaining capabilities.
3. **External API keys** – Hard‑coded in `openclaw.json` (NVIDIA, Brave). Compromise of any node leaks them. No vault‑based secret distribution.

### Cost Optimization

- **Free tier**: Default agent model `openrouter/stepfun/step-3.5-flash:free` – good.
- **Local inference**: Ollama models are self‑hosted and free. However, missing local models force fallback to external paid providers (e.g., NVIDIA API for Kimi). This may incur costs if usage spikes.
- **Runaway API keys**: NVIDIA API key and Brave API key present. Monitor usage via provider dashboards; set limits.

---

## Backup + Recovery

- **Baseline snapshots** exist: `memory/baseline_permissions.json`, `memory/network_baseline.json`, `memory/known_secrets.json`. Good.
- **Daily backup script** at `maintenance/daily_backup.sh` (cron @ 02:00). Verified last run 2026-03-03T02:00:01Z; commit included `memory/2026-03-03-research.md`. No errors observed in `logs/backup.log`.
- **Configuration coverage**: Backup includes workspace files but **excludes critical system configs** (`/etc/wireguard`, `/etc/ollama`, systemd units). Recommend extending `daily_backup.sh`:

```bash
# Add to maintenance/daily_backup.sh
CONFIG_BACKUP_DIR="backup/system-configs/$(date +%Y-%m-%d)"
mkdir -p "$CONFIG_BACKUP_DIR"
sudo tar czf "$CONFIG_BACKUP_DIR/wireguard.tgz" /etc/wireguard 2>/dev/null || true
sudo tar czf "$CONFIG_BACKUP_DIR/ollama.tgz" /etc/ollama 2>/dev/null || true
sudo tar czf "$CONFIG_BACKUP_DIR/systemd-ollama.tgz" /etc/systemd/system/ollama.service* 2>/dev/null || true
sudo tar czf "$CONFIG_BACKUP_DIR/openclaw-gateway.tgz" /home/boss/.config/systemd/user/openclaw-gateway.service 2>/dev/null || true
# Then git add/commit these backups as well.
```

---

## Top 5 Recommendations (Actionable)

### 1. Restore Mesh Nodes (URGENT)
**Problem**: Nexus and Brutus offline since ~01:45 UTC.  
**Fix**: Bring nodes online and re‑establish WireGuard connectivity.

```bash
# On each down node (if reachable via console/IPMI/serial):
# a) Check system is up
ping -c 3 10.0.0.1  # or 10.0.0.3

# b) Verify WireGuard interface
sudo wg show
sudo systemctl status wg-quick@wg0

# If wg0 down, restart:
sudo systemctl restart wg-quick@wg0

# c) Check peer handshakes
sudo wg show | grep -A5 "peer"

# d) If WireGuard config missing, restore from backup:
sudo tar xzf /path/to/backup/system-configs/YYYY-MM-DD/wireguard.tgz -C /

# e) Ensure service enabled:
sudo systemctl enable --now wg-quick@wg0

# f) Verify ping from Clawd:
ping -c 4 10.0.0.1
```

If nodes are powered off, start them via hypervisor/console.

### 2. Secure OpenClaw Secrets
**Problem**: Gateway token and API keys world‑readable in `openclaw.json` and systemd unit.  
**Fix**:

```bash
# On each node running the gateway (Clawd, Plutos, and eventually Brutus/Nexus if desired):
chmod 600 ~/.openclaw/openclaw.json
mkdir -p ~/.openclaw/conf
cat > ~/.openclaw/conf/gateway.env <<'EOF'
OPENCLAW_GATEWAY_TOKEN=63a3931e00c32d904c464e7b1f99a64ccf5ecbec1d2cddea
EOF
chmod 600 ~/.openclaw/conf/gateway.env
sed -i '/Environment=OPENCLAW_GATEWAY_TOKEN/d' ~/.config/systemd/user/openclaw-gateway.service
echo 'EnvironmentFile=%h/.openclaw/conf/gateway.env' >> ~/.config/systemd/user/openclaw-gateway.service
chmod 600 ~/.config/systemd/user/openclaw-gateway.service
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway
```

### 3. Disable Telegram Duplication
**Problem**: Telegram plugin enabled on all gateways → duplicate updates.  
**Fix** (disable on all non‑primary nodes):

```bash
# On Brutus, Plutos, and Nexus (once up):
sed -i 's/"enabled": true/"enabled": false/' ~/.openclaw/openclaw.json
systemctl --user restart openclaw-gateway
# Optionally stop/disable service on those nodes:
systemctl --user disable --now openclaw-gateway
```

Primary (Clawd) keeps Telegram enabled.

### 4. Harden Ollama Network & Firewall
**Problem**: Ollama API exposed to all interfaces; no host firewall.  
**Fix** – bind to localhost **and** deploy firewall:

```bash
# Bind Ollama to localhost on each inference node (Clawd, Brutus, Plutos):
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/override.conf <<'EOF'
[Service]
Environment="OLLAMA_HOST=127.0.0.1"
EOF
sudo systemctl daemon-reload
sudo systemctl restart ollama

# Deploy nftables firewall (run on Clawd and Plutos now; on others when up):
sudo nft add table inet filter
sudo nft 'add chain inet filter input { type filter hook input priority 0; policy drop; }'
sudo nft add rule inet filter input ct state established,related accept
sudo nft add rule inet filter input ip saddr 10.0.0.0/24 tcp dport {22,11434} accept
sudo nft add rule inet filter input lo accept
sudo nft list ruleset > /etc/nftables.conf
sudo systemctl enable --now nftables
```

### 5. Resolve Model Gaps & Version Consistency
**Problem**: Missing local models cause fallback to paid APIs; version mismatch.  
**Fix**:

```bash
# Pull missing models:
# On Clawd (when Brutus down, you may want qwen-coder locally):
ssh clawd 'ollama pull qwen2.5-coder:3b'

# On Plutos (pull qwen14b, e.g., qwen2.5:14b):
ssh plutos 'ollama pull qwen2.5:14b'

# Upgrade Clawd Ollama to match others:
ssh clawd 'sudo apt-get update && sudo apt-get install -y ollama'

# Verify all nodes:
for ip in 10.0.0.2 10.0.0.3 10.0.0.4; do
  echo "=== $ip ==="
  ssh "$ip" 'ollama --version' 2>/dev/null || echo "unreachable"
  ssh "$ip" 'curl -s http://127.0.0.1:11434/api/tags | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin), indent=2))"' 2>/dev/null || echo "API unreachable"
done
```

Remove the dead provider (`ollama` pointing to Brutus) from `openclaw.json` if Brutus remains offline long‑term.

---

## Additional Notes

- **Sentinel monitoring** (`sentinel_mesh_check.sh`) is functioning and generated timely alerts. Consider enhancing it to include WireGuard peer status and service checks via `systemctl is-active` where possible.
- **Log history**: Mesh health history is sparse; consider scheduling hourly runs of `sentinel_mesh_check.sh` and retaining logs for trend analysis.
- **Baseline verification**: Permission and network baselines exist in `memory/` but have not been updated since Feb 21. Re‑capture baselines after remediation.
- **OpenClaw config**: `openclaw.json` also contains Google Places API keys; ensure those are not exposed. Permissions should be 600.
- **Recovery priority**: Bring Brutus and Nexus online first (they host critical models and security functions). Then apply security hardening across all nodes.

---

*Report generated by System Architect Agent on 2026-03-03T02:07:00Z. Recommendations assume passwordless sudo for user `boss` on all nodes as per policy.*
