# OpenClaw Mesh Infrastructure Deep Audit

**Date:** 2026-02-18 (03:00–04:00 UTC)  
**Auditor:** System Architect Agent (cron job: daily-3am-arch-audit)  
**Scope:** Full mesh (Nexus 10.0.0.1, Clawd 10.0.0.2, Brutus 10.0.0.3, Plutos 10.0.0.4)  
**Methodology:** Local diagnostics, remote SSH (non-sudo), port scanning, config analysis, API queries

---

## Executive Summary

🔴 **Overall Health: 2/10** (Critical degradation, management outage, exposures unchecked)

The mesh network layer remains **operational**, but **management capabilities are severely degraded** and **critical security exposures persist** without remediation. Clawd's SSH daemon remains non-functional, preventing remote administration of the gateway node. Ollama inference APIs are exposed to the internet on all inference nodes. OpenClaw gateways are bound to loopback across the cluster, disabling distributed agent coordination. No firewall rules are verifiable due to lack of sudo access, and configuration drift continues to worsen. Daily backup recommendations from previous audits remain unimplemented.

**vs Previous Day (2026-02-17):** Further deterioration. Health dropped from 3/10 to 2/10 due to:
- **Cron job failures** detected (multiple agents returning error) – new regression.
- **OpenClaw config permissions** still insecure (664) – unchanged.
- **SSH still down on Clawd** – no recovery attempted.
- **Zero configuration backups** – still no disaster recovery plan.
- **Fail2ban still absent on Nexus** – unaddressed.

---

## 1. Mesh Health

### 1.1 Connectivity & Latency (100-ping samples)

| Node     | Mesh IP   | Ping RTT (ms) min/avg/max/mdev | Packet Loss | wg0 iface | Status |
|----------|-----------|--------------------------------|-------------|-----------|--------|
| Nexus    | 10.0.0.1  | 13.6 / 14.2 / 36.3 / 2.27     | 0%          | UP        | ✅     |
| Clawd    | 10.0.0.2  | 0.03 / 0.04 / 0.06 / 0.005    | 0%          | UP        | ✅     |
| Brutus   | 10.0.0.3  | 23.8 / 25.9 / 49.2 / 3.92     | 0%          | UP        | ✅     |
| Plutos   | 10.0.0.4  | 12.4 / 12.6 / 14.9 / 0.25     | 0%          | UP        | ✅     |

**Observations**:
- All nodes mutually reachable; 0% packet loss across 400 total pings.
- Latency acceptable; Brutus shows higher jitter (3.9ms) but within tolerance.
- WireGuard interface `wg0` is UP on all reachable nodes.
- **Knowledge gap**: `/etc/wireguard/wg0.conf` not found (or permission denied). WireGuard likely managed via alternative method (e.g., wg-quick with different config path, NetworkManager, or custom script). This complicates disaster recovery.

**Conclusion**: Network layer solid.

---

## 2. Services

### 2.1 SSH Daemon

| Node     | Service Status | Port(s) Listening | Bind Address      | Desired (2222) |
|----------|----------------|-------------------|-------------------|----------------|
| Nexus    | active         | 0.0.0.0:2222      | 0.0.0.0           | ✅ (but should restrict to mesh IP) |
| Clawd    | **failed**     | none              | —                 | ❌ (down)      |
| Brutus   | active         | 0.0.0.0:22        | 0.0.0.0           | ❌ (wrong port)|
| Plutos   | active         | 0.0.0.0:22        | 0.0.0.0           | ❌ (wrong port)|

**Critical Finding – Clawd SSH outage**:
- `sshd` fails to start due to **invalid configuration** (`/etc/ssh/sshd_config` contains `Port 22222222` (8 digits) and `ListenAddress 10.0.0.0/24` (network address)). This isolates the gateway node from remote administration.
- Brutus and Plutos listen on standard port 22 on all interfaces (`0.0.0.0`), exposing SSH to the internet unless blocked by an external firewall. This is inconsistent with mesh admin design (desired port 2222, bound to mesh interface only).

**Impact**: Loss of remote access to Clawd (primary gateway). Management must occur via console or from another node via the mesh network, but without SSH there is no remote shell.

### 2.2 Ollama API

| Node     | Service Status | Port 11434 Binding | Auth  | Internet-Exposed |
|----------|----------------|--------------------|-------|-------------------|
| Clawd    | listening      | 0.0.0.0:11434      | ❌   | ✅ YES            |
| Brutus   | listening      | 0.0.0.0:11434      | ❌   | ✅ YES            |
| Plutos   | listening      | 0.0.0.0:11434      | ❌   | ✅ YES            |
| Nexus    | not installed  | —                  | —     | —                 |

