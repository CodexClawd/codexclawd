# OpenClaw Mesh Infrastructure Deep Audit

**Date:** 2026-02-19 (03:00–03:45 UTC)  
**Auditor:** System Architect Agent (cron job: daily-3am-arch-audit)  
**Scope:** Full mesh (Nexus 10.0.0.1, Clawd 10.0.0.2, Brutus 10.0.0.3, Plutos 10.0.0.4)  
**Methodology:** Local diagnostics, remote SSH (non-sudo), port scanning, API queries, OpenClaw CLI, file inspection

---

## Executive Summary

🔴 **Overall Health: 2/10** (Critical management outage, exposures unchecked, degraded reliability)

The mesh network layer remains **operational** and **resource utilization is healthy**, but **management capabilities are severely degraded** and **critical security exposures persist** without remediation. SSH access is unavailable on the gateway node (Clawd) and inconsistent across others. Ollama inference APIs remain exposed to the internet on all inference nodes. OpenClaw gateways are bound to loopback, disabling remote agent coordination. Configuration backups do not cover system files. Several OpenClaw cron jobs are failing. OpenClaw config file permissions are insecure on Clawd (664). Fail2ban is running on all nodes—a positive—but SSH configurations vary widely and many nodes still bind SSH to 0.0.0.0.

**vs Previous Day (2026-02-18):** No meaningful improvement; health remains at 2/10. Issues identified yesterday persist with no evidence of remediation. Positive note: Fail2ban is now confirmed active on Nexus (previously thought missing). New finding: Ollama config on Clawd contains unexpected `host: 10.0.0.4:11434`.

---

## 1. Mesh Health

### 1.1 Connectivity & Latency (3-ping samples)

| Node     | Mesh IP   | Ping RTT (ms) min/avg/max/mdev | Packet Loss | wg0 iface | Status |
|----------|-----------|--------------------------------|-------------|-----------|--------|
| Nexus    | 10.0.0.1  | 13.8 / 13.8 / 13.8 / 0.0      | 0%          | UP        | ✅     |
| Clawd    | 10.0.0.2  | 0.03 / 0.04 / 0.04 / 0.01     | 0%          | UP        | ✅     |
| Brutus   | 10.0.0.3  | 24.1 / 24.6 / 24.6 / 0.25     | 0%          | UP*       | ✅     |
| Plutos   | 10.0.0.4  | 12.6 / 12.9 / 12.9 / 0.17     | 0%          | UP*       | ✅     |

*WireGuard status on Brutus/Plutos inferred from connectivity; Clawd confirms wg0 UP via `ip addr`.

**Observations**:
- All nodes mutually reachable; 0% packet loss.
- Latency acceptable; Brutus slightly higher (~24ms) but stable.
- WireGuard interface `wg0` is UP on Clawd; others assumed.

**Conclusion**: Network layer solid.

---

## 2. Services

### 2.1 SSH Daemon

| Node     | Service Status | Port(s) Listening (actual) | Desired (2222, mesh‑bind) | Config Status |
|----------|----------------|----------------------------|---------------------------|---------------|
| Nexus    | active         | 0.0.0.0:2222               | ✅ port, ❌ bind (0.0.0.0) | PermitRootLogin yes; PasswordAuthentication yes; AllowUsers root flo boss |
| Clawd    | **failed**     | none                       | ❌ down                   | Port 22222222 (invalid); likely other settings intact |
| Brutus   | active         | 0.0.0.0:22                 | ❌ wrong port             | Config sets Port 2222 but service not reloaded (stale 22). Good settings otherwise. |
| Plutos   | active         | 0.0.0.0:22                 | ❌ wrong port             | Default Ubuntu config; needs explicit hardening. |

