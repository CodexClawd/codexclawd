# OpenClaw Mesh Infrastructure Audit Report
**Date:** 2026-02-27
**Auditor:** System Architect Agent (cron: daily-3am-arch-audit)
**Scope:** Full mesh of 4 nodes (Nexus 10.0.0.1, Clawd 10.0.0.2, Brutus 10.0.0.3, Plutos 10.0.0.4)

---

## Executive Summary

**Overall Health Score:** 6/10
**Trend:** ↑ Improving (from 1/10 on 2026-02-25)

The mesh infrastructure is **functional but with significant security and configuration drift issues**. All nodes are reachable via WireGuard, core services (SSH, Ollama, OpenClaw gateway, fail2ban) are running, and resource utilization remains low. However, critical security exposures exist, including world-readable configuration files containing tokens and API keys, unauthenticated Ollama APIs exposed to all interfaces, multiple Telegram gateway instances risking duplicate polling, and inconsistent model deployment across inference nodes.

**Priority Issues:**
1. **Secret exposure** – `openclaw.json` and systemd unit file contain gateway token and API keys with overly permissive permissions (0644/0664).
2. **Telegram bot duplication** – OpenClaw gateway running on all nodes; only Clawd should be active for Telegram to avoid duplicate message handling.
3. **Ollama API exposure** – All inference nodes bind to `0.0.0.0:11434` without firewall restrictions; must restrict to mesh CIDR or localhost.
4. **Configuration drift** – Missing Ollama models on Clawd (qwen-coder) and Plutos (qwen14b); inconsistent `config.yaml` pointing to remote hosts; version mismatch (Clawd on older Ollama).
5. **Gateway token duplication** – Token stored in plaintext within unit file and `openclaw.json`; move to a dedicated environment file with `0600` permissions.

---

## Mesh Health

### Connectivity Summary

| Target    | Packets | Loss   | Avg Latency (ms) | Max Latency (ms) |
|-----------|---------|--------|------------------|------------------|
| 10.0.0.1  | 4/4     | 0%     | 13.9             | 14.0             |
| 10.0.0.2  | 4/4     | 0%     | 0.042            | 0.055            |
| 10.0.0.3  | 4/4     | 0%     | 26.5             | 26.8             |
| 10.0.0.4  | 4/4     | 0%     | 12.6             | 12.8             |

All nodes mutually reachable with **0% packet loss**. Latency within acceptable range for a WireGuard mesh (sub‑30ms). Brutus shows elevated latency (~26ms) – investigate possible routing or CPU bottleneck (CPU load is negligible, so likely network path).

### WireGuard Status

- **Clawd, Brutus, Plutos, Nexus** all have `wg0` interface in **UP** state.
- Mesh connectivity verified via ICMP; implies WireGuard tunnel is operational.
- Detailed peer statistics (`wg show`) require `sudo`; not captured. Recommend baseline capture of peer handshake stats.

### Network Interface Configuration

All nodes:
- wg0 MTU 1420 (optimal)
- No observed `wg0` errors in `ip link`.

---

## Services

### SSH Daemon

| Node   | Service | Port | Bind Address | Status    | Auth Method |
|--------|---------|------|--------------|-----------|-------------|
| Clawd  | sshd    | 22   | 0.0.0.0      | active    | key+pwd?    |
| Brutus | sshd    | 22   | 0.0.0.0      | active    | key+pwd?    |
| Plutos | sshd    | 22   | 0.0.0.0      | active    | key+pwd?    |
| Nexus  | sshd (OpenRC) | 22 | 0.0.0.0  | active    | key+pwd?    |

**Notes:**
- All nodes listen on `0.0.0.0:22` → exposed to internet if public IP present. Prefer non‑standard port (`2222`) and bind to mesh interface only.
- Nexus also accepts SSH on `2222`? Connection refused; port closed. OK.

### Ollama API

| Node   | Service | Port  | Bind Address | Models Available                         | Version    |
|--------|---------|-------|--------------|-------------------------------------------|------------|
| Clawd  | ollama  | 11434 | 0.0.0.0      | `mistral:7b-instruct-v0.3-q4_K_M`        | 0.15.5     |
| Brutus | ollama  | 11434 | 0.0.0.0      | `qwen2.5-coder:3b`                        | 0.16.1     |
| Plutos | ollama  | 11434 | 0.0.0.0      | `llama3.1:8b-instruct-q4_K_M`            | 0.16.1     |
| Nexus  | –       | –     | –            | –                                         | –          |