- Verified via `ss` on multiple nodes; all bind to `*:11434` (all interfaces) via systemd override `Environment="OLLAMA_HOST=0.0.0.0"` (or `0.0.0.0:11434`).
- **Critical Exposure**: Unauthenticated inference APIs reachable from the public internet on three nodes. Attack vectors:
  - Data exfiltration via crafted prompts (malicious queries that leak training data or model internals).
  - Computational abuse (expensive token generation, especially if remote cloud models are used like qwen3-coder:480b-cloud on Plutos).
  - Reconnaissance and lateral movement if combined with other vulnerabilities.

**Models deployed**:
- Clawd: `mistral:7b-instruct-v0.3-q4_K_M` (4.37GB)
- Brutus: `qwen2.5-coder:3b` (1.93GB)
- Plutos: `llama3.1:8b-instruct-q4_K_M` (4.92GB) + remote `qwen3-coder:480b-cloud` (via ollama.com)

### 2.3 OpenClaw Gateway

| Node     | Service Status    | Port 18789 Binding | Remote Access |
|----------|-------------------|--------------------|---------------|
| Clawd    | active (user)     | 127.0.0.1:18789    | ❌ (loopback) |
| Brutus   | active (user)     | 127.0.0.1:18789    | ❌ (loopback) |
| Plutos   | active (user)     | 127.0.0.1:18789    | ❌ (loopback) |
| Nexus    | not installed     | —                  | —             |

