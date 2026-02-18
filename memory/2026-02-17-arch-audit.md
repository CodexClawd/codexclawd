# OpenClaw Mesh Infrastructure Deep Audit

**Date:** 2026-02-17 (03:00–04:30 UTC)  
**Auditor:** System Architect Agent  
**Scope:** Full mesh (Nexus 10.0.0.1, Clawd 10.0.0.2, Brutus 10.0.0.3, Plutos 10.0.0.4)  
**Methodology:** Local diagnostics + remote SSH (non-sudo) + port scanning + config analysis

---

## Executive Summary

🔴 **Overall Health: 3/10** (Critical regression, multiple security exposures, management outage)

The mesh remains **operationally connected** at the network layer, but **management has been severely degraded** due to Clawd's SSH failure, and **critical security exposures persist** from yesterday (Ollama internet-exposed, OpenClaw gateways loopback-only). Resource health is excellent, but configuration drift is worsening.

**vs Previous Day (2026-02-16):** Deterioration. Health dropped from 5/10 to 3/10 due to:
- Clawd SSH daemon now **failed** (invalid config) – previously it was active on port 22.
- OpenClaw config file permissions still insecure (664) – unfixed.
- No firewall rules can be verified (sudo access blocked).
- No remediation applied despite prior recommendations.

---

## 1. Mesh Health

### 1.1 Connectivity & Latency

| Node     | Mesh IP   | Ping RTT (ms) | Status | wg0 iface |
|----------|-----------|---------------|--------|-----------|
| Nexus    | 10.0.0.1  | 14 avg        | ✅     | UP (confirmed) |
| Clawd    | 10.0.0.2  | 0.04 avg      | ✅     | UP (local) |
| Brutus   | 10.0.0.3  | 27 avg        | ✅     | UP (confirmed) |
| Plutos   | 10.0.0.4  | 12.5 avg      | ✅     | UP (confirmed) |

- **WireGuard**: wg0 UP on all reachable nodes. Interface exists on Clawd (local). No packet loss observed in 4-ping samples (note: limited sample; previous audit used 20 pings). Latency acceptable; Brutus shows higher jitter (24–34 ms) – monitor.
- **Configuration discovery**: No `/etc/wireguard/wg0.conf` found on any node (missing due to permissions or alternate management). This is a **knowledge gap** that complicates recovery.

**Conclusion**: Mesh connectivity remains solid. Network layer functional.

---

## 2. Services

### 2.1 SSH Daemon

| Node     | Service Status | Port(s) Listening | Desired (2222) | Binding Scope |
|----------|----------------|-------------------|----------------|---------------|
| Nexus    | active         | 0.0.0.0:2222      | ✅             | All interfaces (should restrict to 10.0.0.1) |
| Clawd    | **failed**     | none              | ❌             | — |
| Brutus   | active         | 0.0.0.0:22        | ❌             | All interfaces (should be 2222 & mesh-only) |
| Plutos   | active         | 0.0.0.0:22        | ❌             | All interfaces (should be 2222) |

**Critical Finding**: Clawd SSH is down due to **invalid sshd_config**:
- `Port 22222222` (8 digits) – invalid port number.
- `ListenAddress 10.0.0.0/24` – network address, not an IP.
Result: sshd fails to start. This **isolates the gateway node** from remote administration.

Brutus/Plutos: SSH listening on `0.0.0.0:22` (public interface) exposes standard SSH to the internet unless blocked by external firewall. Inconsistent port prevents uniform mesh admin.

**Action required**: Restore Clawd SSH immediately by correcting config or restoring backup `/etc/ssh/sshd_config.broken`.

### 2.2 Ollama API

| Node     | Service Status | Port 11434 Binding | Auth  | Accessible from internet |
|----------|----------------|--------------------|-------|---------------------------|
| Clawd    | listening      | unknown (assume 0.0.0.0) | ❌   | likely (SSH down, but service up) |
| Brutus   | listening      | 0.0.0.0:11434      | ❌   | ✅ YES |
| Plutos   | listening      | 0.0.0.0:11434      | ❌   | ✅ YES |
| Nexus    | not installed  | —                  | —     | — |

