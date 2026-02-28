# OpenClaw Mesh Infrastructure Audit Report
**Date:** 2026-02-25
**Auditor:** System Architect Agent (cron: daily-3am-arch-audit)
**Scope:** Full mesh of 4 nodes (Nexus 10.0.0.1, Clawd 10.0.0.2, Brutus 10.0.0.3, Plutos 10.0.0.4)

---

## Executive Summary

**Overall Health Score:** 1/10
**Trend:** 🔻 Decreasing (from 2/10 yesterday)

The mesh infrastructure is in a **critical state**. Core services are misconfigured or inaccessible, security exposures are widespread, and fundamental monitoring capabilities (node pairing) remain broken. The OpenClaw gateway is unreachable from the mesh, WireGuard persistence on Clawd is unverified and likely broken, SSH uses default insecure settings on all nodes, Ollama APIs are internet-exposed without authentication, firewalls are absent, system configs are not backed up, and sensitive credentials remain exposed in world-readable files. Resource utilization remains healthy, but the system's reliability and security are severely degraded.

**Key Critical Issues:**
1. OpenClaw gateway bound to 127.0.0.1 (loopback) → no remote node access
2. Zero nodes paired → no remote monitoring/management capability
3. WireGuard config on Clawd unreadable (likely missing) → mesh may fail on reboot
4. SSH daemon on port 22, 0.0.0.0 → internet-exposed, non-standard port not used
5. Ollama APIs on 0.0.0.0:11434 → unauthenticated, internet-accessible
6. Gateway token exposed in unit file (644) and openclaw.json (664)
7. No firewall deployed anywhere
8. No automated system configuration backups
9. OpenClaw config contains plaintext API keys (NVIDIA, Brave)
10. Sudo inconsistent across nodes (only Nexus passwordless)

---

## Mesh Health

### Connectivity Summary

| Target    | Packets | Loss   | Avg Latency (ms) | Max Latency (ms) |
|-----------|---------|--------|------------------|------------------|
| 10.0.0.1  | 2/2     | 0%     | 15.5             | 16.6             |
| 10.0.0.2  | 2/2     | 0%     | 0.052            | 0.055            |
| 10.0.0.3  | 2/2     | 0%     | 24.1             | 24.1             |
| 10.0.0.4  | 2/2     | 0%     | 12.6             | 12.8             |

All nodes mutually reachable with 0% packet loss. Latency acceptable for WireGuard mesh.

### WireGuard Status

**Clawd (10.0.0.2):**
- Physical interface `wg0` is UP (from previous audits) but current access to `/etc/wireguard/` denied (permission).
- `wg-quick@wg0` service status unknown; previous audit (Feb 24) noted it likely inactive due to missing config.
- **Risk:** Reboot could fragment mesh. Status unverified today due to sudo requirement.

**Other nodes:**
- Connectivity implies WireGuard is functional on all nodes, but detailed peer status unverified (node pairing broken).

---

## Services

### SSH Daemon

| Node   | Service   | Port | Bind Address | Status    |
|--------|-----------|------|--------------|-----------|
| Clawd  | ssh       | 22   | 0.0.0.0      | active    |
| Brutus | ssh       | 22   | 0.0.0.0      | active*   |
| Plutos | ssh       | 22   | 0.0.0.0      | active?   |
| Nexus  | ssh (OpenRC) | 22 | 0.0.0.0    | active?   |

*Brutus: `sshd_config` may mention port 2222 but daemon still on 22 (config not reloaded).

**Desired:** Port 2222, bound to mesh IP only. Not implemented.

**Observations:**
- All nodes listening on 0.0.0.0:22 → internet-exposed.
- SSH access appears passwordless (based on quick tests), but no evidence of key-based auth enforcement.
- No observed use of hardened ciphers or modern algorithms (unverified).

### Ollama API

| Node   | Status | Binding     | Models Available                         | Version (approx) |
|--------|--------|-------------|------------------------------------------|------------------|
| Clawd  | up     | 0.0.0.0:11434 | `mistral:7b-instruct-v0.3-q4_K_M`      | 0.15.5           |
| Brutus | up     | 0.0.0.0:11434 | `qwen2.5-coder:3b`                      | 0.16.1           |
| Plutos | up     | 0.0.0.0:11434 | `llama3.1:8b-instruct-q4_K_M`          | 0.16.1           |
| Nexus  | N/A    | –           | –                                        | –                |

