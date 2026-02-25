# OpenClaw Mesh Infrastructure Audit Report
**Date:** 2026-02-24  
**Auditor:** System Architect Agent (cron: daily-3am-arch-audit)  
**Scope:** Full mesh of 4 nodes (Nexus 10.0.0.1, Clawd 10.0.0.2, Brutus 10.0.0.3, Plutos 10.0.0.4)

---

## Executive Summary

**Overall Health Score:** 2/10  
**Trend:** ↓ Decreasing (from 3/10 yesterday)

The mesh network remains reachable, but critical misconfigurations have increased. WireGuard on Clawd remains non-persistent, the OpenClaw gateway is still bound to loopback, SSH daemons expose port 22 to the internet, Ollama APIs are unauthenticated, host firewalls are absent, system config backups are nonexistent, and node pairing is disabled. Additional drifts include missing Ollama models on Clawd and Plutos, incorrect Ollama bind config on Clawd, inconsistent sudo privileges, and service naming issues. Resource utilization is healthy. No immediate exfiltration signs.

---

## Mesh Health

### Connectivity Summary
| Target    | Packets | Loss   | Avg Latency (ms) | Max Latency (ms) |
|-----------|---------|--------|------------------|------------------|
| 10.0.0.1  | 4/4     | 0%     | 13.8             | 14.0             |
| 10.0.0.2  | 4/4     | 0%     | 0.04             | 0.05             |
| 10.0.0.3  | 4/4     | 0%     | 25.8             | 27.8             |
| 10.0.0.4  | 4/4     | 0%     | 12.6             | 12.6             |

All nodes mutually reachable with 0% packet loss.

### WireGuard Status

**Clawd (10.0.0.2):**  
- `wg0` interface exists, but `wg show` denied (permission).  
- `/etc/wireguard/wg0.conf` unreadable; `wg-quick@wg0` service likely inactive (previously confirmed inactive).  
- **Risk:** Reboot will likely fragment the mesh.

**Nexus (10.0.0.1):**  
- WireGuard active (OpenRC). Peers: Clawd (10.0.0.2), Brutus (10.0.0.3), and an entry for 10.0.0.5 (Plutos is 10.0.0.4 – misconfiguration).  
- Listening on 51820, keepalive 25s.

**Brutus & Plutos:**  
- Port 51820 LISTEN; SSH allowed `sudo -n` fails, so detailed status unavailable.

---

## Services

### SSH Daemon

| Node   | Service Name | Port | Bind Address | Status |
|--------|--------------|------|--------------|--------|
| Clawd  | ssh          | 22   | 0.0.0.0      | active |
| Brutus | ssh.service  | 22   | 0.0.0.0      | active (sshd unit not found) |
| Plutos | ssh.service  | 22   | 0.0.0.0      | active |
| Nexus  | (OpenRC)     | 22   | 0.0.0.0      | active |

**Desired:** Port 2222 on mesh IP only. All nodes violate.

### Ollama API

| Node   | Status | Binding     | Models Available                         | Version |
|--------|--------|-------------|------------------------------------------|---------|
| Clawd  | up     | 0.0.0.0:11434 | `mistral:7b-instruct-v0.3-q4_K_M`      | 0.15.5  |
| Brutus | up     | 0.0.0.0:11434 | `qwen2.5-coder:3b`                      | 0.16.1  |
| Plutos | up     | 0.0.0.0:11434 | `llama3.1:8b-instruct-q4_K_M`          | 0.16.1  |
| Nexus  | N/A    | –           | –                                        | –       |

- Missing models: Clawd should also have qwen-coder; Plutos should also have qwen14b.  
- All inference nodes expose API unauthenticated to the internet.

### OpenClaw Gateway

- Only on Clawd; running as user service (`openclaw-gateway`), bound to 127.0.0.1:18789 → inaccessible to other nodes.  
- Gateway token readable by all users in unit file (644) and ~/.openclaw/openclaw.json (664). **Critical exposure.**

### Fail2Ban

- Active on all nodes (Clawd, Brutus, Plutos, Nexus). On Nexus uses iptables; on others likely nftables but nft not installed (see Security).

---

## Security

### Firewall

- **No host firewall deployed.** `ufw` absent; `nftables` absent on Ubuntu nodes; only iptables on Nexus with a single `f2b-sshd` jump chain. All services exposing `0.0.0.0` are internet‑reachable.

### Secrets & Permissions

- `~/.openclaw/.env` contains placeholder API keys; world‑readable.  
- Gateway token exposed via unit file and `openclaw.json`.  
- Sudoers: Only `/etc/sudoers.d/boss` on Nexus grants passwordless sudo (0400). Brutus, Plutos, Clawd require password.  
- SSH keys and host configs have proper permissions.

### SSH Hardening

- All nodes listen on port 22, not 2222. Bind address 0.0.0.0. Brutus’s sshd unit missing but `ssh.service` active.

