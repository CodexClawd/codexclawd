# System Architecture — Clawd Mesh

**Version:** 1.0  
**Date:** 2026-02-19  
**Status:** Production  
**Owner:** Flo (Boss)

---

## 1. Overview

A distributed AI infrastructure built on a WireGuard mesh network, with centralized access control via `clawd` as the entry point. The system supports multi-node Ollama inference, OpenClaw orchestration, and secure administration from a Mac Mini control center.

**Design Principles:**
- Defense in depth: internal nodes hidden behind `clawd`
- Single entry point: all external SSH goes through `clawd`
- Mesh networking: all nodes can reach each other via 10.0.0.0/24
- SSH ProxyJump: seamless access to internal nodes from Mac without manual tunneling
- Model distribution: different Ollama models on different nodes for specialization

---

## 2. Network Topology

### 2.1 WireGuard Mesh

All nodes are connected via a WireGuard VPN with subnet `10.0.0.0/24`:

| Node   | Mesh IP    | Role in Mesh      |
|--------|------------|-------------------|
| nexus  | 10.0.0.1   | Hub (optional)    |
| clawd  | 10.0.0.2   | Entry + peer      |
| brutus | 10.0.0.3   | Peer              |
| plutos | 10.0.0.4   | Peer              |

**Note:** The mesh is functional but `nexus` is currently not the hub; `clawd` serves as the entry point. WireGuard configuration exists on all nodes and the mesh is operational for inter-node communication.

### 2.2 Public Endpoints

| Node   | Public IP       | Open Ports               | Purpose                    |
|--------|-----------------|--------------------------|----------------------------|
| clawd  | 85.215.46.147  | 22 (SSH), 9092 (Grafana) | SSH entry, monitoring     |
| brutus | 87.106.6.144   | None (SSH mesh-only)     | Internal only             |
| plutos | 87.106.3.190   | 22 (SSH), 11434 (Ollama) | Direct SSH + Ollama API   |
| nexus  | None            | None (SSH mesh-only)     | Bastion, internal only    |

**Security Model:** Only `clawd` and `plutos` expose SSH to the internet. `brutus` and `nexus` are reachable **only via the mesh** (ProxyJump through `clawd`).

---

## 3. Nodes

### 3.1 clawd-16gb (ION-001)

**Provider:** IONOS (Germany)  
**Public IP:** 85.215.46.147  
**Mesh IP:** 10.0.0.2  
**OS:** Ubuntu 24.04 LTS  
**CPU:** AMD EPYC-Milan, 8 vCPUs  
**RAM:** 16 GB DDR4  
**Storage:** 480 GB NVMe SSD  
**Stack:** OpenClaw 2026.2.6-3, Ollama v0.15.5, Docker v28.2.2, Node v22.22.0  
**Ollama Model:** `mistral:7b-instruct-v0.3-q4_K_M`  
**Role:** OpenClaw Gateway, Telegram Bot, Binance/GitHub integrations, mesh entry point  
**SSH:** Port 22, public key auth only  
**Access:** Direct SSH from Mac (`ssh clawd`)  
**Color:** Pink (prompt: `boss@clawd-16gb`)

---

### 3.2 brutus-8gb (ION-002)

**Provider:** IONOS (Germany)  
**Public IP:** 87.106.6.144  
**Mesh IP:** 10.0.0.3  
**OS:** Ubuntu 24.04 LTS  
**CPU:** AMD EPYC-Milan, 6 vCPUs  
**RAM:** 8 GB DDR4  
**Storage:** 232 GB SSD  
**Stack:** Ollama v0.15.5  
**Ollama Model:** `qwen2.5-coder:3b`  
**Role:** Coding agent, mesh node (via ProxyJump)  
**SSH:** Port 22, mesh-only (no public SSH allowed by firewall design)  
**Access:** `ssh brutus` from Mac → ProxyJump through `clawd` → connects to `10.0.0.3`  
**Color:** Yellow (prompt: `boss@brutus-8gb`)

---

### 3.3 plutos-32gb (Stratos-001)

**Provider:** Stratos (Germany)  
**Public IP:** 87.106.3.190  
**Mesh IP:** 10.0.0.4  
**OS:** Ubuntu 24.04 LTS  
**Stack:** Ollama v0.15.5  
**Ollama Model:** `llama3.1:8b-instruct-q4_K_M`  
**Role:** Inference node (direct SSH, also in mesh)  
**SSH:** Port 22, public key auth only  
**Access:** Direct SSH from Mac (`ssh plutos`)  
**Notes:** Separately hosted on Stratos, not IONOS.

---

### 3.4 nexus-1gb (Servitro-001)

**Provider:** Servitro.com (Frankfurt)  
**Cost:** $12/year  
**Public IP:** None  
**Mesh IP:** 10.0.0.1  
**OS:** Alpine Linux  
**CPU:** AMD EPYC 7443P, 1 vCore  
**RAM:** 1 GB DDR4  
**Storage:** 10 GB SSD  
**Stack:** OpenSSH server (Alpine)  
**Role:** WireGuard hub, mesh gateway, security perimeter (future hardening)  
**SSH:** Port 22 (changed from 2222), mesh-only  
**Access:** `ssh nexus` from Mac → ProxyJump through `clawd` → connects to `10.0.0.1`  
**Current Status:** SSH running, key deployed, reachable via ProxyJump.

---

## 4. SSH Access Control

