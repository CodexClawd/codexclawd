# OpenClaw Mesh Infrastructure Audit Report
**Date:** 2026-03-04
**Auditor:** System Architect Agent (cron: daily-3am-arch-audit)
**Scope:** Full mesh of 4 nodes (Nexus 10.0.0.1, Clawd 10.0.0.2, Brutus 10.0.0.3, Plutos 10.0.0.4)

---

## Executive Summary

**Overall Health Score:** 5/10
**Trend:** ↑ Improved (from 2/10 on 2026-03-03)

The mesh infrastructure has **recovered from yesterday's catastrophic outage**. All four nodes are now reachable, WireGuard tunnels are established, and core services (Ollama APIs, OpenClaw gateway) are operational on inference nodes. However, **significant security and configuration issues remain** that pose risks of secret exposure, unauthorized access, and operational fragility.

**Priority Issues:**
1. **Critical secret exposure** – `openclaw.json` on Clawd is world-readable and contains NVIDIA_API_KEY and BRAVE_API_KEY.
2. **Gateway token exposure** – `openclaw-gateway.service` files on all gateway nodes are world-readable (0664), exposing tokens.
3. **Unnecessary gateway duplication** – Brutus and Plutos run OpenClaw gateway instances; only Clawd should be the primary gateway.
4. **Ollama API exposed to mesh/internet** – All inference nodes bind Ollama to `0.0.0.0:11434` without firewall or authentication.
5. **No host firewall** – nftables rulesets are empty; SSH and Ollama are exposed to the internet on nodes with public IPs.
6. **Model gaps** – Clawd missing `qwen2.5-coder:3b`; Plutos missing `qwen14b`. This forces fallback to external paid APIs.
7. **Version drift** – Clawd runs Ollama 0.15.5 while Brutus/Plutos run 0.16.1.
8. **Missing baselines** – Baseline files in `memory/` are empty; no drift detection reference.
9. **Weak directory permissions** – `~/.openclaw` on Brutus/Plutos is world-readable (0755).
10. **No fail2ban** – Brute-force protection absent on SSH.

---

## Mesh Health

### Connectivity Summary (snapshot 2026-03-04T02:00:08Z from sentinel)

| Target    | Status | Ping (ms) | Ollama API | Latency (ms) | Notes |
|-----------|--------|-----------|------------|--------------|-------|
| 10.0.0.1  | UP     | 13.9      | N/A        | 13.9         | Nexus (security hub) – wg0 UP, process check unclear |
| 10.0.0.2  | UP     | 0.04      | UP         | 0.04         | Clawd (gateway) – healthy |
| 10.0.0.3  | UP     | 25.7      | UP         | 25.7         | Brutus (coding) – healthy |
| 10.0.0.4  | UP     | 12.6      | UP         | 12.6         | Plutos (heavy inference) – healthy |

- **WireGuard**:
  - Clawd: `wg0` interface UP (10.0.0.2/24) but `wg-quick@wg0` service is **inactive (dead)**. Interface remains up but not managed.
  - Brutus: `wg0` UP (10.0.0.3/24) but `wg-quick@wg0` service **inactive (dead)**.
  - Plutos: `wg0` UP (10.0.0.4/24) with service **active (exited)** – normal for wg-quick.
  - Nexus: `wg0` UP (10.0.0.1/24), systemd not available ( Alpine or busybox? ), but interface up.

- **Alert history**: Yesterday's CRITICAL alerts for Nexus and Brutus offline have cleared. No active alerts as of 02:00 UTC.

### Recovery Actions Performed
- Nodes were brought online between 01:45–02:15 UTC (likely automatic recovery or manual intervention).
- WireGuard interfaces resumed operation; however, **wg-quick services on Clawd and Brutus should be re-enabled** to ensure automatic restart on boot/rebuild.

