# OpenClaw Mesh Infrastructure Deep Audit

**Date:** 2026-02-16 (03:00–05:30 UTC)  
**Auditor:** System Architect Agent  
**Scope:** Full mesh (Nexus 10.0.0.1, Clawd 10.0.0.2, Brutus 10.0.0.3, Plutos 10.0.0.4)  
**Methodology:** Local diagnostics + remote SSH (non-sudo) + port scanning

---

## Executive Summary

🔴 **Overall Health: 5/10** (Critical security exposures, configuration drift, but connectivity solid)

The mesh is **operational** with all nodes reachable and WireGuard tunnels up. However, **Ollama APIs are exposed to the internet** (no auth, 0.0.0.0:11434), **no firewall** exists on any node, and **OpenClaw gateways are bound to loopback** on all nodes, preventing remote agent coordination. SSH configuration is inconsistent (only Nexus uses desired mesh port 2222). Resource utilization is healthy across the board. Fail2ban is active on Clawd/Brutus/Plutos but missing on Nexus.

**vs Previous Day (2026-02-15):** No prior automated full audit to compare; earlier manual report noted similar issues. Slight improvement: SSH now active on Brutus/Plutos (previously reported as inactive). Critical exposures (Ollama) unchanged.

---

## 1. Mesh Health

### 1.1 Connectivity & Latency

| Node     | Mesh IP   | Ping RTT (ms) | Status | wg0 iface |
|----------|-----------|---------------|--------|-----------|
| Nexus    | 10.0.0.1  | 14 avg        | ✅     | UP        |
| Clawd    | 10.0.0.2  | 0.04 avg      | ✅     | UP        |
| Brutus   | 10.0.0.3  | 24 avg        | ✅     | UP        |
| Plutos   | 10.0.0.4  | 12.5 avg      | ✅     | UP        |

- **WireGuard**: Interface `wg0` is UP on all nodes.
- **No packet loss** observed in 20-ping samples per node.
- **Configuration discovery**: No `/etc/wireguard/wg0.conf` found on any node. WireGuard likely managed via alternative method (e.g., network manager or custom script). Recommend documenting setup.

**Conclusion**: Mesh connectivity is excellent.

---

## 2. Services

### 2.1 SSH Daemon

| Node     | Service Status | Port(s) Listening | Desired (2222) |
|----------|----------------|-------------------|----------------|
| Nexus    | active         | 0.0.0.0:2222      | ✅ (already)   |
| Clawd    | active         | 0.0.0.0:22        | ❌              |
| Brutus   | active         | 0.0.0.0:22        | ❌              |
| Plutos   | active         | 0.0.0.0:22        | ❌              |

- Clawd: Also listening on [::]:22.
- Brutus: Also listening on 10.0.0.3:22000 (Syncthing, unrelated).
- All nodes allow user `boss` via `AllowUsers` (verified on Clawd; assume others consistent).
- SSH connectivity verified from Clawd to all nodes via host aliases.

**Issue**: Inconsistent SSH port undermines mesh admin uniformity and forces fallback to port 22 (standard, more exposed).

### 2.2 Ollama API

| Node     | Service Status | Port 11434 | Binding  | Auth |
|----------|----------------|------------|----------|------|
| Clawd    | listening      | open       | 0.0.0.0  | ❌   |
| Brutus   | listening      | open       | 0.0.0.0  | ❌   |
| Plutos   | listening      | open       | 0.0.0.0  | ❌   |

- Verified via `ss` and `nc` from Clawd.
- All nodes accept connections from any source, including the public internet (if routed).
- Models detected (from OpenClaw config):
  - Clawd: `mistral:7b-instruct-v0.3-q4_K_M`
  - Brutus: `qwen2.5-coder:3b`
  - Plutos: `llama3.1:8b-instruct-q4_K_M`

**Critical Risk**: Unauthenticated inference API exposed to the internet. Allows anyone to query models, potentially leading to:
- Data exfiltration via prompts
- Computational abuse (costly tokens, if external provider)
- Lateral reconnaissance if combined with other vulnerabilities.

### 2.3 OpenClaw Gateway

| Node     | Service Status    | Port 18789 | Binding  | Remote Access |
|----------|-------------------|------------|----------|---------------|
| Clawd    | active (user)     | LISTEN     | 127.0.0.1| ❌            |
| Brutus   | active (user)     | LISTEN     | 127.0.0.1| ❌            |
| Plutos   | active (user)     | LISTEN     | 127.0.0.1| ❌            |
| Nexus    | not installed     | —          | —        | —             |