### Ollama Exposure

- All inference nodes bind `0.0.0.0:11434`. Unauthenticated API allows anyone to query models.

### Node Pairing

- `openclaw nodes status` → 0 paired nodes. Without pairing, gateway cannot run remote commands or gather telemetry.

---

## Configuration Drift

| Component                     | Desired State                                          | Observed State                                     | Drift |
|-------------------------------|--------------------------------------------------------|----------------------------------------------------|-------|
| WireGuard (Clawd)             | wg0.conf present; wg-quick@wg0 active & enabled       | Config unreadable; service inactive               | 🔴    |
| SSH port (all)                | 2222                                                   | 22                                                 | 🔴    |
| SSH bind address              | Mesh IP (10.0.0.x) only                                | 0.0.0.0                                            | 🔴    |
| OpenClaw gateway bind         | Mesh IP for remote agent access                       | 127.0.0.1                                          | 🔴    |
| OpenClaw config perms         | 600                                                    | 664 / 644                                          | 🔴    |
| Ollama bind address           | 127.0.0.1 or mesh IP                                   | 0.0.0.0 on all inference nodes                    | 🔴    |
| Ollama host config (Clawd)    | host: 10.0.0.2:11434                                   | host: 10.0.0.4:11434 (wrong)                      | 🔴    |
| Ollama models (Clawd)         | `mistral` + `qwen-coder`                               | only `mistral`                                     | 🔴    |
| Ollama models (Plutos)        | `llama3.1` + `qwen14b`                                | only `llama3.1`                                    | 🔴    |
| Firewall                     | ufw/nft enabled, default deny, mesh allow             | Not installed                                      | 🔴    |
| System config backups         | Daily archived backups to workspace/memory            | None                                               | 🔴    |
| Node pairing                 | All nodes paired                                       | 0 paired                                           | 🔴    |
| Sudo consistency (non‑Nexus)  | Passwordless sudo for audit user `boss`               | Password required                                  | 🔴    |
| SSH service naming (Brutus)   | ssh.service (Ubuntu)                                   | `sshd` not found but ssh.service active          | 🟡    |
| Ollama version (Clawd)        | 0.16.1+ (consistent)                                 | 0.15.5                                             | 🟡    |

---

## Resource Utilization

- **Clawd:** 15Gi RAM, 1.6Gi used, 13Gi available. CPU idle.
- **Brutus:** 7.7Gi RAM, 1.8Gi used, 5.9Gi available.
- **Plutos:** 31Gi RAM, 1.9Gi used, 29Gi available.
- **Nexus:** 941Mi RAM, 87.8Mi used, 764Mi available.

No saturation; load averages near zero.

---

## High Availability & Single Points of Failure

- **OpenClaw gateway:** single instance on Clawd, inaccessible remotely → SPOF for management.
- **NeuroSec:** only on Nexus; loss blinds security monitoring.
- **WireGuard:** Clawd’s missing config risks mesh loss on reboot.
- **System config backups:** none → node rebuilds extremely painful.
- **SSH access:** all on port 22 → lockout risk during coordinated changes.
- **Ollama models:** distributed but no per‑model redundancy.

---

## Cost Optimization

- All inference uses local Ollama models (free). ✅  
- No cloud API usage detected. `.env` has placeholder keys.  
- Default OpenRouter model is free tier; ensure fallback to local when network flaky.

---

## Backup + Recovery

- **CRITICAL:** No automated backups of `/etc/ssh`, `/etc/wireguard`, `/etc/ollama`, systemd units, firewall rules. Only workspace Git exists. Implement daily backups now.

---

## Top 5 Recommendations

### 1. Restore WireGuard Persistence on Clawd
```bash
# As root on Clawd
mkdir -p /etc/wireguard
cat > /etc/wireguard/wg0.conf <<'EOF'
[Interface]
PrivateKey = <ActualClawdPrivateKey>
Address = 10.0.0.2/24
DNS = 1.1.1.1

[Peer]
# Nexus
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
chmod 600 /etc/wireguard/wg0.conf
systemctl enable --now wg-quick@wg0
wg show
```
If keys lost, rotate all peers.

### 2. Bind OpenClaw Gateway to Mesh IP and Pair Nodes
```bash
# On Clawd (as boss)
openclaw config set gateway.bind 10.0.0.2
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway
ss -tuln | grep 18789  # should show 10.0.0.2:18789

# On each node, install/start node agent (root)
sudo openclaw node start
# On Clawd:
openclaw nodes pending
openclaw nodes approve --node <id>
```