- Verified via `ss -tuln` on Brutus/Plutos. Both bind to `*:11434` (all interfaces).
- **Critical Exposure**: Unauthenticated inference APIs reachable from the public internet on two nodes. Anyone can query models, potentially leading to:
  - Data exfiltration via crafted prompts
  - Abuse of computational resources (costly if using external model providers)
  - Reconnaissance foothold if combined with other vulns

**Note**: Clawd's Ollama process is running; we assume same binding unless environment overrides.

### 2.3 OpenClaw Gateway

| Node     | Service Status | Port 18789 Binding | Remote Access |
|----------|----------------|--------------------|---------------|
| Clawd    | active (user)  | 127.0.0.1:18789    | ❌ (loopback) |
| Brutus   | active (user)  | 127.0.0.1:18789    | ❌ (loopback) |
| Plutos   | active (user)  | 127.0.0.1:18789    | ❌ (loopback) |
| Nexus    | not installed  | —                  | —             |

- Configuration: `"bind": "loopback"` confirmed on all three nodes.
- This **prevents remote agents** (including other mesh nodes) from connecting to the gateway, defeating distributed architecture. Effectively zero remote gateway capacity.
- Additionally, `openclaw cron list` **hangs** (observed), indicating potential gateway instability.

### 2.4 Fail2Ban

| Node     | Status   | Enabled |
|----------|----------|---------|
| Clawd    | active   | yes     |
| Brutus   | active   | yes     |
| Plutos   | active   | yes     |
| Nexus    | inactive | **no**  |

- Nexus lacks fail2ban entirely. Should be installed and protecting SSH (port 2222) at minimum.

---

## 3. Security

### 3.1 Firewall Status

All nodes have `/etc/ufw/ufw.conf` with `ENABLED=yes`, but **active rules cannot be verified** without sudo (password prompts blocked). Assumptions:
- If ufw is enabled, default policy may be `deny incoming` or `allow` (unknown).
- No evidence of mesh-specific allow rules (SSH 2222, Ollama 11434, OpenClaw 18789) in copied configs (only main ufw.conf, not user.rules).
- Lack of sudo prevents confirmation; **firewall posture is uncertain**.

**Risk**: Even if enabled, misconfigured rules could allow unwanted traffic.

### 3.2 Exposed Services Summary (Public Interface Perspective)

| Node   | Public IP       | Services bound to 0.0.0.0 (all interfaces) |
|--------|-----------------|---------------------------------------------|
| Clawd  | 85.215.46.147  | **SSH** (port 22, if service were running) – currently down; **Ollama** (likely); OpenClaw (loopback only) |
| Brutus | 87.106.6.144   | SSH:22, Ollama:11434, Syncthing:22000, OpenClaw (loopback) |
| Plutos | 87.106.3.190   | SSH:22, Ollama:11434, OpenClaw (loopback) |
| Nexus  | (none?)         | SSH:2222 (all interfaces)                 |

**Internet-facing exposures** (if not blocked by cloud provider security groups):
- Brutus: SSH (22) – weak exposure; Ollama (11434) – critical.
- Plutos: SSH (22) – weak exposure; Ollama (11434) – critical.
- Nexus: SSH (2222) – mesh-only port but still internet-accessible if public IP assigned; should be restricted via firewall.

**Recommendation**: Bind sensitive services to mesh interface only (`10.0.0.x`) or implement firewall rules to restrict by source IP (mesh CIDR).

### 3.3 Configuration File Permissions

- OpenClaw config `/home/boss/.openclaw/openclaw.json` has mode `664` (group-writable). This is a **critical security issue** because API keys reside there (NVIDIA, BRAVE, etc.). Correct: `600`.
- SSH host keys: standard (`600`/`640`) – OK.
- No world-readable private keys found.

**Status**: Unchanged from yesterday; still vulnerable.

---

## 4. Configuration Drift