- Configuration: `~/.openclaw/openclaw.json` contains `"gateway": { "bind": "loopback", "mode": "local" }` on all three nodes.
- `openclaw gateway status` works locally, but `openclaw cron list` **hangs** (gateway API timeout). Indicates potential stability issue.
- The loopback binding **prevents any remote agent** (including other mesh nodes) from connecting to the gateway. This defeats the purpose of a distributed-agent architecture unless all agents are strictly local to each node.

**Recommendation**: Decide on gateway topology:
  - Option A: **Single shared gateway** on Clawd (or dedicated node) bound to `0.0.0.0` or mesh IP, other nodes disable gateway service.
  - Option B: **Per-node local gateways** bound to mesh interface (0.0.0.0) to allow remote agent connections when needed. Do not keep loopback-only unless agents are strictly co-located.

### 2.4 Fail2Ban

| Node     | Status   | Enabled |
|----------|----------|---------|
| Clawd    | active   | yes     |
| Brutus   | active   | yes     |
| Plutos   | active   | yes     |
| Nexus    | inactive | no      |

- Clawd protectors: SSH (and possibly others) – verified locally.
- Nexus lacks fail2ban entirely – should be installed if SSH exposed (even on mesh).

---

## 3. Security

### 3.1 Firewall Status

| Node     | ufw/nft installed? | Default Policy | Mesh allow rules |
|----------|---------------------|----------------|------------------|
| Clawd    | not detected        | –              | –                |
| Brutus   | not detected        | –              | –                |
| Plutos   | not detected        | –              | –                |
| Nexus    | not detected        | –              | –                |

- **No firewall** on any node. All ports are open to any source (subject only to application-level bind restrictions).
- Coupled with exposed Ollama (0.0.0.0:11434), this is a **critical exposure**.

### 3.2 Exposed Ports Summary (Public Interface Perspective)

On Clawd (public IP 85.215.46.147), the following services listen on `0.0.0.0`:
- `22/tcp` – SSH (standard port)
- `11434/tcp` – Ollama (unauthenticated)
- `3000/tcp` – Unidentified; likely a dev server
- `9100/tcp` – Possibly Prometheus node exporter or metrics
- `9092/tcp` – Unidentified

Brutus and Plutos expose at least `22/tcp` (SSH) to all interfaces.

**Note**: Ports bound to `0.0.0.0` are reachable from the public internet unless blocked by an external firewall (e.g., cloud provider security group). IONOS VPS typically allows inbound unless restricted. **Verify and restrict immediately.**

### 3.3 Configuration Permissions

- OpenClaw config `~/.openclaw/openclaw.json` contains sensitive API keys (NVIDIA, BRAVE). Permissions: `600` (owner only) ✓
- SSH host keys: standard `/etc/ssh/ssh_host_*` 600/640 ✓
- No evidence of world-readable private keys.

---

## 4. Configuration Drift

| Item                      | Desired State                                | Observed State(s)                                  | Drift |
|---------------------------|----------------------------------------------|----------------------------------------------------|-------|
| SSH port                  | 2222 on **all** nodes (mesh admin)          | Nexus:2222; Clawd:22; Brutus:22; Plutos:22        | ❌    |
| OpenClaw gateway bind     | `0.0.0.0` **or** mesh IP for remote access | `loopback` on Clawd/Brutus/Plutos (all)           | ❌    |
| Ollama bind               | `127.0.0.1` **or** mesh CIDR only           | `0.0.0.0` on all inference nodes                 | ❌    |
| Firewall                  | ufw/nft enabled, default deny, mesh allow   | Not installed on any node                         | ❌    |
| Fail2ban                  | active on **all** exposed nodes             | Nexus: inactive                                   | ❌    |
| WireGuard config location | `/etc/wireguard/wg0.conf` managed            | Not found; wg0 UP but config location unclear    | ⚠️    |
| SSH service status        | active on all nodes                         | All active ✓ (improved vs earlier report)        | ✅    |

**WireGuard mystery**: All nodes have `wg0` UP, but no standard config file. Could indicate management by network manager, cloud-init, or custom script. Recommend normalizing to `/etc/wireguard/` for consistency and backup.

---

## 5. Resource Utilization

| Node     | RAM Total | Used | Free | Cache | Avail | Disk Total | Used | Free | %Used |
|----------|-----------|------|------|-------|-------|------------|------|------|-------|
| Nexus    | 941M      | 91M  | 728M | 122M  | 719M  | 9.1G       | 686M | 8.1G | 8%    |
| Clawd    | 15Gi      | 1.6Gi| 4.7Gi| 9.6Gi | 14Gi  | 464G       | 32G  | 432G | 7%    |
| Brutus   | 7.7Gi     | 1.4Gi| 3.3Gi| 3.3Gi | 6.3Gi | 232G       | 12G  | 220G | 5%    |
| Plutos   | 31Gi      | 1.3Gi| 25Gi | 5.3Gi | 29Gi  | 464G       | 32G  | 433G | 7%    |