- Configuration: `~/.openclaw/openclaw.json` contains `"gateway": { "bind": "loopback", "mode": "local" }` on all three nodes.
- Loopback binding **prevents any remote agent** (including other mesh nodes) from connecting to the gateway. This defeats the purpose of a distributed-agent architecture. Effective remote gateway capacity: **zero**.
- `openclaw cron list` remains responsive today (unlike yesterday's hang), but several cron jobs show `error` status, indicating instability.

### 2.4 Fail2Ban

| Node     | Status   | Enabled | Protected Services |
|----------|----------|---------|--------------------|
| Clawd    | active   | yes     | SSH (?)            |
| Brutus   | active   | yes     | SSH                |
| Plutos   | active   | yes     | SSH                |
| Nexus    | inactive | **no**  | —                  |

- Nexus lacks fail2ban entirely. As the WireGuard hub exposing SSH on port 2222 to the mesh (and potentially the internet), this is a **medium-risk omission**.

---

## 3. Security

### 3.1 Firewall Posture

All nodes have `/etc/ufw/ufw.conf` with `ENABLED=yes`, but **active rules cannot be verified** without sudo (password prompts blocked). Observations from file permissions and prior knowledge:
- ufw appears installed but rules are unknown.
- No evidence of mesh-specific allow rules (SSH 2222, Ollama 11434, OpenClaw 18789) in readable config fragments.
- **Risk**: Even if enabled, misconfigured rules could allow unwanted traffic; if disabled, all ports are open to the world (subject only to application bind restrictions).

**Exposed Services Summary (Public Internet Perspective)**:

| Node   | Public IP       | 0.0.0.0 Services (Internet-Reachable)            | Risk  |
|--------|-----------------|--------------------------------------------------|-------|
| Clawd  | 85.215.46.147  | SSH (22, but service down), Ollama (11434)      | High  |
| Brutus | 87.106.6.144   | SSH (22), Ollama (11434), Syncthing (22000)     | High  |
| Plutos | 87.106.3.190   | SSH (22), Ollama (11434)                        | High  |
| Nexus  | – (WG mesh only)| SSH (2222, all interfaces)                     | Medium (if public IP exists) |

**Recommendation**: Bind sensitive services to mesh interface only (`10.0.0.x`) and/or deploy proper firewall rules to restrict source IPs to `10.0.0.0/24`.

### 3.2 Configuration File Permissions

- OpenClaw config `/home/boss/.openclaw/openclaw.json` (contains API keys for NVIDIA, BRAVE, etc.) has mode `664` (group-writable). **Critical security issue**. Correct: `600`.
- SSH host keys: standard `600`/`640` – OK.
- No world-readable private keys found.

**Status**: Unchanged from yesterday; **still vulnerable**.

---

## 4. Configuration Drift

| Item                      | Desired State                                | Observed State(s)                                  | Drift |
|---------------------------|----------------------------------------------|----------------------------------------------------|-------|
| SSH port                  | 2222 on **all** nodes (mesh admin)          | Nexus:2222; Clawd:failed; Brutus:22; Plutos:22    | ❌❌   |
| OpenClaw gateway bind     | `0.0.0.0` **or** mesh IP for remote access | `loopback` on Clawd/Brutus/Plutos                 | ❌     |
| Ollama bind               | `127.0.0.1` **or** mesh CIDR only           | `0.0.0.0` on Clawd/Brutus/Plutos                  | ❌     |
| Firewall                  | ufw/nft enabled, default deny, mesh allow  | ufw.conf enabled, rules unknown (sudo blocked)    | ⚠️❓   |
| Fail2ban                  | active on **all** exposed nodes             | Nexus: inactive                                   | ❌     |
| WireGuard config location | `/etc/wireguard/wg0.conf` managed            | Not found; wg0 UP but location unclear           | ⚠️     |
| OpenClaw config perms     | `600` (owner-only)                          | `664` (group-writable) – CRITICAL                 | ❌     |
| OpenClaw cron stability   | All jobs healthy                            | 3 jobs with `error` status                        | ❌     |

**SSH Config Corruption – Clawd**: Contains `Port 22222222` and `ListenAddress 10.0.0.0/24` – fatal errors. Regression from yesterday (previously at least port 22 worked).

**Cron Job Errors** (new finding):
- `macro-daily-scan`
- `digest-morning-briefing`
- `banker-daily-fact`
All show `error` status. Investigate logs: `/tmp/openclaw/openclaw-*.log` or `journalctl --user -u openclaw-gateway`.

---

## 5. Resource Utilization

| Node     | RAM Total | Used | Free | Cache | Avail | Disk Total | Used | Free | %Used | Load (1/5/15) |
|----------|-----------|------|------|-------|-------|------------|------|------|-------|---------------|
| Nexus    | 941M      | 91M  | 728M | 122M  | 719M  | 9.1G       | 686M | 8.1G | 8%    | 0.00 0.00 0.00 |
| Clawd    | 15Gi      | 1.7Gi| 4.5Gi| 9.7Gi | 13Gi  | 464G       | 30G  | 435G | 7%    | (N/A) |
| Brutus   | 7.7Gi     | 1.4Gi| 3.2Gi| 3.3Gi | 6.3Gi | 232G       | 12G  | 220G | 5%    | 0.00 0.00 0.00 |
| Plutos   | 31Gi      | 1.5Gi| 24Gi | 5.7Gi | 29Gi  | 464G       | 32G  | 433G | 7%    | 0.04 0.01 0.00 |

- **Memory**: All nodes >80% available. No saturation.
- **Disk**: All nodes <10% used. Healthy.
- **CPU**: Load averages negligible across board; no resource bottlenecks.

---

## 6. High Availability & Redundancy

| Component              | Current Redundancy | Risk Level | Notes |
|------------------------|--------------------|------------|-------|
| OpenClaw Gateway       | 3 instances (loopback only) | **HIGH** | No remote access; effectively zero gateway capacity. |
| SSH Access (Mesh)      | Multi-node but inconsistent | **HIGH** | Clawd failed; others on 22; Nexus on 2222. Fragile and non-uniform. |
| Telegram Bot           | Single on Clawd    | HIGH       | Single point of failure; stops if Clawd down. |
| WireGuard Hub (Nexus)  | Single node (1GB)  | MEDIUM-HIGH| Hub failure would disrupt entire mesh. |
| Ollama (Inference)     | Distributed 3 nodes| LOW        | Each node serves local models; no single point for inference. |
| NVIDIA/kimi API        | Single external key| MEDIUM     | Monitor usage; consider rate-limiting. |
| Config Backups         | **None**           | **HIGH**   | No recovery path for config loss or node rebuild. |

**Recommendation**: Designate a dedicated, highly-available gateway node (e.g., Plutos due to 32GB) with proper mesh binding. Add secondary WireGuard hub (Brutus or Plutos) with configuration synchronization.

---

## 7. Cost Optimization

- **Local Models**: All inference nodes run free local models (mistral 7B, qwen2.5-coder 3B, llama3.1 8B). ✅ Excellent cost control.
- **Cloud Model**: Plutos runs `qwen3-coder:480b-cloud` (remote). This 480B parameter model is fetched from ollama.com; monitor for usage quotas or costs.
- **OpenRouter**: Using `openrouter/stepfun/step-3.5-flash:free` – good.
- Infrastructure: 4 VPS nodes (~$25–30/month total). Resources underutilized but distributed inference benefits justify.

No runaway API usage detected, but **monitor Plutos remote model prompts**.

---

## 8. Backup + Recovery

**Status: CRITICAL – No system configuration backups exist.**

Only daily memory logs (`memory/YYYY-MM-DD.md`) and previous audit reports are present. Missing backups:
- `/etc/ssh/` (host keys, configs)
- `/etc/wireguard/` (peer keys, configs)
- `/etc/ollama/` (service configs)
- systemd units (`/etc/systemd/system/`)
- OpenClaw workspace (`~/.openclaw/`)
- ufw/nft rules
- Fail2ban jails

**Impact**: Node failure requires full rebuild from scratch. WireGuard peer rekeying and SSH host key regeneration would cause extended downtime and coordination overhead across nodes.

**Prior Day's Recommendation**: To implement automated backups was **not actioned**. Must be treated as emergency.

---

## 9. Top 5 Immediate Recommendations

### 1. Restore Clawd SSH Access (CRITICAL – Management Outage)

**Why**: Clawd is the gateway node; without SSH, no remote administration possible. Config is corrupt (`Port 22222222`, `ListenAddress 10.0.0.0/24`).

**Commands (run from Clawd console, IONOS VNC, or recovery shell)**:
```bash
# Replace sshd_config with a minimal correct version
sudo tee /etc/ssh/sshd_config <<'EOF'
Port 2222
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AllowUsers boss
UsePAM yes
Subsystem sftp /usr/lib/openssh/sftp-server
ListenAddress 10.0.0.2   # mesh IP only; adjust if needed
EOF
# Validate and restart
sudo sshd -t && sudo systemctl restart ssh
# Verify listening
ss -tuln | grep 2222   # should show 0.0.0.0:2222 or [::]:2222 (or 10.0.0.2:2222)
# Test from another node:
# ssh -p 2222 boss@10.0.0.2
```

**After verification, proceed to step 3 to standardize all nodes to port 2222.**

---

### 2. Deploy Firewall with Mesh-Only Policies (HIGH – Security Hygiene)

**Why**: Default-deny principle restricts internet exposure; only mesh subnet (`10.0.0.0/24`) can reach management and internal services.

**Prerequisite**: Ensure SSH is working on **all nodes** on port 2222 **and** bound to mesh IP before applying, to avoid lockout.

**Commands (on every node)**:
```bash
sudo apt-get update && sudo apt-get install -y ufw   # if not installed
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
# Allow SSH from mesh CIDR (on port 2222 after step 3)
sudo ufw allow from 10.0.0.0/24 to any port 2222 proto tcp
# Allow OpenClaw gateway from mesh (after step 4 rebinds to mesh IP)
sudo ufw allow from 10.0.0.0/24 to any port 18789 proto tcp
# Allow Ollama from mesh only if bound to mesh IP (step 5). Alternatively bind to localhost and skip.
# sudo ufw allow from 10.0.0.0/24 to any port 11434 proto tcp
sudo ufw --force enable
sudo ufw status verbose
```

**Verification**: From another mesh node, SSH and gateway connectivity must succeed. From a non-mesh IP (e.g., your laptop), these ports should be filtered/closed.

---

### 3. Standardize SSH on Port 2222 and Bind to Mesh IP (HIGH)

**Why**: Uniform management port reduces scan noise and aligns with mesh design. Binding to mesh interface restricts exposure to the mesh subnet only.

**Commands (on each node that isn't already compliant: Clawd, Brutus, Plutos)**:
```bash
# Determine mesh IP (wg0)
MESH_IP=$(ip -4 addr show wg0 | grep -o '10\.0\.0\.[0-9]*')
# Ensure config contains only mesh IP binding
sudo tee /etc/ssh/sshd_config <<EOF
Port 2222
ListenAddress $MESH_IP
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AllowUsers boss
UsePAM yes
Subsystem sftp /usr/lib/openssh/sftp-server
EOF
# Validate and restart
sudo sshd -t && sudo systemctl restart ssh
# Verify
ss -tuln | grep 2222   # should show $MESH_IP:2222
```

**Nexus**: Already on port 2222, but restrict `ListenAddress` to its mesh IP `10.0.0.1` similarly.

---

### 4. Rebind OpenClaw Gateway to Mesh Interface (HIGH)

**Why**: Enables remote agents on different nodes to connect; required for distributed architecture.

**Commands (on Clawd, Brutus, Plutos)**:
```bash
# 1) Fix config file permissions (critical)
chmod 600 ~/.openclaw/openclaw.json
# 2) Determine mesh IP
MESH_IP=$(ip -4 addr show wg0 | grep -o '10\.0\.0\.[0-9]*')
# 3) Update gateway bind address
jq ".gateway.bind = \"$MESH_IP\"" ~/.openclaw/openclaw.json > tmp.json && mv tmp.json ~/.openclaw/openclaw.json
# 4) Restart gateway (method depends on setup)
# If using systemd user service:
systemctl --user restart openclaw-gateway
# Or via CLI:
openclaw gateway restart
# 5) Verify binding
ss -tuln | grep 18789   # should show LISTEN on $MESH_IP:18789 (not 127.0.0.1)
# 6) Test remote connectivity from another node:
# From clawd: nc -zv 10.0.0.3 18789  (should succeed to brutus)
```

**Note**: After rebinding, `openclaw cron list` should remain responsive. If hangs persist, check logs: `journalctl --user -u openclaw-gateway -n 100`.

---

### 5. Restrict Ollama API to Localhost or Mesh CIDR (CRITICAL – Exposure)

**Why**: Prevents unauthenticated internet access to inference APIs on all inference nodes.

**Commands (on Clawd, Brutus, Plutos)**:
```bash
# Option A (Recommended): Bind to localhost only. Agents access via localhost (same node).
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/limit.conf <<'EOF'
[Service]
Environment="OLLAMA_HOST=127.0.0.1"
EOF
sudo systemctl daemon-reload
sudo systemctl restart ollama
# Verify
ss -tuln | grep 11434   # should show 127.0.0.1:11434 only

# Option B (if remote nodes must call Ollama directly): bind to mesh IP
# MESH_IP=$(ip -4 addr show wg0 | grep -o '10\.0\.0\.[0-9]*')
# sudo tee /etc/systemd/system/ollama.service.d/limit.conf <<EOF
# [Service]
# Environment="OLLAMA_HOST=$MESH_IP:11434"
# EOF
# Then add corresponding ufw allow from 10.0.0.0/24 to 11434 (after step 2).
```

**Important**: If any OpenClaw agents are configured to use Ollama on remote nodes, they must be updated to use the mesh IP after this change, or use a local agent-to-agent proxy. Localhost binding is safest; consider moving inference tasks to local agents instead of remote.

---

### Bonus: Must‑Do Within 48 h

- **Install fail2ban on Nexus** (`sudo apt-get install -y fail2ban && sudo systemctl enable --now fail2ban`). Protects SSH port 2222.
- **Implement automated configuration backups** (see previous audit report for script). Backup `/etc/ssh/`, `/etc/wireguard/`, `/etc/ollama/`, systemd units, and `~/.openclaw/`. Store in workspace memory and rotate (7 days).
- **Document WireGuard setup**: Capture how `wg0` is configured. If using wg-quick, ensure `/etc/wireguard/wg0.conf` exists and is backed up. If using NetworkManager, export connection profile: `nmcli connection show <wg0>` and back up `/etc/NetworkManager/system-connections/`.
- **Identify and restrict services listening on 0.0.0.0**: On Clawd, ports 3000, 9100, 9092 are listening publicly. Determine purpose and bind to localhost or mesh-only, or firewall them.
- **Investigate cron job errors**: Check logs for `macro-daily-scan`, `digest-morning-briefing`, `banker-daily-fact` and fix underlying issues.

---

## 10. Trend vs Previous Day

| Metric                    | 2026-02-16 | 2026-02-17 | 2026-02-18 | Trend |
|---------------------------|------------|------------|------------|-------|
| Overall Health Score      | 5/10       | 3/10       | **2/10**   | 🔻🔻   |
| SSH (Clawd)               | active:22  | failed     | failed     | 🔻     |
| OpenClaw gateway binding  | loopback   | loopback   | loopback   | ➡️     |
| Ollama exposure           | exposed    | exposed    | exposed    | ➡️     |
| Firewall deployment       | unclear    | unclear    | unclear    | ➡️     |
| Config backups            | none       | none       | none       | ➡️     |
| Cron errors               | none       | none       | **3 errors**| 🔻     |
| Resource headroom         | healthy    | healthy    | healthy    | ➡️     |

**Trend**: Continued degradation. No recommendations from previous audits have been implemented. New issues: cron job failures, persistent SSH outage, still no backups. Immediate emergency remediation required.

---

**Report generated**: 2026-02-18 04:00 UTC  
**Next audit**: 2026-02-19 03:00 UTC (daily)