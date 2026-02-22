# OpenClaw Mesh Infrastructure Audit Report
**Date:** 2026-02-21  
**Auditor:** System Architect Agent  
**Scope:** Full mesh of 4 nodes (Nexus, Clawd, Brutus, Plutos)

---

## Executive Summary

**Overall Health Score:** 6/10  
**Trend:** Baseline (no previous data available)

The mesh is operational with all core services up and responsive. However, several security and configuration issues require attention. Critical findings include exposure of the OpenClaw gateway token, inconsistent sudo privileges, misaligned SSH port configuration, and an incorrect Ollama host setting on the gateway node. Resource utilization is healthy across the cluster, and no active attacks or failures were observed.

---

## Mesh Health

### Connectivity Summary
| Target    | Packets | Loss   | Avg Latency (ms) | Max Latency (ms) |
|-----------|---------|--------|------------------|------------------|
| 10.0.0.1  | 20/20   | 0%     | 45.97            | 154.16           |
| 10.0.0.3  | 19/20   | 5%     | 47.64            | 52.06            |
| 10.0.0.4  | 20/20   | 0%     | 71.80            | 84.00            |

- WireGuard interfaces (`wg0`) are UP on all nodes with correct /24 addresses.
- No persistent packet loss; a single lost packet to Brutus likely due to transient scheduling.
- Nexus shows one high-latency spike (~154ms) but otherwise stable.

### Service Health

| Node    | SSH Daemon | Ollama API | OpenClaw Component |
|---------|------------|------------|--------------------|
| Nexus   | N/A (minimal) | Not installed | N/A                |
| Clawd   | Active (port 22) | Active (0.0.0.0:11434) | Gateway (pid 1069471) |
| Brutus  | Active (port 22, config says 2222) | Active (0.0.0.0:11434) | Node (pid 869233) |
| Plutos  | Active (port 22) | Active (0.0.0.0:11434) | Node (pid 1031) |

All Ollama instances respond to `/api/tags` with the expected model lists:
- Clawd: `mistral:7b-instruct-v0.3-q4_K_M`
- Brutus: `qwen2.5-coder:3b`
- Plutos: `llama3.1:8b-instruct-q4_K_M`

OpenClaw gateway (Clawd) and node processes (Brutus, Plutos) are running under user `boss`.

---

## Security

### Critical Exposures

1. **OpenClaw Gateway Token in World-Readable Unit File**  
   `/home/boss/.config/systemd/user/openclaw-gateway.service` contains `OPENCLAW_GATEWAY_TOKEN=63a3931e00c32d904c464e7b1f99a64ccf5ecbec1d2cddea` with permissions `-rw-rw-r--`. Any local user can read the token and potentially control the gateway.

2. **API Keys in World-Readable `.bashrc`**  
   HIBP_API_KEY and NVIDIA_API_KEY are stored in `/home/boss/.bashrc` (mode 644). Exposes potential third‑party API usage to all local users.

3. **Inconsistent Sudo Privileges**  
   Only Nexus runs passwordless sudo for `boss`. Clawd, Brutus, and Plutos require a password, preventing automated maintenance and incident response.

4. **SSH Port Inconsistency**  
   Brutus’ `sshd_config` sets `Port 2222`, but the daemon still listens on port 22. Other nodes use port 22. Desired state (2222 across all) is not enforced.

### Firewall & Exposure

Listening ports (non‑loopback) of interest:

| Node   | Ports (TCP)                          |
|--------|--------------------------------------|
| Clawd  | 22, 11434, 3000, 9092, 9100, 22000  |
| Brutus | 22, 11434, 22000, 8384 (loopback)  |
| Plutos | 22, 11434                           |
| Nexus  | 22                                  |

- Ollama (11434) is bound to `0.0.0.0` on all inference nodes. Should be restricted to mesh CIDR (10.0.0.0/24) via firewall.
- OpenClaw gateway port 18789 is correctly bound to 127.0.0.1.
- Additional services (Grafana on 3000, Prometheus node exporter on 9100) are exposed to the world on Clawd; review necessity.

We could not verify firewall rules (`ufw`/`nftables`) due to insufficient privileges on most nodes. Port scans confirm mesh traffic reaches the intended services.

---

## Configuration Drift

| Component | Desired State | Observed Drift |
|-----------|---------------|----------------|
| **Ollama host config** | Bind to local node IP or 0.0.0.0 | Clawd’s `/etc/ollama/config.yaml` points to `10.0.0.4:11434` (Plutos IP) while service override masks the issue. This is misleading and could break if override is removed. |
| **Ollama service overrides** | Consistent environment | Brutus sets `OLLAMA_HOST=0.0.0.0:11434` (explicit port), others set `0.0.0.0`. Functionally equivalent but could be standardized. |
| **SSH port** | All nodes 22 (or all 2222) | Brutus configured for 2222 but daemon still on 22; others on 22. Unintentional partial migration. |
| **WireGuard** | Identical configs across peers | Unable to compare (configs root‑only). Should validate that each peer’s `[Peer]` sections match. |
| **Systemd units** | Consistent restart policies | Plutos’ `ollama.service.d/override.conf` includes `Restart=always` and `RestartSec=10`; others lack these in override (they may be in main unit). Recommend centralizing. |

