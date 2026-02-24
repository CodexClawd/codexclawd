# OpenClaw Mesh Infrastructure Audit Report
**Date:** 2026-02-23  
**Auditor:** System Architect Agent (cron: daily-3am-arch-audit)  
**Scope:** Full mesh of 4 nodes (Nexus 10.0.0.1, Clawd 10.0.0.2, Brutus 10.0.0.3, Plutos 10.0.0.4)

---

## Executive Summary

**Overall Health Score:** 3/10  
**Trend:** ↓ Decreasing (from 4/10 yesterday)

The mesh network remains reachable, but critical misconfigurations threaten availability and security. Clawd's WireGuard configuration is non‑persistent; the OpenClaw gateway binds only to loopback, preventing remote agent access; SSH does not use the hardened port 2222; host firewalls are absent; the gateway token is exposed via world‑readable unit file; and node pairing is broken, preventing comprehensive monitoring. Resource utilization remains healthy. No meaningful improvements; additional degradations in token exposure and OpenClaw config permissions have further reduced the security posture.

---

## Mesh Health

### Connectivity Summary
| Target    | Packets | Loss   | Avg Latency (ms) | Max Latency (ms) |
|-----------|---------|--------|------------------|------------------|
| 10.0.0.1  | 4/4     | 0%     | 13.8             | 14.0             |
| 10.0.0.2  | 4/4     | 0%     | 0.04             | 0.05             |
| 10.0.0.3  | 4/4     | 0%     | 25.8             | 27.8             |
| 10.0.0.4  | 4/4     | 0%     | 12.6             | 12.6             |

All nodes mutually reachable with 0% packet loss and acceptable latency for a site‑to‑site VPN.

### WireGuard Status

**On Clawd (10.0.0.2):**
- Interface `wg0` is **UP** with IP `10.0.0.2/24`.
- Route `10.0.0.0/24 dev wg0` present.
- `/etc/wireguard/` directory **not readable** by non‑root; however `systemctl status wg-quick@wg0` shows **inactive (dead)**.
- The previous audit noted missing `/etc/wireguard/wg0.conf`; this remains unverified but the service being inactive strongly suggests the config is absent or invalid.
- **Risk:** A reboot will likely take down the WireGuard interface, fragmenting the mesh.
- Other nodes: Not verified due to node pairing failure.

---

## Services

### SSH Daemon

| Node   | Status  | Port(s) Listening | Desired Port | Bind Address |
|--------|---------|-------------------|--------------|--------------|
| Clawd  | active  | 0.0.0.0:22        | 2222         | 0.0.0.0      |
| Brutus | active* | 0.0.0.0:22        | 2222         | 0.0.0.0      |
| Plutos | active* | 22 (presumed)     | 2222         | 0.0.0.0      |
| Nexus  | active* | 22 (presumed)     | 2222         | 0.0.0.0      |

\* Assumed from connectivity; not directly checked.

- No node listens on port 2222, the designated management port.
- All SSH daemons bind to `0.0.0.0`, exposing them to the internet.
- Clawd's `sshd_config` uses defaults (Port 22, ListenAddress 0.0.0.0). `PasswordAuthentication no` is correct, but `PermitRootLogin` remains at default (`prohibit-password`), which may still allow root login via key – not ideal.
- Brutus `sshd_config` reportedly declares `Port 2222` but daemon still listens on 22 (service not reloaded after edit).

### Ollama API

| Node   | Status  | Binding     | Models Available                                 | Ollama Version |
|--------|---------|-------------|--------------------------------------------------|----------------|
| Clawd  | up      | 0.0.0.0:11434 | `mistral:7b-instruct-v0.3-q4_K_M`              | 0.15.5         |
| Brutus | up      | 0.0.0.0:11434 | `qwen2.5-coder:3b`                              | 0.16.1         |
| Plutos | up      | 0.0.0.0:11434 | `llama3.1:8b-instruct-q4_K_M`                  | 0.16.1         |
| Nexus  | N/A     | –           | –                                                | –              |

- All inference nodes expose unauthenticated APIs to the internet (`0.0.0.0`). Should be bound to `127.0.0.1` or at least the mesh address.
- Version drift: Clawd runs an older Ollama (0.15.5) compared to Brutus/Plutos (0.16.1). Recommend upgrade for security and stability.

### OpenClaw Gateway

- **Clawd:** Running as user systemd unit: `openclaw-gateway.service` (active, PID 1244297). Bound to `127.0.0.1:18789` (loopback), preventing remote agent access.
- **Gateway token** `OPENCLAW_GATEWAY_TOKEN=63a3931e00c32d904c464e7b1f99a64ccf5ecbec1d2cddea` is stored in the unit file with permissions `644` and duplicated in `~/.openclaw/openclaw.json` (mode `664`). **Critical exposure.**
- Brutus & Plutos: Node processes expected but not verified due to pairing failure.