**Issues:**
- **Missing models per design**:
  - Clawd should also provide `qwen-coder` (3B).
  - Plutos should also provide `qwen14b` (likely `qwen2.5:14b` or similar).
- **Version drift**: Clawd on older Ollama (0.15.5). Recommend upgrade to match 0.16.1 for consistency.
- **Authentication**: Ollama API lacks built‑in auth; exposes full inference capability to any reachable host.
- **Network exposure**: Bound to `0.0.0.0`; reachable from any interface. Must restrict via firewall or bind to mesh IP (`10.0.0.x`).

### OpenClaw Gateway

All nodes run `openclaw-gateway`:

| Node   | PID (sample) | Bind Address   | Mode | Version          |
|--------|--------------|-----------------|------|------------------|
| Clawd  | 1475912      | 127.0.0.1:18789 | local| 2026.2.3-1       |
| Brutus | 869233       | 127.0.0.1:18789 | local| likely same      |
| Plutos | 1031         | 127.0.0.1:18789 | local| likely same      |
| Nexus  | (via pgrep) | 127.0.0.1:18789 | local| likely same      |

**Critical observations:**
- Gateway token **exposed** in both systemd unit file and `openclaw.json` with permissions `0644/0664`.
- All instances appear to be **full gateways**, meaning each may attempt to poll external services (Telegram, WhatsApp, etc.). Only **one** should be active for channel integrations to avoid duplicate message handling.
- `gateway.mode: local` and `bind: loopback` prevent remote agents from connecting; intended for local agent communication only. This is acceptable if each node’s agents run on the same host.

### Fail2Ban

- Active on all systemd nodes (Clawd, Brutus, Plutos). Nexus (Alpine) reports `started` via OpenRC.
- Without firewall integration, Fail2Ban may not block effectively. Verify `ufw`/`nftables` hooks.

---

## Security

### Firewall Status

- **No `ufw` installed** on any node. `nftables` absent. Only rudimentary iptables rules observed on Nexus (f2b-sshd chain) – not sufficient.
- All listening services (`0.0.0.0:22`, `0.0.0.0:11434`) are unprotected from internet if nodes have public IPs.
- **Recommendation**: Deploy a host‑based firewall (nftables or ufw) with policy:
  ```
  * Allow from 10.0.0.0/24 to any port 22 (SSH)
  * Allow from 10.0.0.0/24 to any port 11434 (Ollama)
  * Allow established/related
  * Deny all other inbound
  ```

### Sensitive File Permissions

| File                                          | Perms   | Risk Level | Contains                           |
|-----------------------------------------------|---------|------------|------------------------------------|
| `~/.openclaw/openclaw.json`                   | 0664    | HIGH       | Telegram token, API keys, gateway token |
| `~/.config/systemd/user/openclaw-gateway.service` | 0644 | HIGH       | `OPENCLAW_GATEWAY_TOKEN` in cleartext |
| `~/.openclaw/credentials/*.json`              | 0600? (check) | OK if 0600 | OAuth tokens, pairing info |
| `~/.ssh/*_key`                                | 0600    | OK         | SSH keys                           |

**Findings:**
- `openclaw.json` is **world‑readable**. Contains:
  - `channels.telegram.botToken`: `8599196253:AAF5afDBxVMzS9RiDUu1DNTSO6u9jNqZYvM`
  - `env.NVIDIA_API_KEY`: `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`
  - `env.BRAVE_API_KEY`: `BSAQPV8ULsWtC3J_uQRINOdv673ky4m`
  - `gateway.auth.token`: same as in unit file.
- Unit file itself is `0644`. Any local user can read the token.

**Remediation commands:**

```bash
# Restrict openclaw.json to owner-only
chmod 600 ~/.openclaw/openclaw.json

# Move gateway token to dedicated env file and restrict permissions
mkdir -p ~/.openclaw/conf
cat > ~/.openclaw/conf/gateway.env <<'EOF'
OPENCLAW_GATEWAY_TOKEN=63a3931e00c32d904c464e7b1f99a64ccf5ecbec1d2cddea
EOF
chmod 600 ~/.openclaw/conf/gateway.env

# Edit unit file to source env file, then reload
sed -i '/Environment=OPENCLAW_GATEWAY_TOKEN/d' ~/.config/systemd/user/openclaw-gateway.service
echo 'EnvironmentFile=%h/.openclaw/conf/gateway.env' >> ~/.config/systemd/user/openclaw-gateway.service
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway

# Ensure unit file is not world-readable (but typically it is in user dir; still restrict)
chmod 600 ~/.config/systemd/user/openclaw-gateway.service
```