### 3. Secure OpenClaw Gateway Token
```bash
sudo mkdir -p /etc/openclaw
echo "OPENCLAW_GATEWAY_TOKEN=<actual-token>" | sudo tee /etc/openclaw/token
sudo chmod 600 /etc/openclaw/token
sudo sed -i '/Environment=OPENCLAW_GATEWAY_TOKEN/d' /home/boss/.config/systemd/user/openclaw-gateway.service
echo 'EnvironmentFile=/etc/openclaw/token' | sudo tee -a /home/boss/.config/systemd/user/openclaw-gateway.service
chmod 600 ~/.openclaw/openclaw.json ~/.openclaw/.env
systemctl --user daemon-reload && systemctl --user restart openclaw-gateway
ps eww -u boss | grep OPENCLAW_GATEWAY_TOKEN || echo "Token secured"
```

### 4. Harden SSH Everywhere
```bash
# On each node (as root)
MESH_IP=$(ip -4 addr show wg0 | grep -o '10\.0\.0\.[0-9]*')
cat > /etc/ssh/sshd_config <<EOF
Port 2222
ListenAddress $MESH_IP
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AllowUsers boss
UsePAM yes
Subsystem sftp /usr/lib/openssh/sftp-server
EOF
sshd -t
if systemctl is-active --quiet ssh; then systemctl reload ssh; elif systemctl is-active --quiet sshd; then systemctl reload sshd; else rc-service sshd restart; fi
ss -tuln | grep 2222
```
Test from another node: `ssh -p 2222 boss@<mesh-ip>`.

### 5. Deploy Firewall After SSH Is Stable
```bash
# Ubuntu nodes
apt-get update && apt-get install -y ufw
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow from 10.0.0.0/24 to any port 2222 proto tcp
ufw allow from 10.0.0.0/24 to any port 18789 proto tcp
ufw --force enable
ufw status verbose

# Nexus (Alpine) – iptables
iptables -A INPUT -p tcp --dport 2222 -s 10.0.0.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 18789 -s 10.0.0.0/24 -j ACCEPT
# Ensure policy DROP or restrict other INPUT after allowing established/related
iptables-save > /etc/iptables/rules.v4
```
**Caution:** Apply only after step 4 verified on all nodes.

---

### Bonus: Pull Missing Models
- Clawd: `ollama pull qwen2.5-coder:3b`
- Plutos: `ollama pull qwen14b:latest`

### Bonus: Unified Sudo for Audit User
```bash
# On Brutus, Plutos, Clawd (as root)
echo 'boss ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/boss
chmod 400 /etc/sudoers.d/boss
```

### Bonus: Config Backups
```bash
cat > /etc/cron.daily/backup-configs <<'EOF'
#!/bin/sh
tar --exclude='/etc/ssh/ssh_host_*' -czf /home/boss/.openclaw/workspace/memory/backups/configs-$(date +%Y%m%d).tar.gz \
  /etc/ssh /etc/wireguard /etc/ollama /etc/systemd/system /etc/ufw 2>/dev/null || true
find /home/boss/.openclaw/workspace/memory/backups -name "*.tar.gz" -mtime +30 -delete
EOF
chmod +x /etc/cron.daily/backup-configs
```

---

## Trend vs Previous Day

| Metric                                | 2026-02-23 | **2026-02-24** | Trend |
|---------------------------------------|------------|----------------|-------|
| Overall Health Score                  | 3/10       | **2/10**       | 🔻    |
| WireGuard config present (Clawd)      | no         | **no**         | ➡️    |
| SSH port 2222 deployed                | no         | **no**         | ➡️    |
| OpenClaw gateway token secured        | no         | **no**         | ➡️    |
| Ollama API exposure                   | yes        | **yes**        | ➡️    |
| Firewall installed/enabled            | no         | **no**         | ➡️    |
| System config backups                 | no         | **no**         | ➡️    |
| Cron jobs healthy                     | 3 errors   | **0 errors**   | ✅    |
| Mesh connectivity (ping loss)         | 0%         | **0%**         | ➡️    |
| Node pairing                          | 0 paired   | **0 paired**   | ➡️    |
| OpenClaw gateway bind                 | loopback   | **loopback**   | ➡️    |
| Ollama models complete (per node)     | partial    | **more partial**| 🔻   |
| Sudo consistency across nodes         | inconsistent | **inconsistent** | ➡️   |

**Interpretation:** Health declined further due to additional drift (missing models, bad Ollama bind, inconsistent sudo) and lack of remediation. Cron jobs improved but core reliability and security gaps remain unfixed.

---

**Report generated:** 2026-02-24 02:30 UTC  
**Next scheduled audit:** 2026-02-25 03:00 UTC  
**Auditor notes:** Remote nodes were accessible via SSH as user `boss`, but passwordless sudo only on Nexus. This limited verification of firewall rules, WireGuard status, and sudoers on other nodes. Recommend granting uniform sudo to the audit user or running the cron as root for full coverage. Immediate action needed on WireGuard persistence, gateway binding, and SSH hardening to avoid service disruption.