---

## Resource Utilization

All nodes have ample headroom:

| Node   | RAM Total | RAM Used | RAM Free | Load Avg (1m) |
|--------|-----------|----------|----------|---------------|
| Clawd  | 16 GB     | ~1.7 GB  | ~4.9 GB  | 0.06          |
| Brutus | 8 GB      | ~1.6 GB  | ~3.1 GB  | 0.06          |
| Plutos | 32 GB     | ~1.7 GB  | ~24.9 GB | 0.00          |
| Nexus  | 1 GB      | ~89 MB   | ~813 MB  | 0.13          |

No CPU or memory saturation detected. Disk space not yet checked; recommended to add to future audits.

---

## High Availability & Single Points of Failure

- **OpenClaw Gateway:** Only one instance (on Clawd). If it fails, external connectivity to the mesh is lost.
- **Telegram Bot:** Runs as part of the gateway process; no separate redundancy.
- **WireGuard Mesh:** Full‑mesh design survives single node loss.
- **Ollama Services:** Distributed across three nodes; losing one reduces capacity but maintains service.
- **Security Monitoring:** Nexus is the sole NeuroSec host; its loss would blind the SOC. Consider deploying a secondary NeuroSec instance on another node.

---

## Cost Optimization

- All Ollama models are local and free of inference costs.
- **Potential cost leaks:**  
  - NVIDIA_API_KEY may be used for paid cloud services. Audit usage or remove if unused.  
  - HIBP_API_KEY is rate‑limited free tier; ensure not exceeded.
- GitHub token is a personal access token; verify scopes and that it’s not used for automated CI that might consume GitHub‑hosted runner minutes.

No runaway cloud API keys detected in environment files beyond those noted.

---

## Backup + Recovery

No automated backup of critical configuration files (`/etc/ollama`, `/etc/ssh/sshd_config`, `/etc/wireguard`, `/etc/ufw`, `/etc/systemd/system/ollama.service*`) to the workspace `memory/` directory exists. Recommend implementing a daily rsync or git‑based backup with versioning.

---

## Top 5 Recommendations

### 1. Secure OpenClaw Gateway Token
**Why:** Token exposed to all local users.  
**Fix:**
```bash
sudo mkdir -p /etc/openclaw
echo "OPENCLAW_GATEWAY_TOKEN=63a3931e00c32d904c464e7b1f99a64ccf5ecbec1d2cddea" | sudo tee /etc/openclaw/token
sudo chmod 600 /etc/openclaw/token
sudo sed -i '/Environment=OPENCLAW_GATEWAY_TOKEN/d' /home/boss/.config/systemd/user/openclaw-gateway.service
echo 'EnvironmentFile=/etc/openclaw/token' | sudo tee -a /home/boss/.config/systemd/user/openclaw-gateway.service
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway
```

### 2. Standardize SSH Port & Sudo Access
**Why:** Inconsistent ports hinder management; lack of passwordless sudo blocks automation.  
**Fix (on each node, excluding Nexus if desired):**
```bash
# Set Port 22 (or 2222) and disable root login
echo -e "Port 22\nPermitRootLogin no\nPasswordAuthentication no" | sudo tee /etc/ssh/sshd_config
# Add passwordless sudo for boss
echo "boss ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/boss
sudo chmod 440 /etc/sudoers.d/boss
# Reload sshd
sudo systemctl reload sshd
```

### 3. Correct Ollama Host Configuration on Clawd
**Why:** `/etc/ollama/config.yaml` points to Plutos (10.0.0.4), which is incorrect and misleading.  
**Fix:**
```bash
echo "host: 0.0.0.0:11434" | sudo tee /etc/ollama/config.yaml
# If using systemd override only, file can be removed
# sudo rm /etc/ollama/config.yaml
sudo systemctl restart ollama
```

### 4. Harden Firewall for Mesh Services
**Why:** Ollama exposed to all interfaces; only mesh should reach it.  
**Fix (use `ufw` or `nftables`; example `ufw`):**
```bash
sudo ufw default deny incoming
sudo ufw allow from 10.0.0.0/24 to any port 22   # adjust if using 2222
sudo ufw allow from 10.0.0.0/24 to any port 11434
sudo ufw enable
```
*Exercise caution to avoid locking out SSH; test rules in a separate session first.*

### 5. Implement Configuration Backups
**Why:** No recovery path for lost configs.  
**Fix:** Create a daily cron job (3:05am) that archives critical directories into `memory/`:
```bash
mkdir -p /home/boss/.openclaw/workspace/memory/backups
cat > /home/boss/.config/systemd/user/backup-configs.service <<'EOF'
[Unit]
Description=Backup critical configs
After=network-online.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'tar czf /home/boss/.openclaw/workspace/memory/backups/configs-$(date +%Y%m%d).tar.gz /etc/ollama /etc/ssh /etc/wireguard /etc/ufw /etc/systemd/system/ollama*'
EOF

cat > /home/boss/.config/systemd/user/backup-configs.timer <<'EOF'
[Unit]
Description=Daily backup of critical configs

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

## Closing Notes

The mesh is a solid foundation but requires the above hardening steps to meet production security standards. Regular audits (weekly) are recommended. Focus on least‑privilege access, consistent configurations, and securing secrets.