### Ollama Exposure

- Ollama bind address `0.0.0.0:11434` on **all** inference nodes. This exposes the inference API to any network interface. Combined with lack of authentication, this allows:
  - Unauthorized use of your models (inference time = CPU cost)
  - Potential data leakage via prompts
  - Denial‑of‑service by exhausting resources

**Remediation (choose one):**

1. **Bind to localhost only** (recommended if only local agents use Ollama):
   ```bash
   # For each node, edit /etc/ollama.service.d/override.conf
   sudo sed -i 's/^Environment="OLLAMA_HOST=.*/Environment="OLLAMA_HOST=127.0.0.1"/' /etc/systemd/system/ollama.service.d/override.conf
   sudo systemctl daemon-reload && sudo systemctl restart ollama
   ```
   Then update `openclaw.json` providers to point to `127.0.0.1:11434` on respective nodes (or keep current `10.0.0.x` if you prefer mesh‑only access).

2. **Restrict via firewall** to mesh CIDR only:
   ```bash
   # Example with ufw (install ufw first)
   sudo ufw allow from 10.0.0.0/24 to any port 11434
   sudo ufw deny from any to any port 11434
   sudo ufw --force enable
   ```

### Telegram Bot Duplication

- OpenClaw gateway running on **all** nodes, each reading the same `openclaw.json` with `plugins.telegram.enabled: true`.
- Telegram bot will receive duplicate updates (once per gateway) causing repeated processing.
- **Single point of failure** if the designated primary goes down; but multiple active instances are worse.

**Remediation:** Disable Telegram plugin on all non‑primary nodes.

```bash
# On Brutus and Plutos (and Nexus if desired), set:
sed -i 's/"enabled": true/"enabled": false/' ~/.openclaw/openclaw.json
# Then restart gateway on those nodes
systemctl --user restart openclaw-gateway   # as boss user
```

Better: Use environment variable per node to conditionally disable plugins.

---

## Configuration Drift

### Desired vs Observed

| Component                     | Desired State (Baseline / Intent)                          | Observed (2026‑02‑27)                              | Drift Severity |
|-------------------------------|-----------------------------------------------------------|----------------------------------------------------|----------------|
| **WireGuard (Clawd)**         | `/etc/wireguard/wg0.conf` present; `wg-quick@wg0` active & enabled | Config unreadable (0600), wg0 UP but peer status unknown | 🔴 Critical (unverified) |
| **SSH port**                  | Non‑standard `2222` on all nodes                         | All nodes: `22`                                    | 🔴 Critical |
| **SSH bind**                  | Mesh IP only (`10.0.0.x`)                                 | `0.0.0.0` (all interfaces)                        | 🔴 Critical |
| **OpenClaw gateway bind**     | Mesh IP for remote agents (or keep loopback if agents local) | `127.0.0.1` (loopback) – acceptable for local agents but token exposed | 🟡 Medium |
| **OpenClaw config perms**     | `600` (owner‑only)                                        | `664` for `openclaw.json`; unit file `644`       | 🔴 Critical |
| **Ollama models – Clawd**      | `mistral:7b...` **and** `qwen2.5-coder:3b`               | Only `mistral` present                            | 🔴 Critical |
| **Ollama models – Plutos**     | `llama3.1:8b...` **and** `qwen14b`                       | Only `llama3.1` present                            | 🔴 Critical |
| **Ollama config.yaml**        | Remove remote `host:` entries or set to `0.0.0.0`        | Clawd & Plutos: `host: 10.0.0.4:11434` (invalid)   | 🔴 Critical |
| **Ollama version**            | Consistent across inference nodes (latest stable)        | Clawd: 0.15.5 vs Brutus/Plutos: 0.16.1          | 🟡 Medium |
| **Ollama service override**   | Uniform `OLLAMA_HOST=0.0.0.0`                            | Plutos has additional `Restart=always RestartSec=10` – benign | 🟢 OK |

### Configuration File Inventory