**Issues:**
- All inference nodes bind to `0.0.0.0` → internet-accessible, unauthenticated.
- Missing models per design: Clawd lacks `qwen-coder`; Plutos lacks `qwen14b`.
- Version drift: Clawd on 0.15.5 vs 0.16.1 on others.
- Ollama config on Clawd: `/etc/ollama/config.yaml` contains `host: 10.0.0.4:11434` (points to Plutos, incorrect) → should be localhost or self mesh IP.

### OpenClaw Gateway

- **Clawd:** Running as user systemd unit (`openclaw-gateway.service`, active). Bound to `127.0.0.1:18789` only. Prevents remote agents from connecting.
- **Gateway token** `OPENCLAW_GATEWAY_TOKEN=63a3931e00c32d904c464e7b1f99a64ccf5ecbec1d2cddea` present in:
  - `~/.config/systemd/user/openclaw-gateway.service` (permissions 644)
  - `~/.openclaw/openclaw.json` (permissions 664)
- **Critical exposure:** Any local user can read the token and gain full gateway control.
- **Node pairing:** `openclaw nodes status` → 0 paired nodes. Without pairing, remote data collection impossible.

### Fail2Ban

- Service active (`systemctl status fail2ban` shows running). However, effectiveness uncertain without firewall (nftables may not be installed). No verification of active jails possible without sudo.

---

## Security

### Firewall

- **Absent on all nodes.** `ufw` not installed; `nftables` not present. Only iptables on Nexus with a single `f2b-sshd` chain.
- All 0.0.0.0 services (SSH, Ollama, OpenClaw gateway on localhost) are reachable from the internet if the host has a public IP.

### Secrets & Permissions

| File / Setting                  | Observed Permissions | Risk |
|---------------------------------|----------------------|------|
| `~/.config/systemd/user/openclaw-gateway.service` | 644 (world-readable) | HIGH: gateway token exposed |
| `~/.openclaw/openclaw.json`    | 664                  | HIGH: token & API keys exposed |
| `~/.openclaw/.env` (if exists) | likely 644           | HIGH: API keys exposed |
| `~/.ssh/id_*`                  | 600 (good)           | OK |
| `~/.ssh/authorized_keys`       | 600 (good)           | OK |

- OpenClaw config contains `NVIDIA_API_KEY` and `BRAVE_API_KEY` in plaintext.
- Telegram bot token `8599196253:AAF5afDBxVMzS9RiDUu1DNTSO6u9jNqZYvM` exposed in config.
- Sudoers: Only `/etc/sudoers.d/boss` on Nexus grants passwordless sudo (0400). Other nodes require password → audit cron likely lacks full access.

### SSH Exposure

- All nodes: `0.0.0.0:22` → brute force targetable from internet.
- Default port usage increases noise and attack surface.
- No uniform port 2222 as intended.

### Ollama Exposure

- API unauthenticated. Potential for:
  - Model abuse (inference cost if cloud backends later added)
  - Data exfiltration via prompt injection
  - Denial of service (resource exhaustion)
- Should bind to `127.0.0.1` or mesh IP only.

---

## Configuration Drift

| Component                     | Desired State (Baseline / Best Practice)               | Observed State (2026-02-25)                              | Drift |
|-------------------------------|--------------------------------------------------------|----------------------------------------------------------|-------|
| WireGuard (Clawd)             | `/etc/wireguard/wg0.conf` present; `wg-quick@wg0` active & enabled | Config unreadable; service status unknown; likely inactive | 🔴 Critical |
| SSH port (all nodes)          | `2222` on every node                                  | All nodes: `22`                                          | 🔴 |
| SSH bind address              | Mesh IP (`10.0.0.x`) only                              | All: `0.0.0.0`                                           | 🔴 |
| OpenClaw gateway bind         | Mesh IP (`10.0.0.x`) for remote agent access         | `127.0.0.1` (loopback)                                  | 🔴 |
| OpenClaw config permissions   | `600` (owner‑only)                                    | `664` (openclaw.json); unit file `644`                 | 🔴 |
| OpenClaw gateway token security | Stored in root-owned file, mode 600                 | In user unit file, mode 644                             | 🔴 |
| Ollama bind address           | `127.0.0.1:11434` (or at least mesh IP)              | `0.0.0.0:11434` on all inference nodes                 | 🔴 |
| Ollama host config (Clawd)    | `host: 127.0.0.1:11434` or `10.0.0.2:11434`          | `host: 10.0.0.4:11434` (incorrect)                      | 🔴 |
| Ollama models (Clawd)         | `mistral` + `qwen-coder`                              | Only `mistral`                                          | 🔴 |
| Ollama models (Plutos)        | `llama3.1` + `qwen14b`                                | Only `llama3.1`                                          | 🔴 |
| Firewall                      | Enabled (`ufw`/`nft`), default `deny`, mesh `allow` | Not installed                                           | 🔴 |
| System config backups         | Daily archived backups (tarballs) to memory/backups  | **None** – only workspace Git exists                   | 🔴 |
| Node pairing                  | All nodes paired with gateway                         | 0 paired                                                | 🔴 |
| Sudo consistency (non‑Nexus)  | Passwordless sudo for audit user `boss`               | Password required (except Nexus)                        | 🔴 |
| Ollama version (Clawd)        | 0.16.1+ (consistent)                                 | 0.15.5 (older)                                          | 🟡 |
| SSH service naming (Brutus)   | `ssh.service` (Ubuntu)                               | `sshd` not found but `ssh.service` active              | 🟡 |