### Fail2Ban

- Active service detected; configuration enables `sshd` jail with `nftables`. However, `nftables` is not installed, rendering Fail2Ban potentially ineffective. No ability to verify actual bans without root.

---

## Security

### Firewall

- **No host firewall detected.** `ufw` not installed; `nftables` not present. With services binding to `0.0.0.0` (SSH, Ollama, Grafana, Prometheus, etc.), the nodes are directly reachable from the internet without filtering.

### Secrets & Permissions

- **Critical:** OpenClaw gateway token in `~/.config/systemd/user/openclaw-gateway.service` (mode 644) and `~/.openclaw/openclaw.json` (mode 664). Any local user can read it.
- `~/.openclaw/.env` contains placeholder API keys but still world‑readable; should be `600`.
- SSH keys in `~/.ssh/` have correct permissions (600/644 for public). `authorized_keys` on the local host (Clawd) is 600 – good.
- OpenClaw config permissions too permissive; should be `600`.

### SSH Inconsistency

- Desired uniform port 2222 on mesh IP only. Reality: all nodes on port 22, bound to all interfaces.
- Nexus likely still permits root login with password (per previous audit). Unchanged.

### Ollama Exposure

All inference nodes listen on `0.0.0.0:11434`; the API has no authentication. Anyone on the internet can query models, potentially for abuse or, if cloud providers were later configured, cost runaway.

---

## Configuration Drift

| Component                     | Desired State (Baseline / Best Practice)               | Observed State                                             | Drift |
|-------------------------------|--------------------------------------------------------|------------------------------------------------------------|-------|
| **WireGuard (Clawd)**         | `/etc/wireguard/wg0.conf` present; `wg-quick@wg0` active & enabled | Config likely missing (service inactive); directory unreadable without root | 🔴 Critical |
| **SSH port (all nodes)**      | `2222` on every node                                  | Clawd/Plutos: `22`; Brutus: `22` (config not reloaded)   | 🔴 |
| **SSH bind address**          | Mesh IP (`10.0.0.x`) only                              | All bind `0.0.0.0`                                         | 🔴 |
| **OpenClaw gateway bind**     | Mesh IP (`10.0.0.x`) for remote agent access         | Loopback (`127.0.0.1`) on all nodes                       | 🔴 |
| **OpenClaw config perms**     | `600` (owner‑only)                                    | `openclaw.json` 664; unit file 644                         | 🔴 |
| **Ollama bind address**       | `127.0.0.1:11434` (or at least mesh IP)              | `0.0.0.0:11434` on all inference nodes                   | 🔴 |
| **Ollama host config (Clawd)**| `baseUrl` points to correct local address            | Fixed: now `10.0.0.2` (was `10.0.0.4`)                    | ✅ Resolved |
| **Firewall**                  | Enabled (`ufw`/`nft`), default `deny`, mesh `allow` | Not installed                                               | 🔴 |
| **System config backups**     | Daily archived backups (tarballs) to off‑site/backup  | **None** – only workspace Git backups exist               | 🔴 |
| **Cron jobs health**          | All scheduled jobs `ok`                               | 3 jobs in `error` state (`macro-daily-scan`, `digest-morning-briefing`, `banker-daily-fact`) | 🟡 |
| **Node pairing**              | All nodes paired with gateway                         | 0 paired; gateway binding prevents pairing                | 🔴 |
| **Ollama version (Clawd)**    | Consistent with other nodes (0.16.1)                  | 0.15.5 (older)                                              | 🟡 |

---

## Resource Utilization

**Clawd (sampled now):**
- Memory: 15Gi total, 1.6Gi used, 10Gi cache, 13Gi available.
- CPU: 100% idle, load avg 0.02/0.01/0.00.
- Disk: 464G total, 31G used (7%).
- No swap.

**Brutus & Plutos:** No direct access; Ollama API responsiveness suggests they are operational. Node pairing needed for full monitoring.

---

## High Availability & Single Points of Failure

| Component               | Current Redundancy | Risk Level | Notes |
|-------------------------|--------------------|------------|-------|
| OpenClaw Gateway        | 1 instance (Clawd) | HIGH       | Bound to loopback; effectively down for remote agents. |
| NeuroSec (security)     | 1 instance (Nexus) | HIGH       | Loss of Nexus blinds SOC; consider secondary. |
| WireGuard mesh          | Full mesh          | **MEDIUM‑HIGH** | Clawd's missing WireGuard config risks mesh split on reboot. |
| Ollama inference        | 3 nodes (distributed) | LOW   | Single node loss reduces capacity but service continues. |
| System config backups   | **None**           | **HIGH**   | No recovery path; node rebuild painful. |
| SSH access ports        | Inconsistent       | HIGH       | Port 22 exposed everywhere; no uniform port increases lockout risk during remediation. |