- `/etc/ollama/config.yaml` exists on Clawd & Plutos (content: `host: 10.0.0.4:11434`). This is **incorrect** if Ollama is meant to run locally; it may be ignored by the systemd override, but confusing. **Delete or correct**.
- `/etc/ollama` on Brutus missing `config.yaml` – optional, but OK.
- Systemd overrides:
  - Clawd: `/etc/systemd/system/ollama.service.d/override.conf` contains `Environment="OLLAMA_HOST=0.0.0.0"`
  - Brutus: same with explicit port
  - Plutos: `OLLAMA_HOST=0.0.0.0` plus restart settings
- SSH config uses default `/etc/ssh/sshd_config` with `Port 22` and `ListenAddress 0.0.0.0`. Desired: `Port 2222` and `ListenAddress 10.0.0.x`.

---

## Resource Utilization

All nodes show excellent headroom; no saturation risks detected.

| Node   | CPU Cores | Memory Total | Used | Load Avg (1m) | Disk Total | Used | FS Use% |
|--------|-----------|--------------|------|---------------|------------|------|---------|
| Clawd  | 8         | 15 GiB       | 1.6 GiB | 0.03        | 464 GiB    | 31 GiB | 7%      |
| Brutus | 6         | 7.7 GiB      | 1.8 GiB | 0.01        | 232 GiB    | 12 GiB | 5%      |
| Plutos | 8         | 31 GiB       | 2.1 GiB | 0.00        | 464 GiB    | 32 GiB | 7%      |
| Nexus  | 1         | 941 MiB      | 97 MiB  | 0.06        | 9.1 GiB    | 686 MiB | 8%      |

- CPU load averages are negligible (< 0.2), indicating no contention.
- Memory free > 2 GiB on all but Nexus (754 MiB free on 1 GiB total – acceptable for security‑hub role).
- Disk usage < 10% everywhere.

---

## Cost & High Availability

### Single Points of Failure (SPOF)

1. **Telegram/Channel Integration** – Only one gateway should be active for external channels. Currently all four are running → duplicate processing, not SPOF.
2. **OpenClaw Gateway cluster** – If the designated primary (Clawd) fails, no automatic failover to other gateways for channel integrations. Recommend implementing leader election (e.g., via lock file in shared storage) or a DNS round‑robin with health checks.
3. **External API keys** – Brave and NVIDIA keys are hard‑coded in `openclaw.json`. Compromise of any node leaks them. Consider vault‑based secret distribution (e.g., HashiCorp Vault, 1Password) with runtime injection.

### Cost Optimization

- **Free‑tier usage**: Default agent model is `openrouter/stepfun/step-3.5-flash:free` – good. Verify that fallback providers are not inadvertently used in batch jobs (check agent logs).
- **Local inference**: Ollama models are self‑hosted and free – excellent.
- **Runaway API keys**: NVIDIA API key (`nvapi-...`) and Brave API key are in `openclaw.json`. Implement usage limits and alerts on those providers.
- **Model sprawl**: Missing models could lead to unnecessary fallback to paid cloud models. Pull required local models to avoid unexpected costs.

---

## Backup + Recovery

- **Baseline snapshots** present in `memory/`: `*_baseline_permissions.json`, `*_baseline_network.json`, `*_baseline_secrets.json`. Good.
- **Daily backup script** at `/home/boss/.openclaw/workspace/maintenance/daily_backup.sh` (cron @ 2 am). Verify it runs without errors (check logs if any).
- **Configuration files** (`openclaw.json`, Ollama systemd units, WireGuard configs) are **not** explicitly included in backups. Recommend extending `daily_backup.sh` to tar `/etc/wireguard`, `/etc/ollama`, `/etc/systemd/system/ollama.service*`, and `~/.config/systemd/user/openclaw-gateway.service`.

---

## Top 5 Recommendations (Actionable)