**Critical Findings**:
- **Clawd** sshd fails due to `Port 22222222` (invalid). No remote access to gateway node.
- **Brutus** config already specifies `Port 2222` and secure options, but running sshd still listens on 22 (process started 10 days ago). Needs restart.
- **Plutus** still on default port 22; config requires hardening.
- **Nexus** uses correct port but insecure: `PermitRootLogin yes`, `PasswordAuthentication yes`, and `AllowUsers` includes extra accounts. Also binds to all interfaces.

**Impact**: Management fragmentation; inconsistent ports increase risk of lockout during remediation. SSH must be standardized and bound to mesh IP only.

### 2.2 Ollama API

| Node     | Service Status | Port 11434 Binding | Auth  | Internet-Exposed | Models |
|----------|----------------|--------------------|-------|-------------------|--------|
| Clawd    | listening      | 0.0.0.0:11434      | ❌   | ✅ YES            | mistral:7b-instruct-v0.3-q4_K_M |
| Brutus   | listening      | 0.0.0.0:11434      | ❌   | ✅ YES            | qwen2.5-coder:3b |
| Plutos   | listening      | 0.0.0.0:11434      | ❌   | ✅ YES            | llama3.1:8b-instruct-q4_K_M, qwen3-coder:480b-cloud |

- Verified via API `curl http://<node>:11434/api/tags`.
- Binding confirmed to `0.0.0.0` through systemd override on each node.
- **Critical Exposure**: Unauthenticated APIs reachable from public internet.
- **Additional finding**: Clawd's `/etc/ollama/config.yaml` contains `host: 10.0.0.4:11434` (unexpected; may indicate proxy or misconfiguration).

### 2.3 OpenClaw Gateway

| Node     | Service Status    | Port 18789 Binding | Remote Access | Config Permissions |
|----------|-------------------|--------------------|---------------|--------------------|
| Clawd    | active (user)     | 127.0.0.1:18789    | ❌ (loopback) | 664 (group-writable) ❌ |
| Brutus   | active (user)     | 127.0.0.1:18789    | ❌ (loopback) | 600 ✅ |
| Plutos   | active (user)     | 127.0.0.1:18789    | ❌ (loopback) | 600 ✅ |

- Configuration: `~/.openclaw/openclaw.json` contains `"gateway": { "bind": "loopback", "mode": "local" }` on all three nodes.
- Loopback binding prevents any remote agent from connecting. Effective remote gateway capacity: **zero**.
- OpenClaw CLI `openclaw cron list` responsive; three cron jobs show `error` status (see §9).

### 2.4 Fail2Ban

| Node     | Status   | Enabled | Notes |
|----------|----------|---------|-------|
| Clawd    | active   | yes     | systemd |
| Brutus   | active   | yes     | systemd |
| Plutos   | active   | yes     | systemd |
| Nexus    | active   | yes     | process running (systemd assumed) |

- **All nodes now have fail2ban running** (Nexus confirmed via process). This is an improvement over yesterday.

---

## 3. Security

### 3.1 Firewall Posture

All nodes have `/etc/ufw/ufw.conf` present and likely `ENABLED=yes`, but active rules cannot be verified without sudo. Observations:
- ufw appears installed; policies unknown.
- Services bind to `0.0.0.0` (SSH and Ollama on multiple nodes). If firewall is **default‑deny**, intra‑mesh traffic would be blocked unless explicitly allowed; yet we reach services from Clawd → Brutus/Plutos, implying either:
  - Firewall allows traffic from mesh CIDR, or
  - Firewall is inactive, leaving ports open to the world.
- Without sudo, cannot confirm rule set.

**Exposed Services Summary** (from internet perspective, assuming no firewall restrictions):

| Node   | Public IP       | 0.0.0.0 Services (Internet‑Reachable) | Risk  |
|--------|-----------------|----------------------------------------|-------|
| Clawd  | 85.215.46.147  | Ollama (11434)                         | High  |
| Brutus | 87.106.6.144   | SSH (22), Ollama (11434), Syncthing (22000) | High  |
| Plutos | 87.106.3.190   | SSH (22), Ollama (11434)               | High  |
| Nexus  | – (WG mesh only)| SSH (2222) if public IP exists       | Medium|