- **CPU**: Not collected (requires sudo). No indication of saturation from memory pressure.
- **Disk**: All nodes well under 10% usage; Clawd disk space is plentiful contrary to previous report (which showed 434G used – that data is stale).
- **Memory**: All nodes have >80% available. Healthy.

---

## 6. High Availability & Redundancy

| Component              | Current Redundancy | Risk Level | Notes |
|------------------------|--------------------|------------|-------|
| OpenClaw Gateway       | 3 instances (loopback only) | HIGH | All bound to 127.0.0.1 → remote agents cannot use them. Effectively zero remote gateway capacity. |
| Telegram Bot           | Single instance on Clawd (assumed) | HIGH | If Clawd goes down, Telegram notifications stop. |
| Fastmail SMTP          | Single provider | MEDIUM | Standard email provider dependency. |
| SSH Access (Mesh)      | Multi-node but mixed port config | MEDIUM | Nexus on 2222 good; others on 22 – less consistent but still accessible. |
| WireGuard Hub (Nexus)  | Single node | MEDIUM | Nexus is the only hub with 1GB RAM; failure would disrupt mesh. Consider secondary hub. |
| Ollama (Inference)     | Distributed across 3 nodes | LOW | Each node can serve models independently; no single point for inference. |
| NVIDIA API (kimi)      | Single external key | MEDIUM | Rate-limit or rotate key; monitor usage. |

**Recommendation**: Add a secondary WireGuard hub (could be Brutus or Plutos) with identical configuration and a floating IP or DNS failover. Also implement redundant OpenClaw gateway instance on a separate node, bound to mesh interface.

---

## 7. Cost Optimization

- **Model Usage**: Primary models are free-tier via OpenRouter (step-3.5-flash, mimo) and local Ollama (CPU). ✅ Good.
- **Paid Models**: `nvidia-direct/moonshotai/kimi-k2.5` appears in config; also `openrouter/moonshotai/kimi-k2.5`. These incur cost. Evaluate if free alternatives (e.g., local llama3-plutos) can substitute for reasoning tasks.
- **Infrastructure**: 4 VPS nodes (~$25–30/month total). Resources underutilized; could potentially consolidate, but distributed inference benefits justify current setup.

No runaway API usage detected in session logs.

---

## 8. Backup + Recovery

**Status**: Not implemented for system configuration.

- Only `~/.openclaw/openclaw.json.backup` exists.
- No backups of:
  - `/etc/ssh/` (host keys, config)
  - `/etc/wireguard/` (or wg state)
  - `/etc/ollama/` (model configuration)
  - systemd units
  - ufw/nft rules (once deployed)
  - Fail2ban jails
- **Risk**: Loss of any node could require lengthy reconfiguration from scratch, especially WireGuard and SSH keys.

**Action**: Create nightly backup job via OpenClaw cron or systemd timer to tar critical configs into workspace memory and optionally push to remote storage.

---

## 9. Top 5 Recommendations

### 1. Restrict Ollama API to Localhost or Mesh CIDR (CRITICAL)
**Why**: Prevents unauthenticated internet access to inference APIs.

**Commands (per inference node)**:
```bash
# Create systemd override
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/override.conf <<EOF
[Service]
Environment="OLLAMA_HOST=127.0.0.1"
EOF
sudo systemctl daemon-reload
sudo systemctl restart ollama
```
*Alternative*: bind directly to mesh CIDR `10.0.0.0/24` instead of localhost if remote nodes need access (they already do via mesh IPs). Set `OLLAMA_HOST=10.0.0.x:11434` accordingly.

**Verify**: `ss -tuln | grep 11434` should show `127.0.0.1:11434` (or `10.0.0.x:11434`) only.

### 2. Deploy Firewall on All Nodes (HIGH)
**Why**: Default-deny reduces attack surface; restricts services to mesh subnet only.

**Commands**:
```bash
sudo apt-get update && sudo apt-get install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
# Allow mesh subnet for management
sudo ufw allow from 10.0.0.0/24 to any port 2222 proto tcp  # SSH (after port change)
sudo ufw allow from 10.0.0.0/24 to any port 11434 proto tcp # Ollama (if bound to mesh or localhost, may skip)
sudo ufw allow from 10.0.0.0/24 to any port 18789 proto tcp # OpenClaw gateway (after rebinding)
sudo ufw --force enable
```

**Note**: After applying, verify you can still SSH via port 2222 before locking out. Keep a recovery console handy (IONOS VPS console access).

### 3. Standardize SSH on Mesh Port 2222 (HIGH)
**Why**: Consistency, avoids conflicts with standard SSH port, and aligns with mesh design.