| Item                      | Desired State                                | Observed State(s)                                  | Drift |
|---------------------------|----------------------------------------------|----------------------------------------------------|-------|
| **SSH port**              | 2222 on **all** nodes (mesh admin)          | Nexus:2222; Clawd:failed; Brutus:22; Plutos:22    | ❌❌   |
| **OpenClaw gateway bind** | `0.0.0.0` **or** mesh IP for remote access | `loopback` on all three running instances         | ❌     |
| **Ollama bind**           | `127.0.0.1` **or** mesh CIDR only           | `0.0.0.0` on Brutus/Plutos (exposed)              | ❌     |
| **Firewall**              | ufw/nft enabled, default deny, mesh allow  | ufw.conf enabled, but rules unknown (sudo blocked) | ⚠️❓   |
| **Fail2ban**              | active on **all** exposed nodes             | Nexus: inactive                                    | ❌     |
| **WireGuard config**      | `/etc/wireguard/wg0.conf` managed            | Not found; wg0 UP but location unclear            | ⚠️     |
| **OpenClaw config perms** | `600` (owner-only)                          | `664` (group-writable) – CRITICAL                 | ❌     |

**SSH Config Corruption**: Clawd's `sshd_config` contains two fatal errors (`Port 22222222`, `ListenAddress 10.0.0.0/24`). This is a **regression** from yesterday (previously port 22). Likely accidental edit.

**WireGuard Mystery**: All nodes have `wg0` UP, but no standard config file exists (or permissions restrict access). Could indicate management via NetworkManager, cloud-init, or custom script. **Must be documented** to ensure recoverability.

---

## 5. Resource Utilization

| Node     | RAM Total | Used | Free | Cache | Avail | Disk Total | Used | Free | %Used |
|----------|-----------|------|------|-------|-------|------------|------|------|-------|
| Nexus    | 941M      | 91M  | 728M | 122M  | 719M  | 9.1G       | 686M | 8.1G | 8%    |
| Clawd    | 15Gi      | 1.6Gi| 4.7Gi| 9.6Gi | 14Gi  | 464G       | 32G  | 432G | 7%    |
| Brutus   | 7.7Gi     | 1.4Gi| 3.3Gi| 3.3Gi | 6.3Gi | 232G       | 12G  | 220G | 5%    |
| Plutos   | 31Gi      | 1.4Gi| 25Gi | 5.3Gi | 29Gi  | 464G       | 32G  | 433G | 7%    |

- **CPU**: Not collected (requires sudo). Load averages are negligible across nodes (0.0–0.2). No saturation concerns.
- **Memory**: All nodes have >80% available. Healthy.
- **Disk**: All nodes <10% used. Plenty of headroom.

**Conclusion**: Resources are not a bottleneck. Good.

---

## 6. High Availability & Redundancy

| Component              | Current Redundancy | Risk Level | Notes |
|------------------------|--------------------|------------|-------|
| OpenClaw Gateway       | 3 instances (loopback only) | **HIGH** | All bound to 127.0.0.1 → no remote access. Effectively zero gateway capacity for distributed agents. |
| Telegram Bot           | Single on Clawd    | HIGH       | If Clawd down, notifications stop. |
| SSH Access (Mesh)      | Multi-node but inconsistent | HIGH | Clawd SSH failed; others on 22; Nexus on 2222. Fragile. |
| WireGuard Hub (Nexus) | **Single node**    | MEDIUM-HIGH| Nexus is only hub; 1GB RAM. Failure would disrupt mesh. |
| Ollama (Inference)     | Distributed 3 nodes| LOW        | Each node serves local models; no single point for inference, but exposures increase risk. |
| NVIDIA/kimi API        | Single external key| MEDIUM     | Monitor usage; rate-limit. |

**Recommendation**: Designate a dedicated gateway node (e.g., Plutos due to 32GB) with HA failover. Add secondary WireGuard hub (Brutus or Plutos) with config sync and health checks.

---

## 7. Cost Optimization