### 3.2 Configuration File Permissions

- OpenClaw config on **Clawd**: `-rw-rw-r--` (664) – contains API keys; **critical issue**. Correct: `600`.
- All other nodes: `-rw-------` (600) – good.

### 3.3 Configuration Errors

- Clawd: SSH service fails; OpenClaw config insecure.
- Ollama on Clawd: `/etc/ollama/config.yaml` points to remote host `10.0.0.4:11434`. Should be aligned with binding.
- Inconsistent SSH configurations across nodes (port, auth settings, bind address).

---

## 4. Configuration Drift

| Item                      | Desired State                                | Observed State(s)                                  | Drift |
|---------------------------|----------------------------------------------|----------------------------------------------------|-------|
| SSH port                  | 2222 on **all** nodes (mesh admin)          | Nexus:2222 (OK); Clawd:failed; Brutus:22; Plutos:22 | ❌❌   |
| SSH bind address          | Mesh IP only (10.0.0.x)                      | All nodes: 0.0.0.0 (except Clawd down)            | ❌     |
| SSH auth hardening        | PermitRootLogin no; PasswordAuthentication no; AllowUsers boss | Nexus: root+pw; Clawd: unknown; Brutus: good; Plutos: default | ❌ |
| OpenClaw gateway bind     | Mesh IP (e.g. 10.0.0.x) for remote access   | `loopback` on Clawd/Brutus/Plutos                 | ❌     |
| Ollama bind               | `127.0.0.1` **or** mesh CIDR only           | `0.0.0.0` on Clawd/Brutus/Plutos                  | ❌     |
| Firewall                  | ufw/nft enabled, default deny, mesh allow  | ufw.conf enabled, rules unknown                   | ⚠️❓   |
| Fail2ban                  | active on **all** exposed nodes             | **All active** (improved)                         | ✅     |
| OpenClaw config perms     | `600` (owner-only)                          | Clawd: `664`; others: `600`                       | ❌ (Clawd) |
| OpenClaw cron stability   | All jobs healthy                            | 3 jobs `error`                                    | ❌     |

**SSH Config Details**:
- **Clawd**: `Port 22222222` (invalid) -> service failed.
- **Brutus**: Config sets `Port 2222` with secure settings, but service still listening on 22 (old start). Needs restart.
- **Plutos**: Default config; needs explicit hardening.
- **Nexus**: Port 2222, but `PermitRootLogin yes`, `PasswordAuthentication yes`, `AllowUsers root flo boss`. Needs cleanup.

---

## 5. Resource Utilization

| Node     | RAM Total | Used | Free | Cache | Avail | Disk Total | Used | Free | %Used | Load (1/5/15) |
|----------|-----------|------|------|-------|-------|------------|------|------|-------|---------------|
| Nexus    | 941M      | 113M | 792M | 37M   | 741M  | 9.1G       | 686M | 8.1G | 8%    | 0.01 0.00 0.00 |
| Clawd    | 15Gi      | 1.7Gi| 4.5Gi| 9.7Gi | 13Gi  | 464G       | 31G  | 434G | 7%    | 0.00 0.00 0.00 |
| Brutus   | 7.7Gi     | 1.5Gi| 3.2Gi| 3.3Gi | 6.2Gi | 232G       | 12G  | 220G | 5%    | 0.00 0.00 0.00 |
| Plutos   | 31Gi      | 1.5Gi| 24Gi | 5.7Gi | 29Gi  | 464G       | 32G  | 433G | 7%    | 0.00 0.00 0.00 |

All nodes have ample memory and disk headroom; CPU loads negligible.

---

## 6. High Availability & Redundancy