**Commands (on each node except Nexus which already uses 2222)**:
```bash
sudo sed -i 's/^#Port 22/Port 2222/' /etc/ssh/sshd_config
sudo sed -i 's/^Port 22/Port 2222/' /etc/ssh/sshd_config 2>/dev/null || true
sudo grep -q '^Port 2222' /etc/ssh/sshd_config || echo "Port 2222" | sudo tee -a /etc/ssh/sshd_config
# Ensure PasswordAuthentication no (already implied)
sudo systemctl restart ssh
```
Then update firewall rules (step 2) to allow 2222 instead of 22.

**Verify**: `ss -tuln | grep 2222` shows LISTEN.

### 4. Rebind OpenClaw Gateway to Mesh Interface (HIGH)
**Why**: Enables remote agents on other nodes to connect; required for distributed agent coordination.

**Commands (on Clawd, Brutus, Plutos)**:
```bash
# Edit ~/.openclaw/openclaw.json
# Change "bind": "loopback" to "bind": "0.0.0.0" (or specific mesh IP e.g., 10.0.0.2)
jq '.gateway.bind = "0.0.0.0"' ~/.openclaw/openclaw.json > tmp.json && mv tmp.json ~/.openclaw/openclaw.json
# Restart gateway
openclaw gateway restart   # or: systemctl --user restart openclaw-gateway
```
**Verify**: `ss -tuln | grep 18789` shows `0.0.0.0:18789` (or `10.0.0.x:18789`).

**Stability note**: `openclaw cron list` hangs; monitor logs at `/tmp/openclaw/openclaw-*.log`; investigate if persists after rebinding.

### 5. Implement Automated Configuration Backups (MEDIUM)
**Why**: Enables rapid recovery from configuration loss or node rebuild.

**Implementation**:
Create script `/home/boss/bin/backup-configs.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/home/boss/.openclaw/workspace/backups/$(date +%Y-%m-%d)"
mkdir -p "$BACKUP_DIR"
# System configs (may need sudo; configure passwordless NOPASSWD for these commands in sudoers)
sudo tar czf "$BACKUP_DIR/etc-ssh.tar.gz" /etc/ssh 2>/dev/null || true
sudo tar czf "$BACKUP_DIR/etc-wireguard.tar.gz" /etc/wireguard 2>/dev/null || true
sudo tar czf "$BACKUP_DIR/etc-ollama.tar.gz" /etc/ollama 2>/dev/null || true
sudo tar czf "$BACKUP_DIR/etc-systemd.tar.gz" /etc/systemd/system/openclaw* 2>/dev/null || true
# OpenClaw workspace
tar czf "$BACKUP_DIR/openclaw-home.tar.gz" /home/boss/.openclaw 2>/dev/null
# Retention: keep last 7 days
find /home/boss/.openclaw/workspace/backups -mindepth 1 -maxdepth 1 -type d -mtime +7 -exec rm -rf {} \;
```
Make executable and add to OpenClaw daily cron (via `openclaw cron add`) or systemd timer.

**Important**: Ensure backup directory is included in memory compaction or pushed to remote storage.

---

## 10. Additional Observations & Next Steps

- **Orphan WireGuard peer**: Previous audit mentioned `10.0.0.5` on Nexus. Not verified (requires `wg show`). Run manually on Nexus: `sudo wg show` and remove any stale peers.
- **Cron job errors**: Several OpenClaw cron jobs show error status. Investigate via `openclaw cron runs <jobid>` once cron API is responsive.
- **Unidentified services**: Ports 3000, 9100, 9092 on Clawd listening on all interfaces. Identify and either secure or remove.
- **Syncthing**: Port 22000 on Clawd (10.0.0.2:22000) listening on all interfaces; ensure intended and secured.
- **OpenClaw cron timeout**: `openclaw cron list` hangs. Check `/tmp/openclaw/openclaw-2026-02-16.log` for errors. May indicate gateway overload or API deadlock.
- **Nexus security hardening**: As the WireGuard hub, Nexus should also have fail2ban and firewall enabled. Currently lacks both.
- **Gateway redundancy**: Consider designating a dedicated gateway node (maybe Plutos due to 32GB) with HA failover.

**Immediate actions (today)**:
1. Lock down Ollama (rec. #1) on all inference nodes.
2. Enable ufw and allow only mesh CIDR (rec. #2).
3. Change SSH to 2222 (rec. #3).
4. Rebind OpenClaw gateway (rec. #4) – test remote agent connectivity after.
5. Install fail2ban on Nexus.

**This week**:
- Implement config backups (rec. #5).
- Clean up WireGuard peer config.
- Audit cron jobs and fix failing ones.
- Identify services on ports 3000/9100/9092.
- Document WireGuard setup method.

---

**Report generated**: 2026-02-16 05:30 UTC  
**Next audit**: 2026-02-17 03:00 UTC (daily)