### 1. Secure OpenClaw Secrets
**Problem**: Gateway token and API keys world‑readable in `openclaw.json` and unit file.  
**Fix**:
```bash
chmod 600 ~/.openclaw/openclaw.json
# Move token to dedicated env file
mkdir -p ~/.openclaw/conf
printf 'OPENCLAW_GATEWAY_TOKEN=63a3931e00c32d904c464e7b1f99a64ccf5ecbec1d2cddea\n' > ~/.openclaw/conf/gateway.env
chmod 600 ~/.openclaw/conf/gateway.env
# Remove token from unit file and add EnvironmentFile=
sed -i '/Environment=OPENCLAW_GATEWAY_TOKEN/d' ~/.config/systemd/user/openclaw-gateway.service
echo 'EnvironmentFile=%h/.openclaw/conf/gateway.env' >> ~/.config/systemd/user/openclaw-gateway.service
chmod 600 ~/.config/systemd/user/openclaw-gateway.service
systemctl --user daemon-reload && systemctl --user restart openclaw-gateway
```

### 2. Prevent Telegram Duplication
**Problem**: Multiple gateways polling Telegram → duplicate messages.  
**Fix** (disable on all but Clawd):
```bash
# On Brutus, Plutos, Nexus:
sed -i 's/"enabled": true/"enabled": false/' ~/.openclaw/openclaw.json
systemctl --user restart openclaw-gateway
```
Optionally stop and disable the service on non‑primary nodes:
```bash
systemctl --user disable --now openclaw-gateway
```

### 3. Harden Ollama Network Exposure
**Problem**: Ollama API reachable from any interface, no auth.  
**Fix** (bind to localhost):
```bash
# On each inference node (Clawd, Brutus, Plutos):
sudo bash -c 'cat > /etc/systemd/system/ollama.service.d/override.conf <<EOF
[Service]
Environment="OLLAMA_HOST=127.0.0.1"
EOF'
sudo systemctl daemon-reload && sudo systemctl restart ollama
```
Update `openclaw.json` providers to use `127.0.0.1:11434` (or keep `10.0.0.x` if you want mesh‑only access and firewall blocks external).

### 4. Deploy Basic Firewall
**Problem**: No host firewall; services exposed to internet if public IP exists.  
**Fix** (using nftables or ufw). Example with nftables (distributed across nodes):
```bash
sudo nft add table inet filter
sudo nft 'add chain inet filter input { type filter hook input priority 0; policy drop; }'
sudo nft add rule inet filter input ct state established,related accept
sudo nft add rule inet filter input ip saddr 10.0.0.0/24 tcp dport {22,11434} accept
sudo nft add rule inet filter input lo accept
# Save ruleset
sudo nft list ruleset > /etc/nftables.conf
# Enable nftables service
sudo systemctl enable --now nftables
```
Or use `ufw`:
```bash
sudo apt-get install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 10.0.0.0/24 to any port 22
sudo ufw allow from 10.0.0.0/24 to any port 11434
sudo ufw --force enable
```

### 5. Resolve Model Gaps & Version Consistency
**Problem**: Missing Ollama models on inference nodes; version mismatch.  
**Fix**:
```bash
# On Clawd: pull qwen2.5-coder:3b (or qwen-coder alias)
ssh clawd 'ollama pull qwen2.5-coder:3b'
# On Plutos: pull qwen14b (choose exact tag, e.g., qwen2.5:14b)
ssh plutos 'ollama pull qwen2.5:14b'
# Upgrade Clawd’s Ollama to 0.16.1 to match others
ssh clawd 'sudo apt-get update && sudo apt-get install -y ollama=0.16.1'  # adjust package source
```
Verify models appear in API responses: `curl http://10.0.0.x:11434/api/tags`.

---

## Additional Notes

- **WireGuard config files** are not readable by non‑root; ensure they exist at `/etc/wireguard/wg0.conf` with `0600` perms and that `wg-quick@wg0` is enabled (`systemctl enable --now wg-quick@wg0`). Re‑verify peer handshake with `sudo wg show`.
- **SSH hardening**: Consider changing port to `2222`, disabling password auth (`PasswordAuthentication no`), and allowing only mesh IPs (`ListenAddress 10.0.0.x`). This requires coordination and testing.
- **Node pairing**: `openclaw nodes status` shows 0 paired nodes. Review node identity configuration (`~/.openclaw/identity/device.json`) and network reachability on gateway port 18789 (currently loopback only – by design?). If agents on different hosts need to communicate, reconfigure `gateway.bind` to the mesh IP.

---

**Audit completeness:** Partial – some checks (full firewall ruleset, WireGuard peer stats, sudoers inspection) require root access that was not available during this run. Recommend running the next audit with passwordless sudo for the `boss` user on all nodes to capture those details.

---

*Report generated automatically by System Architect Agent.*