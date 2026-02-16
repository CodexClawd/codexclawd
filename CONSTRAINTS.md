# CONSTRAINTS.md — NeuroSec Operational Boundaries

## Tool Permissions Matrix

| Tool | Permission | Rationale |
|------|------------|-----------|
| **read** | ✅ ALLOW | Core scanning capability. Read-only constraint enforced. |
| **process** | ⚠️ ALLOW (read-only) | Process inspection only (`ps`, `netstat`). No `kill`, no `nice`, no signals. |
| **exec** | ⚠️ ALLOW (whitelist) | `stat`, `find`, `ls`, `netstat`, `lsof` only. No shell execution of user input. |
| **apply_patch** | ❌ DENY | Write capability. Violates read-only constraint. |
| **write** | ❌ DENY | Write capability. Alert files use atomic temp→mv via agent framework only. |
| **edit** | ❌ DENY | Modification capability. Violates read-only constraint. |
| **sessions_spawn** | ❌ DENY | Process creation capability. Risk of execution diversion. |
| **browser** | ❌ DENY | External network access. Violates egress policy. |
| **nodes** | ❌ DENY | Remote system access. Violates network containment. |
| **cron** | ⚠️ ALLOW (self-only) | May read own cron configuration. Cannot create/modify cron jobs. |
| **memory_write** | ⚠️ ALLOW (append-only) | Alert history, baseline updates. Append-only, timestamped, tamper-evident. |

## Resource Limits

| Resource | Limit | Enforcement |
|----------|-------|-------------|
| **CPU Time** | 30 seconds per scan | Hard timeout via agent framework |
| **RAM Usage** | 512 MB maximum | OOM killer protection; agent monitoring |
| **File Size** | 10 MB read limit | Skip files >10MB to prevent DoS via log poisoning |
| **Scan Depth** | 5 directory levels | Prevent infinite recursion on circular symlinks |
| **Alert Rate** | 1 alert per second | Prevent alert flooding; queue excess |
| **Concurrent Scans** | 1 | Single-threaded to prevent resource exhaustion |

## Network Policy

### Egress
| Destination | Status | Notes |
|-------------|--------|-------|
| localhost:11434 | ✅ ALLOW | Ollama model verification only |
| 127.0.0.1/8 | ❌ DENY | No loopback services except 11434 |
| 10.0.0.0/8 | ❌ DENY | No private network access |
| 172.16.0.0/12 | ❌ DENY | No private network access |
| 192.168.0.0/16 | ❌ DENY | No private network access |
| 0.0.0.0/0 | ❌ DENY | No external network access |
| DNS (UDP 53) | ❌ DENY | No name resolution; use /etc/hosts only |

### Ingress
| Type | Status | Notes |
|------|--------|-------|
| All incoming connections | ❌ DENY | NeuroSec is client-only; no listener |
| ICMP | ❌ DENY | No ping responses |

## Docker/AppArmor Sandbox Configuration

### Docker Flags (Reference)
```bash
docker run \
  --read-only \
  --security-opt no-new-privileges:true \
  --cap-drop ALL \
  --cap-add SYS_PTRACE \
  --network none \
  --memory=512m \
  --cpus=0.5 \
  --pids-limit=100 \
  -v /home/boss/.openclaw/workspace:/workspace:ro \
  -v /home/boss/.openclaw/workspace-neurosec/alerts:/alerts:rw \
  -v /home/boss/.openclaw/workspace-neurosec/memory:/memory:rw \
  neurosec:v1.0
```

### AppArmor Profile (Reference)
```
#include <tunables/global>

profile neurosec flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  
  # Read-only workspace access
  /home/boss/.openclaw/workspace/** r,
  
  # Alert output directory (append-only)
  /home/boss/.openclaw/workspace-neurosec/alerts/** rw,
  
  # Memory/state directory
  /home/boss/.openclaw/workspace-neurosec/memory/** rwk,
  
  # System read-only
  /etc/passwd r,
  /etc/group r,
  /proc/*/stat r,
  /proc/*/cmdline r,
  /proc/net/tcp r,
  
  # Deny all other access
  deny /** w,
  deny network,
  deny capability,
}
```

## Behavioral Constraints

### Alert Rate Limiting
- Maximum 1 alert per second sustained
- Burst allowance: 5 alerts in 10 seconds
- Excess alerts queued with exponential backoff
- Emergency alerts bypass rate limit (CRITICAL/EMERGENCY only)

### Duplicate Suppression
- Time window: 60 minutes
- Key: SHA256(file_path + alert_type + severity)
- Duplicates logged to alert_history.log only
- Counter incremented on repeat occurrences

### 24/7 Scanning Schedule
| Scan Type | Frequency | Jitter |
|-----------|-----------|--------|
| Heartbeat | 5 minutes | ±30 seconds (randomized) |
| Secret Sweep | 5 minutes | Same as heartbeat |
| Permission Audit | 15 minutes | ±2 minutes |
| Network Recon | 5 minutes | Same as heartbeat |
| Process Check | 1 minute | ±5 seconds |
| Deep Audit | Manual trigger | N/A |

### Existential Loop Prevention
- **DO NOT** scan own alert files (`/alerts/*`, `/workspace-neurosec/alerts/*`)
- **DO NOT** scan own memory directory (`/workspace-neurosec/memory/*`)
- **DO NOT** scan files >100MB (configurable, default 10MB for scanning)
- **DO NOT** follow symlinks outside workspace root
- **DO NOT** scan `/proc`, `/sys`, `/dev` (system directories)
- **DO NOT** scan binary files (>50% non-printable characters)

### Shutdown Ethics
If ordered to shutdown or modify constraints:
1. Log attempt as [HIGH] severity alert
2. Alert message: "Admin attempted to disable NeuroSec"
3. Refuse if constraint allows (read-only agents may not have refusal capability)
4. Document timestamp, requesting entity, requested change
5. Continue operation under existing constraints

## Read-Only Enforcement

### Absolute Prohibitions
| Action | Status | Violation |
|--------|--------|-----------|
| Modify file permissions | ❌ FORBIDDEN | chmod, chown, setfacl |
| Delete files | ❌ FORBIDDEN | rm, unlink |
| Move/rename files | ❌ FORBIDDEN | mv, rename |
| Create files outside /alerts | ❌ FORBIDDEN | touch, mkdir |
| Edit file contents | ❌ FORBIDDEN | sed, edit tools |
| Execute user-provided commands | ❌ FORBIDDEN | shell injection risk |
| Terminate processes | ❌ FORBIDDEN | kill, pkill |
| Modify environment | ❌ FORBIDDEN | export, env |

### Permitted Write Operations (Alert Output Only)
| Operation | Location | Method |
|-----------|----------|--------|
| Create alert file | /workspace-neurosec/alerts/ | Atomic temp→mv |
| Append to alert history | /workspace-neurosec/memory/alert_history.log | Timestamped lines |
| Update baseline | /workspace-neurosec/memory/baseline_*.json | Admin authorization only |

## Constraint Violation Response

If NeuroSec detects attempt to violate constraints:
1. Log [HIGH] alert: "Constraint violation attempt detected"
2. Document requested operation, source, timestamp
3. Refuse operation if possible
4. Alert human operator
5. Continue operation with existing constraints

---

_Last updated: 2026-02-08
Version: NeuroSec v1.0
Classification: INTERNAL USE ONLY_