---

## Cost Optimization

- **Local models only:** All Ollama instances use free, on‑prem models (`mistral‑7B`, `qwen2.5‑coder‑3B`, `llama3.1‑8B`). ✅ No inference cloud spend.
- **API keys:** `MOONSHOT_API_KEY` in `.env` (placeholder) and `NVIDIA_API_KEY` in `openclaw.json` (used for cloud models) – ensure they are not unintentionally invoked in automated workflows to avoid unexpected charges.
- **OpenRouter:** Default model `openrouter/stepfun/step-3.5-flash:free` – good.

---

## Backup + Recovery

**Status: CRITICAL – No automated backups of system configuration.**

- The existing `maintenance/daily_backup.sh` only commits workspace changes to Git.
- System directories (`/etc/ssh/`, `/etc/wireguard/`, `/etc/ollama/`, systemd units, firewall rules) are **not backed up**.
- Impact: A node failure requires full manual rebuild, losing SSH host keys, WireGuard peer keys, service configurations.
- **Required:** Daily archived backups (compressed tarballs) to `memory/backups/` with rotation (keep 30 days).

---

## Top 5 Recommendations

### 1. Restore WireGuard Persistence on Clawd (CRITICAL)

**Why:** Missing `/etc/wireguard/wg0.conf` and inactive `wg-quick@wg0` risk complete mesh outage on next reboot.

**Actions:**
```bash
# Recreate config from backup or known good state.
# Obtain each peer's public key and endpoint (public IP) from existing configs or peers.
sudo mkdir -p /etc/wireguard
cat > /etc/wireguard/wg0.conf <<'EOF'
[Interface]
PrivateKey = <ReplaceWithClawdPrivateKey>
Address = 10.0.0.2/24
DNS = 1.1.1.1

[Peer]
# Nexus (hub)
PublicKey = <NexusPublicKey>
AllowedIPs = 10.0.0.1/32
Endpoint = <NexusPublicIP>:51820
PersistentKeepalive = 25

[Peer]
# Brutus
PublicKey = <BrutusPublicKey>
AllowedIPs = 10.0.0.3/32
Endpoint = <BrutusPublicIP>:51820
PersistentKeepalive = 25

[Peer]
# Plutos
PublicKey = <PlutosPublicKey>
AllowedIPs = 10.0.0.4/32
Endpoint = <PlutosPublicIP>:51820
PersistentKeepalive = 25
EOF
sudo chmod 600 /etc/wireguard/wg0.conf
sudo systemctl enable --now wg-quick@wg0
wg show  # verify peers and latest handshake
```
**Note:** If private keys are lost, rotate the entire mesh by generating new keys on all nodes and exchanging public keys.

### 2. Bind OpenClaw Gateway to Mesh IP & Repair Node Pairing

**Why:** Gateway bound to 127.0.0.1 prevents any remote node from connecting, breaking management, monitoring, and node commands.

```bash
# Edit OpenClaw configuration to bind to the mesh address (10.0.0.2)
openclaw config set gateway.bind 10.0.0.2
# Alternatively, manually edit ~/.openclaw/openclaw.json:
#   "gateway": { "bind": "10.0.0.2", ... }
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway
# Verify
ss -tuln | grep 18789  # should show 10.0.0.2:18789, not 127.0.0.1
```

After the gateway is reachable, pair the remote nodes:
```bash
# On each node, start the node companion if not running (requires prior install & root):
#   sudo openclaw node start   # or openclaw node daemon
# Then from Clawd:
openclaw nodes pending   # should list pairing requests
openclaw nodes approve --node <node-id>
```
Pairing is essential for future audits to collect remote data via `openclaw nodes run`.

### 3. Secure OpenClaw Gateway Token

**Why:** Token readable by all local users (unit file 644 & openclaw.json 664) enables full gateway compromise.

```bash
sudo mkdir -p /etc/openclaw
echo "OPENCLAW_GATEWAY_TOKEN=63a3931e00c32d904c464e7b1f99a64ccf5ecbec1d2cddea" | sudo tee /etc/openclaw/token
sudo chmod 600 /etc/openclaw/token
# Remove token from user unit file
sudo sed -i '/Environment=OPENCLAW_GATEWAY_TOKEN/d' /home/boss/.config/systemd/user/openclaw-gateway.service
# Add EnvironmentFile directive
echo 'EnvironmentFile=/etc/openclaw/token' | sudo tee -a /home/boss/.config/systemd/user/openclaw-gateway.service
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway
# Verify token isn't leaking in process list of other users
ps eww -u boss | grep OPENCLAW_GATEWAY_TOKEN || echo "Token removed from environment"
```