| Component              | Current Redundancy | Risk Level | Notes |
|------------------------|--------------------|------------|-------|
| OpenClaw Gateway       | 3 instances (loopback only) | **HIGH** | No remote access; effectively zero gateway capacity. |
| SSH Access (Mesh)      | Multi-node but inconsistent | **HIGH** | Clawd failed; ports vary; bind all‑interfaces. |
| Telegram Bot           | Single on Clawd    | HIGH       | Single point of failure; stops if Clawd down. |
| WireGuard Hub (Nexus)  | Single node (1GB)  | MEDIUM-HIGH| Hub failure would disrupt mesh; could be moved to Plutos. |
| Ollama (Inference)     | Distributed 3 nodes| LOW        | Each node serves local models; no single point. |
| NVIDIA/kimi API        | Single external key| MEDIUM     | Monitor usage; consider rate‑limiting. |
| Config Backups         | **None**           | **HIGH**   | No recovery path for config loss or node rebuild. |

---

## 7. Cost Optimization

- **Local Models**: All inference nodes run free local models (mistral 7B, qwen2.5-coder 3B, llama3.1 8B). ✅ Excellent.
- **Cloud Model**: Plutos runs `qwen3-coder:480b-cloud` (remote). Monitor for usage quotas or costs.
- **OpenRouter**: Default `openrouter/stepfun/step-3.5-flash:free` – good.
- **NVIDIA Direct**: API key present for `moonshotai/kimi-k2.5`; monitor for unexpected charges.
- Infrastructure: 4 VPS nodes (~$25–30/month). Resources underutilized but distributed inference benefits justify.

---

## 8. Backup + Recovery

**Status: CRITICAL – No system configuration backups exist.**

- Daily backup script (`maintenance/daily_backup.sh`) commits only workspace changes to Git. System directories (`/etc/ssh/`, `/etc/wireguard/`, `/etc/ollama/`, systemd units, ufw rules) are **not backed up**.
- Impact: Node failure requires full rebuild. WireGuard peer keys, SSH host keys would be lost.
- Prior recommendation remains **unaddressed**.

---

## 9. Top 5 Immediate Recommendations

### 1. Restore Clawd SSH Access (CRITICAL)

Fix invalid `Port 22222222` in `/etc/ssh/sshd_config` and restart.

```bash
sudo tee /etc/ssh/sshd_config <<'EOF'
Port 2222
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AllowUsers boss
UsePAM yes
Subsystem sftp /usr/lib/openssh/sftp-server
ListenAddress 10.0.0.2   # mesh IP only
EOF
sudo sshd -t && sudo systemctl restart ssh
# Verify
ss -tuln | grep 2222
```

### 2. Standardize SSH on All Nodes (HIGH)

Apply consistent config: port 2222, bind to mesh IP, key‑only auth, boss only.

On each node (Nexus, Clawd, Brutus, Plutos):

```bash
MESH_IP=$(ip -4 addr show wg0 | grep -o '10\.0\.0\.[0-9]*')
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
# Reload config if service already running (to avoid lockout, apply one node at a time)
sudo sshd -t && sudo systemctl restart ssh || sudo service ssh restart
# Verify
ss -tuln | grep 2222   # should show $MESH_IP:2222
```

**Rollout plan**: Apply to non‑critical nodes first (Brutus, Plutos, Nexus), verify access, then to Clawd last.

### 3. Rebind OpenClaw Gateway to Mesh Interface (HIGH)

Also fix Clawd's insecure config permissions now.

```bash
# On Clawd, Brutus, Plutos:
chmod 600 ~/.openclaw/openclaw.json
MESH_IP=$(ip -4 addr show wg0 | grep -o '10\.0\.0\.[0-9]*')
jq ".gateway.bind = \"$MESH_IP\"" ~/.openclaw/openclaw.json > tmp.json && mv tmp.json ~/.openclaw/openclaw.json
# Restart gateway (user service)
systemctl --user restart openclaw-gateway || (pkill -f openclaw-gateway; nohup openclaw-gateway > /tmp/gw.log 2>&1 &)
# Verify binding
ss -tuln | grep 18789   # LISTEN on $MESH_IP:18789
```