- **Local Models**: Free-tier via Ollama (mistral 7B, qwen2.5-coder 3B, llama3.1 8B). ✅ Excellent.
- **Cloud Model**: Plutos has `qwen3-coder:480b-cloud` (remote). This is a massive 480B parameter model fetched from ollama.com. It likely has usage limits or costs depending on Ollama's terms. Monitor/log prompts sent to this model to ensure no runaway bills.
- **OpenRouter**: Stepfun/step-3.5-flash:free in use – good.
- Infrastructure cost: ~$25-30/month for 4 VPS nodes. Underutilized resources could be consolidated, but distributed inference benefits justify current topology.

No obvious runaway usage detected.

---

## 8. Backup + Recovery

**Status**: **Poor**. No system configuration backups exist.

- Only daily memory logs (`memory/YYYY-MM-DD.md`) are present.
- No backups of:
  - `/etc/ssh/` (host keys, configs)
  - `/etc/wireguard/` (or wg state)
  - `/etc/ollama/` (service configs)
  - systemd units
  - OpenClaw workspace (`~/.openclaw/`)
- **Impact**: Node loss requires full rebuild from scratch, especially WireGuard peer keys and SSH host keys. Recovery time unknown.

**Yesterday's recommendation to implement backups was not actioned**. Must prioritize.

---

## 9. Top 5 Immediate Recommendations

### 1. **Restore Clawd SSH** (CRITICAL – Management Outage)

**Why**: Clawd is the gateway node; without SSH, no remote administration possible. Current config corrupt.

**Commands (run from Clawd console or recovery)**:
```bash
# Restore known-good config
sudo cp /etc/ssh/sshd_config.broken /etc/ssh/sshd_config
# Or regenerate minimal correct config
sudo tee /etc/ssh/sshd_config <<'EOF'
Port 22
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
ss -tuln | grep :22
```

