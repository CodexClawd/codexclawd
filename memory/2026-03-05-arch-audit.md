# OpenClaw Mesh Infrastructure Audit Report
**Date:** 2026-03-05
**Auditor:** System Architect Agent (cron: daily-3am-arch-audit)
**Scope:** Full mesh of 4 nodes (Nexus 10.0.0.1, Clawd 10.0.0.2, Brutus 10.0.0.3, Plutos 10.0.0.4)

---

## Executive Summary

**Overall Health Score:** 5/10
**Trend:** ↑ Slight improvement (from 5/10 on 2026-03-04; note: yesterday's score was 5/10 after recovery from outage)

The mesh infrastructure remains **operational but insecure**. All nodes are reachable via WireGuard and Ollama APIs are responsive. However, **critical security misconfigurations remain unaddressed** from the previous day, including secret exposure, unnecessary gateway duplication, lack of firewall, and missing Ollama models. Minor improvements have been made: SSH password authentication is now disabled on Clawd, `fail2ban` is installed and running, and baseline snapshots are available for drift detection.

**Priority Issues:**
1. **Critical secret exposure** – `openclaw.json` on Clawd is world-readable (0664) and contains plaintext API keys (NVIDIA, Brave). Unchanged.
2. **Gateway token exposure** – `openclaw-gateway.service` files on all gateway nodes are world-readable (0664), exposing tokens. Unchanged.
3. **Unnecessary gateway duplication** – Brutus and Plutos likely still run OpenClaw gateway instances; only Clawd should be primary. No evidence of remediation.
4. **Ollama API exposed to mesh/internet** – All inference nodes bind Ollama to `0.0.0.0:11434` without firewall or authentication. Unchanged.
5. **No host firewall** – `nftables` ruleset is empty; default policy likely ACCEPT. SSH and Ollama are exposed to the internet on nodes with public IPs. Unchanged.
6. **Model gaps** – Clawd missing `qwen2.5-coder:3b`; Plutos missing `qwen14b`. This forces fallback to external paid APIs. Unchanged.
7. **Version drift** – Clawd runs Ollama 0.15.5 while Brutus/Plutos run 0.16.1 (assumed from previous data). Unchanged.
8. **SSH hardening incomplete** – Clawd: password auth now disabled (improvement), but still listening on port 22 and all interfaces (`0.0.0.0`). No change on other nodes.
9. **Baseline files present but not used for alerting** – Baselines exist in `memory/baselines/` but the automated drift detection is not integrated into the daily audit.
10. **WireGuard service not managed** – On Clawd (and likely Brutus), `wg-quick@wg0` service is inactive; interfaces remain up due to manual start or other mechanisms. This risks loss of mesh on reboot.

---

## Mesh Health

### Connectivity Summary (snapshot 2026-03-05T02:01:48Z from sentinel)

| Target    | Status | Ping (ms) | Ollama API | Notes |
|-----------|--------|-----------|------------|-------|
| 10.0.0.1  | UP     | 14.5      | N/A        | Nexus (security hub) |
| 10.0.0.2  | UP     | 0.04      | UP         | Clawd (gateway) |
| 10.0.0.3  | UP     | 24.4      | UP         | Brutus (coding) |
| 10.0.0.4  | UP     | 12.6      | UP         | Plutos (heavy inference) |

- **WireGuard** (local check on Clawd):
  - Interface `wg0`: UP, IP 10.0.0.2/24.
  - Service `wg-quick@wg0`: Loaded but **inactive (dead)**. This is a regression risk; the interface is up but not managed by systemd, so it may not survive reboot or network restart.
  - **Other nodes**: Could not verify due to SSH access failure; assume similar to previous day (Brutus service dead, Plutos active-exited, Nexus on Alpine with wg-quick unavailable). Recommend urgent verification.

- **Alert history**: No alerts generated overnight (last alerts from March 3). Sentinel confirms all nodes and Ollama APIs operational.

### Recovery / Stability
The mesh has been stable since the March 3 outage. No packet loss or latency spikes detected in the current sampling.

**Immediate Fixes:**
```bash
# On Clawd and Brutus (enable wg-quick; check if wg-quick package is installed)
sudo systemctl enable --now wg-quick@wg0
# If systemd is not used (e.g., Nexus), ensure wg-quick equivalent or add to rc.local
# Verify:
sudo wg show
```

---

## Services

### OpenClaw Gateway

**Local node (Clawd):**
- Status: `active (running)` (PID 1475912)
- Version: `2026.2.3-1` (older than Brutus/Plutos reported at `2026.2.9`)
- Memory: 6.1G (peak 8.7G)
- Control ports: 127.0.0.1:18789, 18792 (good – bound to localhost)
- Telegram plugin: Not verified; assumed enabled (as per previous audit). Duplication across nodes likely persists.

**Remote nodes (Brutus, Plutos):**
- Status: **Could not verify** (SSH connections to port 22 failed from this agent; credentials issue). Sentinel does not check gateway process.
- **Assumption**: Based on March 4 report, both were running gateway instances and should be disabled to avoid duplicate Telegram bots and reduce attack surface.

**Remediation:**
```bash
# Disable gateway on Brutus and Plutos (as root or via sudo)
ssh brutus 'systemctl --user disable --now openclaw-gateway'
ssh plutos 'systemctl --user disable --now openclaw-gateway'
# Verify only Clawd runs the gateway for external channels.
```

### SSH Daemon

**Clawd:**
- Port: `22` (default; should be `2222`)
- ListenAddress: `0.0.0.0` (all interfaces; should be mesh IP only)
- PasswordAuthentication: `no` (improved!)
- PubkeyAuthentication: `yes`
- fail2ban: `running` (since Feb 20), with `jail.d` config enabling `sshd`. ✅ Partial improvement.

**Remote nodes:**
- Unknown. Assume same pre-hardening state (port 22, bind all, password auth possibly enabled).

**Hardening Commands (apply to all nodes):**
```bash
# Change port to 2222
sed -i 's/^#Port 22/Port 2222/' /etc/ssh/sshd_config
# Bind to mesh IP (determine based on hostname)
MY_MESH_IP="10.0.0.$(hostname -s | sed 's/nexus/1/;s/clawd/2/;s/brutus/3/;s/plutos/4/')"
sed -i "s/^#ListenAddress 0.0.0.0/ListenAddress $MY_MESH_IP/" /etc/ssh/sshd_config
# Ensure password auth disabled
sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd
# Install/enable fail2ban if missing
apt-get install -y fail2ban
systemctl enable --now fail2ban
```

### Ollama API

**Model inventory (via API):**

| Node   | Available Models                              | Missing Models            |
|--------|-----------------------------------------------|---------------------------|
| Clawd  | `mistral:7b-instruct-v0.3-q4_K_M`            | `qwen2.5-coder:3b`        |
| Brutus | `qwen2.5-coder:3b`                            | –                         |
| Plutos | `llama3.1:8b-instruct-q4_K_M`                | `qwen14b` (e.g., `qwen2.5:14b`) |

**Version (local on Clawd):** `0.15.5` (expected: `0.16.1` across all nodes).

**Bind address:** `0.0.0.0:11434` on all inference nodes (confirmed on Clawd). This exposes the API to the internet.

**Remediation:**
```bash
# Pull missing models
# On Clawd:
ollama pull qwen2.5-coder:3b
# On Plutos:
ollama pull qwen2.5:14b   # adjust variant as needed
# Upgrade Ollama on Clawd to match others
apt-get update && apt-get install -y ollama   # will upgrade to latest
# Harden network binding (choose one):
# Option A - Bind to localhost (if agents connect locally):
sed -i 's/^OLLAMA_HOST=.*/OLLAMA_HOST=127.0.0.1/' /etc/default/ollama  # or appropriate config
# Option B - Keep mesh binding but restrict via firewall (see Security section)
systemctl --user restart ollama   # or: systemctl restart ollama
```

---

## Security

### File Permissions – Sensitive Credentials

| File                                          | Node   | Perms   | Risk  | Notes |
|-----------------------------------------------|--------|---------|-------|-------|
| `~/.openclaw/openclaw.json`                   | Clawd  | 0664    | **CRITICAL** | Contains NVIDIA_API_KEY, BRAVE_API_KEY, gateway/Telegram tokens in plaintext. |
| `~/.config/systemd/user/openclaw-gateway.service` | Clawd | 0664    | **CRITICAL** | `Environment=OPENCLAW_GATEWAY_TOKEN=...` exposes token. |
| `~/.openclaw/` (directory)                   | Clawd  | 0700    | OK    | – |
| `~/.openclaw/` (dir) – remote nodes?         | unknown| (assume 755) | MED | |

**Remediation (apply to all affected nodes):**
```bash
# 1. Restrict openclaw.json to 600
chmod 600 ~/.openclaw/openclaw.json

# 2. Move gateway tokens to dedicated env file with strict perms
mkdir -p ~/.openclaw/conf
jq -r '.gateway.auth.token' ~/.openclaw/openclaw.json > ~/.openclaw/conf/gateway.env
chmod 600 ~/.openclaw/conf/gateway.env

# 3. Remove token from systemd unit and reference env file
sed -i '/Environment=OPENCLAW_GATEWAY_TOKEN/d' ~/.config/systemd/user/openclaw-gateway.service
echo 'EnvironmentFile=%h/.openclaw/conf/gateway.env' >> ~/.config/systemd/user/openclaw-gateway.service
chmod 600 ~/.config/systemd/user/openclaw-gateway.service

# 4. Tighten .openclaw directory perms if needed
chmod 700 ~/.openclaw

# 5. Reload and restart gateway
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway
```

### Firewall – Missing Entirely

- **nftables** configuration (`/etc/nftables.conf`) is a skeleton with no rules. Default policy likely ACCEPT.
- All ports (22, 11434, 4330, 44321, etc.) are exposed to the internet on nodes with public IPs (Clawd: 85.215.46.147).
- **fail2ban** is installed and running on Clawd, which will add dynamic rules for SSH under its own chain. However, base firewall still allows all inbound; fail2ban only adds reject rules after bans. A default-drop policy is required.

**Recommended nftables ruleset (apply to all nodes):**
```bash
sudo nft flush ruleset
sudo nft add table inet filter
sudo nft 'add chain inet filter input { type filter hook input priority 0; policy drop; }'
sudo nft add rule inet filter input ct state established,related accept
# Allow mesh CIDR (10.0.0.0/24) for SSH and WireGuard
sudo nft add rule inet filter input ip saddr 10.0.0.0/24 tcp dport 2222 accept   # SSH hardened port
sudo nft add rule inet filter input ip saddr 10.0.0.0/24 udp dport 51820 accept # WireGuard
# Allow SSH from trusted management IPs if needed (example)
# sudo nft add rule inet filter input ip saddr <YOUR_MGMT_IP> tcp dport 2222 accept
# Allow Ollama only from mesh if binding to mesh interface; if bound to localhost, no rule needed
sudo nft add rule inet filter input ip saddr 10.0.0.0/24 tcp dport 11434 accept
# Allow loopback
sudo nft add rule inet filter input iif lo accept
# Optional: allow ICMP echo from mesh
sudo nft add rule inet filter input ip saddr 10.0.0.0/24 icmp type echo-request accept
# Save and enable
sudo nft list ruleset > /etc/nftables.conf
sudo systemctl enable --now nftables
```

### Other Security Gaps

- **sudoers** – Not audited due to lack of root access; requires review to ensure least privilege.
- **Exposed services** – Ports `4330` and `44321` on Clawd are listening on `0.0.0.0`. Identify owning processes and restrict via firewall or bind to localhost. (Likely Syncthing, Prometheus exporters, or custom agents.)
- **Ollama network exposure** – Should be bound to `127.0.0.1` if agents use localhost providers; current `0.0.0.0` is dangerous.
- **SSH brute-force** – `fail2ban` is running on Clawd; ensure it is also installed and configured on Brutus, Plutos, and Nexus.

---

## Configuration Drift

| Component                     | Desired State (Target)                                          | Observed (2026-03-05)                                 | Severity |
|-------------------------------|-----------------------------------------------------------------|-------------------------------------------------------|----------|
| **WireGuard**                 | wg0 up, peers connected, service enabled & managed             | Clawd: wg0 UP but service dead; others unknown      | 🔴 Critical |
| **OpenClaw gateway instances**| Only Clawd runs gateway                                          | Brutus & Plutos likely still running (unverified)   | 🔴 Critical |
| **OpenClaw version**          | Consistent across all gateway nodes                             | Clawd 2026.2.3-1 vs others 2026.2.9 (from prev)    | 🟡 Medium |
| **Ollama models – Clawd**     | mistral **and** qwen2.5-coder:3b                                | Only mistral present                                 | 🔴 Critical |
| **Ollama models – Plutos**    | llama3.1:8b **and** qwen14b                                     | Only llama3.1:8b present                             | 🔴 Critical |
| **Ollama version**            | All nodes on 0.16.1                                             | Clawd 0.15.5                                         | 🟡 Medium |
| **Ollama bind address**       | 127.0.0.1 (or firewall mesh-only)                              | 0.0.0.0 on all inference nodes                      | 🔴 Critical |
| **openclaw.json perms**       | 600                                                             | Clawd 664                                            | 🔴 Critical |
| **gateway.service perms**     | 600                                                             | Clawd 664                                            | 🔴 Critical |
| **~/.openclaw perms**         | 700                                                             | Clawd OK; others unknown (assume 755)               | 🟡 Medium |
| **SSH hardening**             | Port 2222, bind to mesh IP, disable password, fail2ban active  | Clawd: port 22, bind 0.0.0.0, pwd disabled, fail2ban running | 🔴 Critical |
| **Telegram plugin**           | Enabled only on primary gateway (Clawd)                        | Likely still enabled on all three                   | 🔴 Critical |
| **Baseline capture**          | Baseline snapshots available for drift detection               | Baselines exist in `memory/baselines/` (populated) | ✅ Improved |

---

## Resource Utilization

| Node   | CPU Cores | Memory Total | Used | Load Avg (1m) | Disk Total | Used | FS Use% | Notes |
|--------|-----------|--------------|------|---------------|------------|------|---------|-------|
| Clawd  | 8         | 15 GiB       | 2.1 GiB | 0.01       | 464 GiB    | 31 GiB | 7%      | Excellent headroom |
| Nexus  | (unknown) | (unknown)    | (unknown) | –         | 9.1 GiB    | 687 MiB | 8% (prev) | Limited but sufficient |
| Brutus | (unknown) | (unknown)    | (unknown) | –         | 232 GiB    | 12 GiB | 5% (prev) | Good |
| Plutos | (unknown) | (unknown)    | (unknown) | –         | 464 GiB    | 32 GiB | 7% (prev) | Excellent |

- **Clawd**: No saturation risks. Load average negligible.
- Remote nodes: Could not fetch live stats; assume similar to previous day.

---

## Cost & High Availability

### Single Points of Failure

1. **Primary gateway dependency** – Only Clawd should be the designated gateway for external channels. If Clawd fails and others have gateway disabled, channel connectivity is lost until manual failover. Recommend:
   - Keep gateway disabled on Brutus/Plutos (as above).
   - Implement a quick-failover script that promotes one of the worker nodes to gateway if Clawd becomes unresponsive for >N minutes.
2. **Node capacity** – Losing any node reduces specialized capacity (security, coding, heavy inference). Consider adding a fifth node for redundancy if budget allows.

### Cost Optimization

- **Free-tier models**: Default `openrouter/stepfun/step-3.5-flash:free` is in use – good.
- **Local inference**: Ollama models are self-hosted and free. However, missing local models (`qwen-coder` on Clawd, `qwen14b` on Plutos) force fallback to paid providers (NVIDIA, OpenRouter) for certain tasks. Completing the model portfolio will reduce external API costs.
- **Runaway API keys**: NVIDIA_API_KEY and BRAVE_API_KEY are present. Monitor usage dashboards and set hard limits. Consider migrating to a vault-based secret distribution system (HashiCorp Vault, 1Password).
- **Telegram bot duplication** – Not a direct cost, but wastes resources and may lead to rate-limit issues if multiple bots are added to the same group.

---

## Backup + Recovery

- **Workspace backup**: `maintenance/daily_backup.sh` runs daily at 02:00 and commits changes to git (origin & backup remotes). This backs up all workspace files but **excludes critical system configurations** (`/etc/wireguard`, `/etc/ollama`, systemd units, firewall rules).
- **Baseline snapshots**: Present in `memory/baselines/` (text format) and `memory/*_baseline_*.json`. These capture permissions and network state as of Feb 20–21. They can be used for drift detection but are not integrated into automated daily checks.
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
git add "$CONFIG_BACKUP_DIR"
```

---

## Top 5 Recommendations (Actionable)

### 1. Secure OpenClaw Secrets and Permissions (URGENT)
**Risk**: Critical API keys and tokens are world-readable on Clawd.  
**Action**: Apply remediation steps now; replicate across all nodes where gateway runs.

```bash
chmod 600 ~/.openclaw/openclaw.json
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
**Action**: Stop and disable `openclaw-gateway` on Brutus and Plutos; keep only on Clawd.

```bash
# TODO: Verify SSH credentials to remote nodes; if broken, fix SSH keys first.
ssh brutus 'systemctl --user disable --now openclaw-gateway'
ssh plutos 'systemctl --user disable --now openclaw-gateway'
# Verify: on those nodes, only openclaw-node should run
```

### 3. Harden Network Firewall (URGENT)
**Risk**: All services exposed to internet; SSH and Ollama directly reachable.  
**Action**: Deploy nftables with mesh-only allow rules and drop-all-else policy (see full ruleset above).

```bash
# Distribute and apply the nftables ruleset to all nodes (requires root).
# Ensure to allow SSH on the new port 2222 from your management IPs, not from 0.0.0.0.
```

### 4. Complete Ollama Model Portfolio and Version Alignment
**Risk**: Missing models trigger fallback to paid APIs; version drift may cause incompatibilities.  
**Action**:
```bash
# On Clawd:
ollama pull qwen2.5-coder:3b
sudo apt-get update && sudo apt-get install -y ollama   # upgrade to 0.16.1
# On Plutos:
ollama pull qwen2.5:14b
# Consider binding Ollama to 127.0.0.1 and updating openclaw provider URLs accordingly.
```

### 5. Harden SSH and Ensure fail2ban Coverage across All Nodes
**Risk**: Brute-force attacks on exposed SSH port 22; some nodes may lack fail2ban.  
**Action**:
```bash
# On all nodes (as root):
sed -i 's/^#Port 22/Port 2222/' /etc/ssh/sshd_config
# Set ListenAddress to mesh IP (script above)
sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd
# Install and enable fail2ban if not present
apt-get install -y fail2ban
systemctl enable --now fail2ban
# Verify jail status: fail2ban-client status sshd
```

---

## Additional Notes

- **Sentinel monitoring** is functional and provided connectivity checks. The script could be enhanced to include wg-quick service status, firewall validation, and gateway process checks (e.g., via `systemctl --user is-active` over SSH if keys are fixed).
- **Baseline capture** exists but is not integrated into daily audits. Consider adding a drift check step that compares current permissions/network listeners against baselines and reports deviations.
- **OpenClaw config**: Review provider configurations; prefer `127.0.0.1` for local Ollama to avoid mesh-wide exposure.
- **Root access**: The System Architect agent currently lacks passwordless sudo, preventing full verification of system-level configurations (firewall, processes, sudoers). Arrange appropriate sudo privileges (NOPASSWD for specific commands) to enable complete audits.
- **WireGuard auto-start**: Ensure `wg-quick@wg0` is enabled on all nodes that use it. For non-systemd nodes (e.g., Nexus), add to appropriate startup scripts.

---

*Report generated by System Architect Agent on 2026-03-05T02:30:00Z. All commands assume appropriate privileges (sudo where indicated).*