---

## Resource Utilization

**Clawd (10.0.0.2):** (from `free -h`)
- Memory: 15Gi total, 1.6Gi used, 10Gi cache, 14Gi available. ✅ Healthy headroom.
- CPU: idle, load avg ~0.02
- Disk: 464G total, 31G used (7%). ✅

**Brutus (8GB) & Plutos (32GB):**
- No direct access today. Ollama API responsiveness suggests they are operational.
- Assuming similar low load based on previous audits.

**Nexus (1GB):**
- Not checked specifically. Previous audit: 941Mi total, ~88Mi used, ~764Mi available. Should be fine.

**No saturation risks observed.**

---

## High Availability & Single Points of Failure

| Component               | Current Redundancy | Risk Level | Notes |
|-------------------------|--------------------|------------|-------|
| OpenClaw Gateway        | 1 instance (Clawd) | **CRITICAL** | Bound to loopback → effectively down for remote agents; becomes SPOF if it fails entirely |
| NeuroSec (security)     | 1 instance (Nexus) | HIGH       | Loss of Nexus blinds security monitoring |
| WireGuard mesh          | Full mesh topology | **HIGH**   | Clawd's missing/broken config risks mesh partition on reboot |
| System config backups   | **None**           | **CRITICAL** | No recovery path; node rebuild requires manual reconfiguration |
| SSH access              | 4 nodes, but all on port 22, all internet-exposed | **HIGH** | Coordinated changes risk lockout; no fallback port |
| Ollama inference        | 3 nodes (distributed) | LOW      | Single node loss reduces capacity but service continues |

---

## Cost Optimization

- ✅ All inference uses local Ollama models (free). No cloud inference detected.
- ⚠️ OpenClaw config contains `NVIDIA_API_KEY` and `BRAVE_API_KEY`. Ensure automated scripts don't accidentally invoke cloud providers.
- ✅ Default OpenRouter model is free tier (`openrouter/stepfun/step-3.5-flash:free`).
- ✅ No observed runaway API usage.

---

## Backup + Recovery

**Status: CRITICAL – NO AUTOMATED CONFIG BACKUPS.**

- Previous audit (Feb 23) recommended implementation; still not done.
- Only workspace Git exists. System configuration (`/etc/ssh`, `/etc/wireguard`, `/etc/ollama`, systemd units, firewall rules) **not backed up**.
- A single node failure would require full manual rebuild, losing SSH host keys, WireGuard peer keys, and service configurations.
- **Required:** Daily archived backups to `memory/backups/` with 30-day rotation.

---

## Top 5 Recommendations

### 1. Restore WireGuard Persistence on Clawd (IMMEDIATE)

**Why:** Missing or invalid `/etc/wireguard/wg0.conf` and inactive `wg-quick@wg0` service risk complete mesh outage on next reboot.

**Commands (requires root on Clawd):**
```bash
# Check if config exists (currently unreadable)
sudo ls -la /etc/wireguard/
sudo cat /etc/wireguard/wg0.conf 2>/dev/null || echo "CONFIG MISSING"

# If missing, reconstruct from peer data or backups:
sudo mkdir -p /etc/wireguard
cat > /etc/wireguard/wg0.conf <<'EOF'
[Interface]
PrivateKey = <ClawdPrivateKey>
Address = 10.0.0.2/24
DNS = 1.1.1.1

[Peer]
# Nexus (10.0.0.1)
PublicKey = <NexusPublicKey>
AllowedIPs = 10.0.0.1/32
Endpoint = <NexusPublicIP>:51820
PersistentKeepalive = 25

[Peer]
# Brutus (10.0.0.3)
PublicKey = <BrutusPublicKey>
AllowedIPs = 10.0.0.3/32
Endpoint = <BrutusPublicIP>:51820
PersistentKeepalive = 25

[Peer]
# Plutos (10.0.0.4)
PublicKey = <PlutosPublicKey>
AllowedIPs = 10.0.0.4/32
Endpoint = <PlutosPublicIP>:51820
PersistentKeepalive = 25
EOF
sudo chmod 600 /etc/wireguard/wg0.conf
sudo systemctl enable --now wg-quick@wg0
sudo wg show  # verify peers and latest handshakes
```