After recovery, change to desired port 2222 (see rec #3) and restart again.

---

### 2. **Restrict Ollama API to Localhost or Mesh CIDR** (CRITICAL – Exposure)

**Why**: Prevents unauthenticated internet access to inference APIs on Brutus and Plutos.

**Commands (per inference node: brutus, plutos, and clawd once SSH restored)**:
```bash
# Create systemd override to bind to localhost
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/limit.conf <<'EOF'
[Service]
Environment="OLLAMA_HOST=127.0.0.1"
# Optionally also limit to IPv4 only: Environment="OLLAMA_HOST=127.0.0.1:11434"
EOF
sudo systemctl daemon-reload
sudo systemctl restart ollama
# Verify
ss -tuln | grep 11434  # Should show 127.0.0.1:11434 or 127.0.0.1:11434 only
```

*Alternative*: If remote nodes must access Ollama directly (not recommended), bind to mesh interface IP instead of localhost: `Environment="OLLAMA_HOST=10.0.0.x:11434"` and add firewall rule to restrict source to `10.0.0.0/24`.

---

### 3. **Standardize SSH on Mesh Port 2222 and Bind to Mesh IP** (HIGH)

**Why**: Consistency, reduces noise from internet-wide SSH scans, and aligns with mesh design.

**Commands (on each node except Nexus which already uses 2222)**:
```bash
# Edit /etc/ssh/sshd_config
sudo sed -i 's/^#Port 22/Port 2222/' /etc/ssh/sshd_config
sudo sed -i 's/^Port 22/Port 2222/' /etc/ssh/sshd_config 2>/dev/null || echo "Port 2222" | sudo tee -a /etc/ssh/sshd_config
# Ensure only mesh interface listens (replace with your node's mesh IP)
MESH_IP=$(ip -4 addr show wg0 | grep -o '10\.0\.0\.[0-9]*')
sudo sed -i "/^#ListenAddress/s/^#//; /^ListenAddress/d" /etc/ssh/sshd_config
echo "ListenAddress $MESH_IP" | sudo tee -a /etc/ssh/sshd_config
# Ensure other security settings
sudo sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
# Validate and restart
sudo sshd -t && sudo systemctl restart ssh
# Verify
ss -tuln | grep 2222
```

**Firewall update** (after step 4) will need to allow port 2222 from mesh CIDR only.

---

### 4. **Deploy Firewall with Mesh-Only Policies** (HIGH)

**Why**: Default-deny reduces attack surface; restrict management and app traffic to mesh subnet only.

**Assumption**: ufw is installed. If not, install it.

**Commands (on every node)**:
```bash
sudo apt-get update && sudo apt-get install -y ufw  # if not present
# Reset to clean state (careful: may disconnect if SSH not on 2222 yet)
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
# Allow SSH from mesh CIDR (after you've moved to port 2222)
sudo ufw allow from 10.0.0.0/24 to any port 2222 proto tcp
# Allow Ollama from mesh CIDR only (if you bind to mesh IP instead of localhost)
# sudo ufw allow from 10.0.0.0/24 to any port 11434 proto tcp
# Allow OpenClaw gateway from mesh CIDR (after rebinding to mesh IP)
sudo ufw allow from 10.0.0.0/24 to any port 18789 proto tcp
# Enable
sudo ufw --force enable
# Verify
sudo ufw status verbose
```

**IMPORTANT**: Apply **after** SSH is on 2222 and listening on mesh IP only, and **after** OpenClaw gateways are rebound. Test connectivity from another node before locking yourself out.

---

### 5. **Fix OpenClaw Gateway Binding & Permissions + Reboot Gateway** (HIGH)

**Why**: Enables remote agent coordination across mesh. Also fixes critical config exposure.

**Commands (on each OpenClaw node: clawd, brutus, plutos)**:
```bash
# 1) Fix config file permissions (critical)
chmod 600 ~/.openclaw/openclaw.json
# 2) Rebind gateway to mesh interface (so other nodes can connect)
MESH_IP=$(ip -4 addr show wg0 | grep -o '10\.0\.0\.[0-9]*')
jq ".gateway.bind = \"$MESH_IP\"" ~/.openclaw/openclaw.json > tmp.json && mv tmp.json ~/.openclaw/openclaw.json
# 3) Restart gateway
# If using systemd user service:
systemctl --user restart openclaw-gateway
# Or use CLI:
openclaw gateway restart
# 4) Verify binding
ss -tuln | grep 18789  # Should show LISTEN on 10.0.0.x:18789 (not 127.0.0.1)
# 5) Test remote connectivity from another node:
# From clawd: nc -zv 10.0.0.3 18789  (to plutos)
```

**Note**: If `openclaw cron list` still hangs after restart, check logs: `journalctl --user -u openclaw-gateway -n 50` or `/tmp/openclaw/openclaw-*.log`.

---

### Bonus: Must‑Do Within 48 h

- **Install fail2ban on Nexus** (`sudo apt-get install -y fail2ban; sudo systemctl enable --now fail2ban`). Protects SSH port 2222.
- **Implement automated configuration backups** (as previously recommended) to enable disaster recovery.
- **Document WireGuard setup** – capture how wg0 is configured; create `/etc/wireguard/wg0.conf` if managed manually, or document the tool (NetworkManager, etc.) and backup its state.
- **Identify and restrict services listening on 0.0.0.0**: Ports 3000, 9100, 9092 on Clawd; understand their purpose and bind to localhost or mesh-only if internal.

---

## 10. Trend vs Previous Day

| Metric                    | 2026-02-16 | 2026-02-17 | Trend |
|---------------------------|------------|------------|-------|
| Overall Health Score      | 5/10       | 3/10       | 🔻 Deteriorated |
| SSH (Clawd)               | active:22  | failed     | 🔻 Regression |
| OpenClaw gateway binding  | loopback   | loopback   | ➡️ No change |
| Ollama exposure           | exposed    | exposed    | ➡️ No change |
| Firewall deployment       | unclear    | unclear    | ➡️ No action |
| Config backups            | none       | none       | ➡️ No action |
| Resource headroom         | healthy    | healthy    | ➡️ OK |

**Key takeaway**: Critical services degraded; prior recommendations ignored. Immediate remediation required to avoid further erosion of manageability and security.

---

**Report generated**: 2026-02-17 04:30 UTC  
**Next audit**: 2026-02-18 03:00 UTC (daily)