**Immediate Fixes:**
```bash
# On Clawd and Brutus (enable wg-quick)
sudo systemctl enable --now wg-quick@wg0  # requires sudo; if not possible, add to /etc/rc.local or equivalent
# Verify:
sudo wg show
```

---

## Services

### OpenClaw Gateway

| Node   | Version      | PID   | Uptime   | Status   | Telegram | Config Perms |
|--------|--------------|-------|----------|----------|----------|--------------|
| Clawd  | 2026.2.3-1   | 1475912 | 6 days   | active   | enabled  | 664 (world-read) |
| Brutus | 2026.2.9     | 869233 | 2 weeks  | active   | enabled  | 664 |
| Plutos | 2026.2.9     | 1031   | 2 weeks  | active   | enabled  | 664 |

- **Version drift**: Clawd is on older version. Upgrade recommended.
- **Telegram duplication**: All three nodes have Telegram plugin enabled with **different bot tokens**. This causes duplicate updates if all bots are added to the same group/channel. Only Clawd should have Telegram enabled; disable on Brutus and Plutos.
- **Service duplication**: Brutus and Plutos should not run `openclaw-gateway` at all. They should only run `openclaw-node` (worker agents). Stop and disable the gateway on these nodes to reduce attack surface and avoid conflicts.

**Commands:**
```bash
# Disable gateway on Brutus and Plutos
ssh brutus 'systemctl --user disable --now openclaw-gateway'
ssh plutos 'systemctl --user disable --now openclaw-gateway'
# Ensure openclaw-node remains running (if needed)
# Optionally remove from autostart: systemctl --user disable openclaw-gateway
```

### SSH Daemon

| Node   | Port | Bind Address | Status    | Auth Method |
|--------|------|--------------|-----------|-------------|
| Clawd  | 22   | 0.0.0.0      | reachable | keys + pwd? |
| Brutus | 22   | 0.0.0.0      | reachable | keys + pwd? |
| Plutos | 22   | 0.0.0.0      | reachable | keys + pwd? |
| Nexus  | 22   | 0.0.0.0      | reachable | keys + pwd? |