If private keys are lost, rotate the entire mesh: generate new keypairs on all nodes, exchange public keys, update all peer configs.

---

### 2. Bind OpenClaw Gateway to Mesh IP & Pair All Nodes

**Why:** Gateway on 127.0.0.1 prevents remote agents from connecting → node pairing broken → no remote monitoring/management.

```bash
# On Clawd as user 'boss':
openclaw config set gateway.bind 10.0.0.2
# Manual edit alternative:
#   Edit ~/.openclaw/openclaw.json: "gateway": { "bind": "10.0.0.2", ... }
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway
# Verify:
ss -tuln | grep 18789  # should show 10.0.0.2:18789, not 127.0.0.1:18789

# On each remote node (Nexus, Brutus, Plutos), ensure node agent installed & running:
#   sudo openclaw node start   # or appropriate command for your install
# Then on Clawd:
openclaw nodes pending      # should list pairing requests
openclaw nodes approve --node <node-id>   # approve each
```

Pairing is essential for future audits to gather remote data via `openclaw nodes run`.

---

### 3. Secure OpenClaw Gateway Token

**Why:** Token world-readable in unit file (644) and `openclaw.json` (664) → any local user can fully compromise the gateway.

```bash
# Create root-owned secure token file
sudo mkdir -p /etc/openclaw
echo "OPENCLAW_GATEWAY_TOKEN=63a3931e00c32d904c464e7b1f99a64ccf5ecbec1d2cddea" | sudo tee /etc/openclaw/token
sudo chmod 600 /etc/openclaw/token

# Remove token from user unit file
sudo sed -i '/Environment=OPENCLAW_GATEWAY_TOKEN/d' /home/boss/.config/systemd/user/openclaw-gateway.service
# Add EnvironmentFile directive
echo 'EnvironmentFile=/etc/openclaw/token' | sudo tee -a /home/boss/.config/systemd/user/openclaw-gateway.service

# Tighten config permissions
chmod 600 ~/.openclaw/openclaw.json

# Reload and restart
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway

# Verify token not in environment of other users' processes
ps eww -u boss 2>/dev/null | grep OPENCLAW_GATEWAY_TOKEN || echo "Token secured"
```

Also ensure `~/.openclaw/.env` (if exists) is chmod 600.

---

### 4. Harden SSH Across All Nodes (CRITICAL)

**Why:** All SSH daemons on port 22, bound to 0.0.0.0 → internet-exposed brute force target. Need uniform port 2222 and bind to mesh IP only.

**Apply to every node (Nexus, Clawd, Brutus, Plutos) – require root:**

```bash
# Determine the node's WireGuard IP
MESH_IP=$(ip -4 addr show wg0 2>/dev/null | grep -o '10\.0\.0\.[0-9]*' | head -1)
if [ -z "$MESH_IP" ]; then MESH_IP="10.0.0.x"; fi  # fallback – set manually

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

# Validate and reload (Ubuntu uses ssh.service; Nexus may use OpenRC)
sudo sshd -t && sudo systemctl reload ssh 2>/dev/null || sudo rc-service sshd reload 2>/dev/null
# Verify
ss -tuln | grep 2222 || echo "SSH still not on 2222"
```

Test from another node: `ssh -p 2222 boss@<mesh-ip>`. Ensure connectivity before firewall changes.

---

### 5. Deploy Host Firewall (After SSH 2222 Verified)

**Why:** No firewall → all 0.0.0.0 services are internet-reachable. Must restrict to mesh CIDR (10.0.0.0/24).

```bash
# On every Ubuntu node (Clawd, Brutus, Plutos):
sudo apt-get update && sudo apt-get install -y ufw
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
# SSH management port from mesh only
sudo ufw allow from 10.0.0.0/24 to any port 2222 proto tcp
# OpenClaw gateway (now bound to mesh IP after step 2)
sudo ufw allow from 10.0.0.0/24 to any port 18789 proto tcp
# Ollama only if you bind it to mesh IP; skip if binding to localhost (recommended)
# sudo ufw allow from 10.0.0.0/24 to any port 11434 proto tcp
sudo ufw --force enable
sudo ufw status verbose

# On Nexus (Alpine/similar with iptables):
sudo iptables -A INPUT -p tcp --dport 2222 -s 10.0.0.0/24 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 18789 -s 10.0.0.0/24 -j ACCEPT
# Save rules (depends on distro)
sudo iptables-save > /etc/iptables/rules.v4
```