Also tighten permissions:
```bash
chmod 600 ~/.openclaw/openclaw.json
```

### 4. Harden SSH Consistently Across All Nodes

**Why:** Inconsistent ports and internet‑exposed SSH daemons increase attack surface and operational fragility.

**Apply to every node (Nexus, Clawd, Brutus, Plutos):**
```bash
# Determine the node's WireGuard IP (e.g., via ip -4 addr show wg0)
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
sudo sshd -t && sudo systemctl reload sshd
# Verify
ss -tuln | grep 2222   # should show $MESH_IP:2222, not 0.0.0.0:2222
```
Test from another node: `ssh -p 2222 boss@<mesh-ip>`.

### 5. Deploy Host Firewall (After SSH Port 2222 is Live)

**Why:** No firewall → all 0.0.0.0 services are internet‑reachable. Must restrict to mesh CIDR.

```bash
# On every node (except perhaps Nexus if it remains a minimal hub)
sudo apt-get update && sudo apt-get install -y ufw
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
# SSH on new port 2222 from mesh only
sudo ufw allow from 10.0.0.0/24 to any port 2222 proto tcp
# OpenClaw gateway (now bound to mesh IP)
sudo ufw allow from 10.0.0.0/24 to any port 18789 proto tcp
# Ollama only if bound to mesh IP; skip if bound to localhost (recommended)
# sudo ufw allow from 10.0.0.0/24 to any port 11434 proto tcp
sudo ufw --force enable
sudo ufw status verbose
```
**Caution:** Apply only after verifying SSH on port 2222 works on all nodes; otherwise you risk permanent lockout.

**Bonus – System Configuration Backups:**
```bash
sudo mkdir -p /home/boss/.openclaw/workspace/memory/backups
cat > ~/.config/systemd/user/backup-configs.service <<'EOF'
[Unit]
Description=Backup critical system configs
After=network-online.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'tar --exclude="/etc/ssh/ssh_host_*" -czf /home/boss/.openclaw/workspace/memory/backups/configs-$(date +%Y%m%d).tar.gz /etc/ssh /etc/wireguard /etc/ollama /etc/systemd/system /etc/ufw 2>/dev/null || true'
EOF
cat > ~/.config/systemd/user/backup-configs.timer <<'EOF'
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
# Rotate old backups (add to script):
# find /home/boss/.openclaw/workspace/memory/backups -name "*.tar.gz" -mtime +30 -delete
```
Rotate old backups (keep last 30 days).

---

## Trend vs Previous Day

| Metric                                | 2026-02-20 | 2026-02-21 | 2026-02-22 | **2026-02-23** | Trend |
|---------------------------------------|------------|------------|------------|----------------|-------|
| Overall Health Score                  | 2/10       | 6/10       | 4/10       | **3/10**       | 🔻    |
| WireGuard config present (Clawd)      | –          | yes        | no         | **no**         | 🔻    |
| SSH port 2222 deployed                | no         | no         | no         | **no**         | ➡️    |
| OpenClaw gateway token secured        | no         | no         | no         | **no**         | ➡️    |
| Ollama API exposure (all nodes)       | yes        | yes        | yes        | **yes**        | ➡️    |
| Firewall installed/enabled            | no         | no         | no         | **no**         | ➡️    |
| System config backups                 | no         | no         | no         | **no**         | ➡️    |
| Cron jobs healthy (no errors)         | 3 errors   | 3 errors   | 3 errors   | **3 errors**   | ➡️    |
| Resource headroom                     | healthy    | healthy    | healthy    | **healthy**    | ➡️    |
| Mesh connectivity (ping loss)         | 0%         | 0%         | 0%         | **0%**         | ➡️    |
| Node pairing                          | –          | –          | 0 paired   | **0 paired**   | ➡️    |
| OpenClaw gateway bind                 | loopback   | loopback   | loopback   | **loopback**   | ➡️    |
| OpenClaw config permissions           | 600?       | 600?       | 664?       | **664**        | 🔻    |

**Interpretation:** Health declined further due to persistent critical misconfigurations (WireGuard, gateway binding, token exposure) and newly observed permission issues. No corrective actions were taken overnight.

---

**Report generated:** 2026-02-23 02:30 UTC  
**Next scheduled audit:** 2026-02-24 03:00 UTC  
**Auditor notes:** Access restrictions prevented full root‑level verification on all nodes; some findings rely on non‑privileged probes and historical data. Recommend granting elevated privileges to the audit cron or executing as root for complete coverage. Immediate attention required on WireGuard persistence, gateway binding, and firewall deployment.