- All nodes expose SSH on all interfaces (`0.0.0.0`) and port 22. This is **high risk** given public IPs (Clawd's external IP is 85.215.46.147).
- **Hardening required**:
  - Change port to `2222` (or non-standard)
  - Bind to mesh IP only (`10.0.0.x`)
  - Disable password authentication; use keys only.
  - Install and configure `fail2ban`.

**Example hardening:**
```bash
# On each node (as root):
sed -i 's/^#Port 22/Port 2222/' /etc/ssh/sshd_config
sed -i 's/^#ListenAddress 0.0.0.0/ListenAddress 10.0.0.$(hostname -s | sed "s/nexus/1/;s/clawd/2/;s/brutus/3/;s/plutos/4/")/' /etc/ssh/sshd_config
sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd
# Install fail2ban
apt-get install -y fail2ban
# Copy basic jail config and enable
cat > /etc/fail2ban/jail.local <<'EOF'
[sshd]
enabled = true
port = 2222
filter = sshd
logpath = /var/log/auth.log
maxretry = 5
EOF
systemctl enable --now fail2ban
```

### Ollama API

| Node   | Version  | Models Available (API)                     | Bind Address |
|--------|----------|--------------------------------------------|--------------|
| Clawd  | 0.15.5   | `mistral:7b-instruct-v0.3-q4_K_M`        | 0.0.0.0:11434 |
| Brutus | 0.16.1   | `qwen2.5-coder:3b`                        | 0.0.0.0:11434 |
| Plutos | 0.16.1   | `llama3.1:8b-instruct-q4_K_M`            | 0.0.0.0:11434 |
| Nexus  | (unknown)| (process seen, API not accessible)       | unknown      |

- **Critical**: Ollama binds to all interfaces (`0.0.0.0`) on Clawd, Brutus, Plutos. This exposes the API to the internet and the entire mesh without authentication. Combined with lack of firewall, any actor can query or use these models.
- **Missing models**:
  - Clawd should also run `qwen2.5-coder:3b` to provide coding capability locally.
  - Plutos should also run `qwen14b` (e.g., `qwen2.5:14b`) for advanced tasks.
- **Version inconsistency**: Clawd on 0.15.5; upgrade to 0.16.1.
- **Nexus anomaly**: Ollama process observed earlier but `ollama` command not in PATH and API not responding. Verify and likely remove Ollama from Nexus (security hub should not run inference).

**Remediation:**
```bash
# Pull missing models
# On Clawd:
ollama pull qwen2.5-coder:3b
# On Plutos:
ollama pull qwen2.5:14b   # or desired 14b variant
# Upgrade Ollama on Clawd to 0.16.1:
apt-get update && apt-get install -y ollama
# Restart service:
systemctl --user restart ollama  # or: systemctl restart ollama (if system service)
```

---

## Security

### File Permissions – Sensitive Credentials

| File                                          | Node   | Perms   | Risk  | Contains |
|-----------------------------------------------|--------|---------|-------|----------|
| `~/.openclaw/openclaw.json`                   | Clawd  | 0664    | **CRITICAL** | NVIDIA_API_KEY, BRAVE_API_KEY, gateway token, Telegram token |
| `~/.openclaw/openclaw.json`                   | Brutus | 0600    | OK    | (similar, but protected) |
| `~/.openclaw/openclaw.json`                   | Plutos | 0600    | OK    | (protected) |
| `~/.config/systemd/user/openclaw-gateway.service` | Clawd | 0664    | **CRITICAL** | `Environment=OPENCLAW_GATEWAY_TOKEN=...` |
| `~/.config/systemd/user/openclaw-gateway.service` | Brutus| 0664    | **CRITICAL** | token exposed |
| `~/.config/systemd/user/openclaw-gateway.service` | Plutos| 0664    | **CRITICAL** | token exposed |
| `~/.openclaw/` (directory)                   | Clawd  | 0700    | OK    | – |
| `~/.openclaw/` (directory)                   | Brutus | 0755    | MED   | world-listable (filenames visible) |
| `~/.openclaw/` (directory)                   | Plutos | 0755    | MED   | world-listable |

**Remediation (apply to all affected nodes):**
```bash
# 1. Restrict openclaw.json to 600
chmod 600 ~/.openclaw/openclaw.json

# 2. Move gateway tokens to dedicated env files with strict perms
mkdir -p ~/.openclaw/conf
cat > ~/.openclaw/conf/gateway.env <<'EOF'
OPENCLAW_GATEWAY_TOKEN=$(jq -r '.gateway.auth.token' ~/.openclaw/openclaw.json)
EOF
chmod 600 ~/.openclaw/conf/gateway.env

# 3. Remove token from systemd unit and reference env file
sed -i '/Environment=OPENCLAW_GATEWAY_TOKEN/d' ~/.config/systemd/user/openclaw-gateway.service
echo 'EnvironmentFile=%h/.openclaw/conf/gateway.env' >> ~/.config/systemd/user/openclaw-gateway.service
chmod 600 ~/.config/systemd/user/openclaw-gateway.service

# 4. Tighten .openclaw directory perms
chmod 700 ~/.openclaw

# 5. Reload and restart gateway
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway
```

### Firewall – Missing Entirely

- **nftables** config on Clawd, Brutus, Plutos exists but is **empty** (no rules). Default policy is likely ACCEPT. All ports are open to the world.
- **ufw** is installed on Brutus and Plutos but not active (or we can't verify status due to sudo). Clawd has nftables only.
- This leaves SSH (22) and Ollama (11434) directly exposed to the internet on nodes with public IPs (Clawd: 85.215.46.147). Brutus and Plutos may also have public IPs.

**Remediation – Deploy a restrictive firewall:**
```bash
# Recommended nftables ruleset (apply to all nodes):
sudo nft flush ruleset
sudo nft add table inet filter
sudo nft 'add chain inet filter input { type filter hook input priority 0; policy drop; }'
sudo nft add rule inet filter input ct state established,related accept
sudo nft add rule inet filter input ip saddr 10.0.0.0/24 tcp dport {22,11434} accept
sudo nft add rule inet filter input ip saddr 10.0.0.0/24 udp dport 51820 accept   # WireGuard
sudo nft add rule inet filter input lo accept
# Optional: allow ICMP echo from mesh only
sudo nft add rule inet filter input ip saddr 10.0.0.0/24 icmp type echo-request accept
sudo nft list ruleset > /etc/nftables.conf
sudo systemctl enable --now nftables
```

### Other Security Gaps

- **fail2ban** not installed on any node – increases brute-force risk on SSH.
- **SSH password authentication** appears enabled (we connected with keys, but password may still be allowed). Disable passwords.
- **Ollama network exposure** should be mitigated by binding to localhost (`127.0.0.1`) if agents connect locally. However, some providers in `openclaw.json` reference remote IPs (`10.0.0.3`, `10.0.0.4`, `10.0.0.2`). To secure, either:
  - Bind Ollama to `127.0.0.1` on each node and keep providers as `http://127.0.0.1:11434`; or
  - Keep binding to mesh interface but firewall restrict to mesh CIDR only.
- **Exposed services** from network baseline: ports 3000, 9100, 9092, 44321, 4330 are listening on `0.0.0.0` on Clawd. Identify what they are and restrict or firewall them. Likely Syncthing, Prometheus node exporter, and custom apps. Ensure they require authentication.

---

## Configuration Drift

| Component                     | Desired State (Target)                                          | Observed (2026-03-04)                                 | Severity |
|-------------------------------|-----------------------------------------------------------------|-------------------------------------------------------|----------|
| **WireGuard**                 | wg0 up, peers connected, service enabled & managed             | Clawd/Brutus service dead; wg0 up but not auto-restart | 🔴 Critical |
| **OpenClaw gateway instances**| Only Clawd runs gateway                                          | Brutus & Plutos also running gateway                | 🔴 Critical |
| **OpenClaw version**          | Consistent across all gateway nodes                             | Clawd 2026.2.3-1 vs Brutus/Plutos 2026.2.9          | 🟡 Medium |
| **Ollama models – Clawd**     | mistral **and** qwen2.5-coder:3b                                | Only mistral present                                 | 🔴 Critical |
| **Ollama models – Plutos**    | llama3.1:8b **and** qwen14b                                     | Only llama3.1:8b present                             | 🔴 Critical |
| **Ollama version**            | All nodes on 0.16.1                                             | Clawd on 0.15.5                                      | 🟡 Medium |
| **Ollama bind address**       | 127.0.0.1 (if local agents) or firewall mesh-only              | 0.0.0.0 on all inference nodes                      | 🔴 Critical |
| **openclaw.json perms**       | 600 (owner-only)                                                | Clawd 664; Brutus/Plutos 600                        | 🔴 Critical (Clawd) |
| **gateway.service perms**     | 600                                                            | All three nodes 664                                 | 🔴 Critical |
| **~/.openclaw perms**         | 700                                                            | Brutus/Plutos 755                                   | 🟡 Medium |
| **SSH hardening**             | Port 2222, bind to mesh IP, disable password, fail2ban active | Port 22, bind 0.0.0.0, no fail2ban                  | 🔴 Critical |
| **Telegram plugin**           | Enabled only on primary gateway (Clawd)                        | Enabled on Clawd, Brutus, Plutos                     | 🔴 Critical |
| **Baseline files**            | Non-empty snapshots of secure configurations                  | All baseline files empty                            | 🔴 Critical |

---

## Resource Utilization

| Node   | CPU Cores | Memory Total | Used | Load Avg (1m) | Disk Total | Used | FS Use% | Notes |
|--------|-----------|--------------|------|---------------|------------|------|---------|-------|
| Clawd  | 8         | 15 GiB       | 2.2 GiB | 0.03        | 464 GiB    | 31 GiB | 7%      | Excellent headroom |
| Nexus  | 1         | 941 MiB      | 98 MiB | –             | 9.1 GiB    | 687 MiB | 8%      | Limited but sufficient for security hub |
| Brutus | 6         | 7.7 GiB      | 1.8 GiB | –             | 232 GiB    | 12 GiB | 5%      | Good headroom |
| Plutos | 8         | 31 GiB       | 2.0 GiB | –             | 464 GiB    | 32 GiB | 7%      | Excellent |

- No saturation risks on operational nodes.
- All nodes have ample memory and disk space.

---

## Cost & High Availability

### Single Points of Failure

1. **Primary gateway dependency** – Only Clawd should be the designated gateway for external channels. If Clawd fails and others have gateway disabled, channel connectivity is lost until failover. We recommend:
   - Keep gateway disabled on Brutus/Plutos.
   - Implement a quick-failover script that promotes one of the worker nodes to gateway if Clawd becomes unresponsive.
2. **Node capacity** – While all nodes are up, losing any one reduces capacity (inference or security functions). Consider adding a fifth node for redundancy if budget allows.

### Cost Optimization

- **Free-tier models**: Default `openrouter/stepfun/step-3.5-flash:free` is in use – good.
- **Local inference**: Ollama models are self-hosted and free. However, missing local models (`qwen-coder` on Clawd, `qwen14b` on Plutos) force fallback to paid providers (NVIDIA, OpenRouter) for certain tasks. This may incur costs if usage is high.
- **Runaway API keys**: NVIDIA_API_KEY and BRAVE_API_KEY are present. Monitor usage dashboards and set hard limits. Consider moving to vault-based secret distribution (e.g., HashiCorp Vault, 1Password) rather than embedding in config.
- **Telegram bot duplication** – Not a direct cost, but wastes resources and may lead to rate-limit issues if multiple bots hit the same Telegram API.

---

## Backup + Recovery

- **Workspace backup**: `maintenance/daily_backup.sh` runs daily at 02:00 and commits changes to git (origin & backup remotes). This backs up all workspace files but **excludes critical system configurations** (`/etc/wireguard`, `/etc/ollama`, systemd units, firewall rules).
- **Baseline snapshots**: Exists in `memory/` but are empty. They should be populated with secure baselines after hardening.
- **Recommendation**: Extend `daily_backup.sh` to include system configs as compressed tarballs in a dedicated backup directory, then commit those as well. Run a full system config backup after major changes.

**Enhanced backup snippet:**
```bash
CONFIG_BACKUP_DIR="backup/system-configs/$(date +%Y-%m-%d)"
mkdir -p "$CONFIG_BACKUP_DIR"
sudo tar czf "$CONFIG_BACKUP_DIR/wireguard.tgz" /etc/wireguard 2>/dev/null || true
sudo tar czf "$CONFIG_BACKUP_DIR/ollama.tgz" /etc/ollama 2>/dev/null || true
sudo tar czf "$CONFIG_BACKUP_DIR/systemd-ollama.tgz" /etc/systemd/system/ollama.service* 2>/dev/null || true
sudo tar czf "$CONFIG_BACKUP_DIR/openclaw-gateway.tgz" /home/boss/.config/systemd/user/openclaw-gateway.service 2>/dev/null || true
sudo tar czf "$CONFIG_BACKUP_DIR/nftables.tgz" /etc/nftables.conf 2>/dev/null || true
# Add to git commit
git add "$CONFIG_BACKUP_DIR"
```

---

## Top 5 Recommendations (Actionable)

### 1. Secure OpenClaw Secrets and Permissions (URGENT)
**Risk**: Critical API keys and tokens are world-readable on Clawd.  
**Action**: Apply remediation steps from Security section to all nodes with misconfigurations.

```bash
# On Clawd, Brutus, Plutos (as boss):
chmod 600 ~/.openclaw/openclaw.json
# Move tokens to env file and clean unit files (see full script above)
mkdir -p ~/.openclaw/conf
jq -r '.gateway.auth.token' ~/.openclaw/openclaw.json > ~/.openclaw/conf/gateway.env
chmod 600 ~/.openclaw/conf/gateway.env
sed -i '/Environment=OPENCLAW_GATEWAY_TOKEN/d' ~/.config/systemd/user/openclaw-gateway.service
echo 'EnvironmentFile=%h/.openclaw/conf/gateway.env' >> ~/.config/systemd/user/openclaw-gateway.service
chmod 600 ~/.config/systemd/user/openclaw-gateway.service
chmod 700 ~/.openclaw
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway
```

### 2. Deactivate Duplicate Gateways and Telegram (URGENT)
**Risk**: Multiple Telegram bots cause duplicate updates; unnecessary services increase attack surface.  
**Action**: Stop and disable openclaw-gateway on Brutus and Plutos; keep only on Clawd.

```bash
ssh brutus 'systemctl --user disable --now openclaw-gateway'
ssh plutos 'systemctl --user disable --now openclaw-gateway'
# Verify: on those nodes, only openclaw-node should run
```

### 3. Harden Network Firewall (URGENT)
**Risk**: All services exposed to internet; SSH and Ollama directly reachable.  
**Action**: Deploy nftables with mesh-only allow rules and drop-all-else policy.

```bash
# Distribute and apply the nftables ruleset provided earlier to all nodes.
# Make sure to allow SSH from mesh CIDR (10.0.0.0/24) and WireGuard UDP 51820.
```

### 4. Complete Ollama Model Portfolio and Version Alignment
**Risk**: Missing models trigger fallback to paid APIs; version drift may cause incompatibilities.  
**Action**:
```bash
# On Clawd:
ollama pull qwen2.5-coder:3b
sudo apt-get update && sudo apt-get install -y ollama   # upgrade to 0.16.1
# On Plutos:
ollama pull qwen2.5:14b  # or qwen14b variant
# On Nexus: verify if ollama should be removed entirely (process not needed)
# Consider: If Ollama must run on Nexus for some reason, ensure it's bound to 127.0.0.1 only.
```

### 5. Harden SSH and Install Fail2ban
**Risk**: Brute-force attacks on exposed SSH port 22.  
**Action**:
```bash
# On all nodes:
sed -i 's/^#Port 22/Port 2222/' /etc/ssh/sshd_config
# Determine mesh IP for ListenAddress (10.0.0.1 for nexus, etc.)
sed -i 's/^#ListenAddress 0.0.0.0/ListenAddress 10.0.0.$(hostname -s | sed "s/nexus/1/;s/clawd/2/;s/brutus/3/;s/plutos/4/")/' /etc/ssh/sshd_config
sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd
apt-get install -y fail2ban
# Enable jail for sshd on port 2222
```

---

## Additional Notes

- **Sentinel monitoring** is functioning and provided timely alerts yesterday. The script can also be enhanced to check wg-quick service status and firewall configuration.
- **Baseline capture**: The empty baseline files indicate the initialization step was skipped. Run a proper baseline capture after hardening:
  ```bash
  # As System Architect with privileges:
  capture baseline permissions and network state into memory/baseline_*.json
  ```
- **OpenClaw config**: Consider separating provider configurations per node to avoid hardcoding IPs. Use `127.0.0.1` for local Ollama and rely on Docker/Kubernetes service discovery if applicable.
- **Nexus role**: Verify that Ollama is not intended to run on Nexus. If it is running inadvertently, uninstall or stop it.
- **Resource headroom**: Good; no immediate scaling needed.

---

*Report generated by System Architect Agent on 2026-03-04T02:30:00Z. All commands assume `boss` user with appropriate sudo rights where indicated.*