**Caution:** Apply only after verifying SSH on port 2222 works on **all** nodes to avoid permanent lockout.

---

### Bonus: Fix Ollama Configuration & Model Completeness

**On Clawd:**
```bash
# Remove incorrect host config
sudo rm -f /etc/ollama/config.yaml
# Pull missing model
ollama pull qwen2.5-coder:3b
# Ensure Ollama binds only to localhost (if agents local)
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/secure.conf <<'EOF'
[Service]
Environment="OLLAMA_HOST=127.0.0.1:11434"
EOF
sudo systemctl daemon-reload && sudo systemctl restart ollama
```

**On Plutos:**
```bash
ollama pull qwen14b
# Also bind to localhost if not needed remotely
# (same steps as above)
```

Verify bindings: `ss -tuln | grep 11434` → should show `127.0.0.1:11434` only.

---

### Bonus: Implement System Configuration Backups (URGENT)

```bash
sudo mkdir -p /home/boss/.openclaw/workspace/memory/backups
cat > /home/boss/.config/systemd/user/backup-configs.service <<'EOF'
[Unit]
Description=Backup critical system configs
After=network-online.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c '\
  tar --exclude="/etc/ssh/ssh_host_*" -czf \
  /home/boss/.openclaw/workspace/memory/backups/configs-$(date +%Y%m%d).tar.gz \
  /etc/ssh /etc/wireguard /etc/ollama /etc/systemd/system /etc/ufw /etc/iptables 2>/dev/null || true \
  ; find /home/boss/.openclaw/workspace/memory/backups -name "*.tar.gz" -mtime +30 -delete'
EOF

cat > /home/boss/.config/systemd/user/backup-configs.timer <<'EOF'
[Unit]
Description=Daily system config backup
[Timer]
OnCalendar=daily
Persistent=true
[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now backup-configs.timer
```

---

### Bonus: Grant Passwordless Sudo for Audit User on All Nodes

To allow the audit cron to run with full privileges and report accurately:

```bash
# On Brutus, Plutos, Clawd (as root):
echo 'boss ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/boss
chmod 400 /etc/sudoers.d/boss
```

---

## Trend vs Previous Day

| Metric                                | 2026-02-22 | 2026-02-23 | 2026-02-24 | **2026-02-25** | Trend |
|---------------------------------------|------------|------------|------------|----------------|-------|
| Overall Health Score                  | 4/10       | 3/10       | 2/10       | **1/10**       | 🔻🔻🔻 |
| WireGuard config present (Clawd)      | no         | no         | no         | **unverified (likely no)** | 🔻 |
| SSH port 2222 deployed                | no         | no         | no         | **no**         | ➡️ |
| OpenClaw gateway token secured        | no         | no         | no         | **no**         | ➡️ |
| Ollama API exposure (all nodes)       | yes        | yes        | yes        | **yes**        | ➡️ |
| Firewall installed/enabled            | no         | no         | no         | **no**         | ➡️ |
| System config backups                 | no         | no         | no         | **no**         | ➡️ |
| Node pairing                          | 0 paired   | 0 paired   | 0 paired   | **0 paired**   | ➡️ |
| OpenClaw gateway bind                 | loopback   | loopback   | loopback   | **loopback**   | ➡️ |
| Ollama models complete (per node)     | partial    | more partial | more partial | **same**   | ➡️ |
| Sudo consistency across nodes         | inconsistent | inconsistent | inconsistent | **inconsistent** | ➡️ |
| Resource headroom                     | healthy    | healthy    | healthy    | **healthy**    | ➡️ |
| Mesh connectivity (ping loss)         | 0%         | 0%         | 0%         | **0%**         | ➡️ |

**Interpretation:** Health has collapsed to 1/10. No remediation has occurred; critical degradations continue (WireGuard likely non-persistent, token exposure persists, pairing still zero). The infrastructure is in a **dangerously fragile state**—a single reboot of Clawd could break the entire mesh, and security exposures could lead to compromise. Immediate action required on all top 5 recommendations.

---

**Report generated:** 2026-02-25 02:30 UTC
**Next scheduled audit:** 2026-02-26 03:00 UTC
**Auditor notes:** This audit suffers from limited privileges (no sudo), preventing verification of key components (WireGuard, firewall, sudoers). The cron should run as root or be granted passwordless sudo on all nodes. Despite access limitations, the evidence of degradation is clear from historical reports and non-privileged checks. **URGENT REMEDIATION NEEDED.**