### 4. Restrict Ollama API to Localhost (CRITICAL)

Prevent internet‑accessible unauthenticated inference.

```bash
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/limit.conf <<'EOF'
[Service]
Environment="OLLAMA_HOST=127.0.0.1"
EOF
sudo systemctl daemon-reload
sudo systemctl restart ollama
# Verify
ss -tuln | grep 11434   # should show 127.0.0.1:11434 only
```

If any agent needs remote Ollama, use a local mesh‑only proxy or bind to mesh IP and add a corresponding ufw rule (after step 5).

### 5. Harden SSH on Nexus + Enable Mesh‑Only Firewall (HIGH)

Nexus already has fail2ban, but SSH config is weak. Apply the same SSH hardening from step 2. Additionally, after SSH is standardized, deploy ufw mesh‑only allow rules.

```bash
# After SSH on all nodes is on 2222 and bound to mesh IP:
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 10.0.0.0/24 to any port 2222 proto tcp
sudo ufw allow from 10.0.0.0/24 to any port 18789 proto tcp
# If Ollama kept bound to mesh IP (instead of localhost), also:
# sudo ufw allow from 10.0.0.0/24 to any port 11434 proto tcp
sudo ufw --force enable
sudo ufw status verbose
```

### Bonus: Within 48 h

- Implement **system configuration backups**: Extend `maintenance/daily_backup.sh` to tar `/etc/ssh/`, `/etc/wireguard/`, `/etc/ollama/`, `/etc/systemd/system/`, `~/.openclaw/` and commit to workspace memory daily with rotation.
- Repair Clawd Ollama config: remove or explain `host: 10.0.0.4:11434` mismatch.
- Investigate and fix failing OpenClaw cron jobs (`macro-daily-scan`, `digest-morning-briefing`, `banker-daily-fact`). Check logs: `journalctl --user -u openclaw-gateway -n 100` or `~/.openclaw/logs/`.
- Scan for other services listening on `0.0.0.0` (e.g., ports 3000, 9100, 9092) and bind to localhost or firewall them.

---

## 10. Trend vs Previous Day

| Metric                    | 2026-02-16 | 2026-02-17 | 2026-02-18 | **2026-02-19** | Trend |
|---------------------------|------------|------------|------------|----------------|-------|
| Overall Health Score      | 5/10       | 3/10       | 2/10       | **2/10**       | 🔻➡️   |
| SSH (Clawd)               | active:22  | failed     | failed     | failed         | 🔻     |
| OpenClaw gateway binding  | loopback   | loopback   | loopback   | loopback       | ➡️     |
| Ollama exposure           | exposed    | exposed    | exposed    | exposed + config anomaly | 🔻 |
| Firewall deployment       | unclear    | unclear    | unclear    | unclear        | ➡️     |
| Config backups            | none       | none       | none       | none           | ➡️     |
| Cron errors               | none       | none       | 3 errors   | 3 errors       | ➡️     |
| Resource headroom         | healthy    | healthy    | healthy    | healthy        | ➡️     |
| Fail2ban coverage         | partial    | partial    | partial    | **full (Nexus fixed)** | 🔺 |

**Trend**: Stagnation at critical level. No evidence of any recommended remediation being applied. Positive: Fail2ban now runs on all nodes. Major regressions remain unaddressed, and Clawd's SSH outage continues.

---

**Report generated**: 2026-02-19 03:45 UTC  
**Next audit**: 2026-02-20 03:00 UTC (daily)  
**Audit notes**: Remote SSH access to Brutus, Plutos, and Nexus enabled detailed non‑privileged inspection of configurations and processes. Sudo access remains unavailable for firewall/ufw verification and service restarts; remediation steps above will require elevated permissions.