### 4.1 Mac ~/.ssh/config

```sshconfig
Host clawd
    HostName 85.215.46.147
    User boss
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking accept-new

Host nexus
    HostName 10.0.0.1
    User boss
    ProxyJump clawd
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking accept-new

Host brutus
    HostName 10.0.0.3
    User boss
    ProxyJump clawd
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking accept-new

Host plutos
    HostName 87.106.3.190
    User boss
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking accept-new
```

### 4.2 Access Flow

| Command             | Path                                             |
|---------------------|--------------------------------------------------|
| `ssh clawd`         | Mac → 85.215.46.147:22 (direct)                 |
| `ssh nexus`         | Mac → clawd → 10.0.0.1:22 (ProxyJump)          |
| `ssh brutus`        | Mac → clawd → 10.0.0.3:22 (ProxyJump)          |
| `ssh plutos`        | Mac → 87.106.3.190:22 (direct)                 |

### 4.3 Public Key Distribution

- Mac's `~/.ssh/id_ed25519.pub` is deployed to `~boss/.ssh/authorized_keys` on **all four nodes**.
- All nodes have `PasswordAuthentication no` (SSH keys only).
- Each node's SSH host keys were regenerated during setup.

---

## 5. Ollama Models

| Node   | Model                                 | Size   | Purpose       |
|--------|---------------------------------------|--------|---------------|
| clawd  | `mistral:7b-instruct-v0.3-q4_K_M`    | ~4 GB  | General chat  |
| brutus | `qwen2.5-coder:3b`                    | ~2 GB  | Coding tasks  |
| plutos | `llama3.1:8b-instruct-q4_K_M`        | ~5 GB  | Heavy inference |

**Usage:** Models are available locally on each node via `ollama generate <model>` or through OpenClaw's integration when spawning sessions on that node.

---

## 6. Security Model

### 6.1 Network Isolation

- **External Surface Area:** Only `clawd` (85.215.46.147) and `plutos` (87.106.3.190) have public SSH open.
- `brutus` and `nexus` have **no public SSH**; they are reachable exclusively via WireGuard mesh and ProxyJump.
- Inter-node traffic stays within the 10.0.0.0/24 private network; no node is exposed to the public internet except as noted.

### 6.2 SSH Hardening

- All nodes: `PasswordAuthentication no`, `PubkeyAuthentication yes`
- All nodes: `PermitRootLogin no` (root SSH disabled)
- All nodes: `UseDNS no` to prevent reverse lookup delays
- Firewall (where applicable):
  - `clawd`: UFW allows 22 and necessary services
  - `brutus`/`nexus`: external port 22 blocked by provider/firewall (mesh-only by design)
  - `plutos`: port 22 open, key-only

### 6.3 Monitoring

- Grafana running on `clawd` port 3000 (monitoring future work)
- Node metrics: `node_exporter` on `clawd` port 9100

---

## 7. OpenClaw Deployment

**Gateway:** Running on `clawd` (service: `openclaw-gateway`)  
**Node Connectivity:** OpenClaw can communicate with `brutus` and `plutos` via internal mesh IPs if needed for agent spawning.

**Agent Models:**
- When spawning a session, select model based on node:
  - Coding tasks → `brutus` (`qwen2.5-coder:3b`)
  - General chat → `clawd` (`mistral`)
  - Heavy analysis → `plutos` (`llama3.1`)

---

## 8. Backup & Recovery

### 8.1 SSH Config Backup

Location: `~/.ssh/config.backup` on Mac.  
Restore: `cp ~/.ssh/config.backup ~/.ssh/config`

### 8.2 Critical Credentials

- Mac SSH private key: `~/.ssh/id_ed25519` (keep secure)
- Node `boss` users: same key pair across all nodes
- No passwords stored; all key-based

### 8.3 Re-deploy Keys

If a node's `authorized_keys` is lost, from Mac:
```bash
cat ~/.ssh/id_ed25519.pub | ssh <node> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

---

## 9. Troubleshooting

### 9.1 Node Unreachable

```bash
# Test mesh connectivity
ping -c 2 10.0.0.x

# Test SSH via ProxyJump
ssh -vvv <node>
```

### 9.2 Host Key Changed

```bash
ssh-keygen -R <hostname or IP>
# Then reconnect to accept new key
```

### 9.3 SSH Agent Issues

If keys aren't being offered:
```bash
eval $(ssh-agent)
ssh-add ~/.ssh/id_ed25519
```

Or use explicit `-i` flag:
```bash
ssh -i ~/.ssh/id_ed25519 <node>
```

### 9.4 Ollama Not Running

On node:
```bash
systemctl status ollama  # Ubuntu
# or
rc-service ollama status # Alpine
```

Start if needed:
```bash
sudo systemctl start ollama
```

---

## 10. Future Work

- [ ] Formalize `sessions_spawn` targets for each node/model
- [ ] Add TLS encryption to Ollama API endpoints
- [ ] Set up automated backups of `/etc/ssh/sshd_config` and WireGuard configs
- [ ] Implement log aggregation (Loki/Vector) from all nodes
- [ ] Harden `nexus` as a true security bastion (fail2ban, port knocking)
- [ ] Document OpenClaw agent deployment procedure

---

## 11. Contact

**Owner:** Flo (Boss)  
**Last Verified:** 2026-02-19  
**Status:** All nodes operational, mesh healthy, SSH keys deployed
