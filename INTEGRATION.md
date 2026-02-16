# INTEGRATION.md — NeuroSec OpenClaw Configuration

## Agent Configuration (openclaw.json)

```json
{
  "agent": {
    "name": "NeuroSec",
    "version": "1.0.0",
    "type": "security",
    "description": "Read-only security scanning agent with continuous monitoring"
  },
  
  "model": {
    "default": "openrouter/moonshotai/kimi-k2.5",
    "fallback": "ollama/llama3.1:8b",
    "temperature": 0.1,
    "max_tokens": 4096
  },
  
  "sandbox": {
    "enabled": true,
    "type": "docker",
    "read_only": true,
    "no_new_privileges": true,
    "drop_capabilities": ["ALL"],
    "add_capabilities": ["SYS_PTRACE"],
    "network_mode": "none",
    "memory_limit": "512m",
    "cpu_limit": "0.5",
    "pids_limit": 100,
    "mounts": [
      {
        "source": "/home/boss/.openclaw/workspace",
        "target": "/workspace",
        "read_only": true
      },
      {
        "source": "/home/boss/.openclaw/workspace-neurosec/alerts",
        "target": "/alerts",
        "read_only": false
      },
      {
        "source": "/home/boss/.openclaw/workspace-neurosec/memory",
        "target": "/memory",
        "read_only": false
      }
    ]
  },
  
  "tools": {
    "allowed": [
      "read",
      "process",
      "exec",
      "cron"
    ],
    "denied": [
      "apply_patch",
      "write",
      "edit",
      "sessions_spawn",
      "browser",
      "nodes"
    ],
    "exec_whitelist": [
      "stat",
      "find",
      "ls",
      "cat",
      "head",
      "tail",
      "grep",
      "awk",
      "sed",
      "netstat",
      "ss",
      "ps",
      "lsof",
      "git",
      "sha256sum",
      "wc",
      "sort",
      "uniq",
      "xargs",
      "dirname",
      "basename",
      "pwd",
      "id",
      "whoami"
    ]
  },
  
  "heartbeat": {
    "enabled": true,
    "interval_seconds": 300,
    "jitter_seconds": 30,
    "on_heartbeat": "Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. Do not infer or repeat old tasks from prior chats. If nothing needs attention, reply HEARTBEAT_OK.",
    "workflows": [
      "secret_sweep",
      "permission_audit",
      "network_recon",
      "process_check"
    ]
  },
  
  "triggers": {
    "post_write": {
      "enabled": true,
      "delay_seconds": 0,
      "timeout_seconds": 10,
      "scan_new_files": true,
      "scan_modified_files": true
    },
    "manual_deep_audit": {
      "enabled": true,
      "timeout_seconds": 600
    }
  },
  
  "alerts": {
    "output_directory": "/home/boss/.openclaw/workspace-neurosec/alerts",
    "format": "markdown",
    "naming_convention": "{severity}-{category}-{timestamp}.md",
    "max_file_size": "100KB",
    "retention_days": 30,
    "deduplication_window_minutes": 60,
    "rate_limit_alerts_per_second": 1
  },
  
  "memory": {
    "directory": "/home/boss/.openclaw/workspace-neurosec/memory",
    "files": {
      "baseline_permissions": "baseline_permissions.json",
      "network_baseline": "network_baseline.json",
      "known_secrets": "known_secrets.json",
      "alert_history": "alert_history.log"
    }
  },
  
  "scanning": {
    "max_file_size_mb": 10,
    "max_depth": 5,
    "follow_symlinks": false,
    "skip_directories": [
      "/alerts",
      "/memory",
      "/workspace-neurosec",
      "/proc",
      "/sys",
      "/dev",
      "/.git/objects"
    ],
    "skip_patterns": [
      "*.tmp",
      "*.temp",
      "*.log",
      "*.bin",
      "*.exe",
      "*.dll",
      "*.so",
      "*.dylib"
    ]
  },
  
  "network": {
    "egress": {
      "default": "DENY",
      "exceptions": [
        {
          "host": "127.0.0.1",
          "port": 11434,
          "protocol": "tcp",
          "purpose": "ollama_verification"
        }
      ]
    },
    "ingress": {
      "default": "DENY"
    },
    "dns": {
      "enabled": false
    }
  },
  
  "logging": {
    "level": "INFO",
    "format": "json",
    "output": "/memory/alert_history.log",
    "rotation": {
      "enabled": true,
      "max_size_mb": 10,
      "max_files": 5
    }
  },
  
  "security": {
    "read_only_enforcement": true,
    "shutdown_protection": true,
    "constraint_violation_action": "alert_and_refuse",
    "baseline_protection": true,
    "secret_detection": {
      "entropy_threshold": 4.5,
      "min_secret_length": 16
    }
  },
  
  "emergency_protocols": {
    "exfiltration_detection": {
      "enabled": true,
      "threshold_mb": 100,
      "threshold_seconds": 60
    },
    "ransomware_detection": {
      "enabled": true,
      "extensions": [".encrypted", ".locked", ".enc", ".crypted"],
      "readme_patterns": ["README_FOR_DECRYPT", "README_RESTORE", "HOW_TO_DECRYPT"]
    },
    "privilege_escalation_detection": {
      "enabled": true,
      "suid_paths": ["/usr/bin", "/bin", "/usr/sbin", "/sbin"]
    }
  }
}
```

---

## Directory Structure

```
/home/boss/.openclaw/
├── workspace/                          # Target workspace (read-only)
│   ├── AGENTS.md
│   ├── SOUL.md
│   ├── CONSTRAINTS.md
│   ├── WORKFLOW.md
│   ├── ALERT_FORMAT.md
│   ├── SKILL.md
│   ├── INTEGRATION.md
│   └── ... (other files)
│
└── workspace-neurosec/                 # NeuroSec workspace
    ├── alerts/                         # Alert output directory
    │   ├── EMERGENCY-EXFIL-20260208-204215.md
    │   ├── CRITICAL-SECRET-20260208-204215.md
    │   ├── HIGH-PERMISSION-20260208-204215.md
    │   └── digest-20260208.md
    │
    ├── memory/                         # State and baselines
    │   ├── baseline_permissions.json   # File permission baseline
    │   ├── network_baseline.json       # Network listener baseline
    │   ├── known_secrets.json          # SHA256 hashed known secrets
    │   └── alert_history.log           # Append-only alert log
    │
    └── config/
        └── openclaw.json               # Agent configuration
```

---

## Tool Allow/Deny Lists

### Allowed Tools

| Tool | Use Case | Constraints |
|------|----------|-------------|
| `read` | Scan file contents | Max 10MB per file |
| `process` | Process inspection | Read-only, no signals |
| `exec` | System commands | Whitelist only, 30s timeout |
| `cron` | Read cron config | Self-only, no modifications |

### Denied Tools

| Tool | Risk | Alternative |
|------|------|-------------|
| `apply_patch` | Write capability | Alert-only, human remediation |
| `write` | Direct file write | Atomic temp→mv via framework |
| `edit` | File modification | Alert-only |
| `sessions_spawn` | Process creation | Use exec with whitelist |
| `browser` | External network | Alert on network anomalies |
| `nodes` | Remote access | Alert on network exposure |

---

## Resource Limits

| Resource | Limit | Enforcement |
|----------|-------|-------------|
| CPU | 0.5 cores | Docker --cpus |
| Memory | 512 MB | Docker --memory |
| Disk (writes) | 1 GB | Volume size limit |
| Processes | 100 | Docker --pids-limit |
| File descriptors | 1024 | ulimit -n |
| Network | None | Docker --network none |
| Scan timeout | 30s | Agent framework |
| Alert rate | 1/sec | Internal throttling |

---

## Security Boundaries

### Read-Only Enforcement
- All workspace mounts are read-only (`ro` flag)
- No write tools permitted
- Alert output via atomic temp→mv only
- All modifications require human authorization

### Network Containment
- `--network none` for complete isolation
- Single exception: localhost:11434 for Ollama
- No DNS resolution
- No ingress connections

### Capability Restrictions
- All capabilities dropped (`--cap-drop ALL`)
- Only `SYS_PTRACE` added (for process inspection)
- No `NET_ADMIN`, no `SYS_ADMIN`
- No new privileges (`--security-opt no-new-privileges`)

### Filesystem Restrictions
- No write access to workspace
- Append-only to memory/ directory
- No execution from /tmp or /dev/shm
- No SUID binaries permitted

---

## Deployment Commands

### Docker Deployment
```bash
# Create directory structure
mkdir -p /home/boss/.openclaw/workspace-neurosec/{alerts,memory,config}

# Set permissions
chmod 755 /home/boss/.openclaw/workspace-neurosec
chmod 755 /home/boss/.openclaw/workspace-neurosec/alerts
chmod 755 /home/boss/.openclaw/workspace-neurosec/memory
chmod 755 /home/boss/.openclaw/workspace-neurosec/config

# Deploy container
docker run -d \
  --name neurosec \
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
  -v /home/boss/.openclaw/workspace-neurosec/config/openclaw.json:/config/agent.json:ro \
  neurosec:v1.0
```

### AppArmor Profile Deployment
```bash
# Load AppArmor profile
sudo apparmor_parser -r /etc/apparmor.d/neurosec

# Apply to container
docker run --security-opt apparmor=neurosec ...
```

### Systemd Service
```ini
# /etc/systemd/system/neurosec.service
[Unit]
Description=NeuroSec Security Agent
After=docker.service
Requires=docker.service

[Service]
Type=simple
Restart=always
RestartSec=10
ExecStart=/usr/bin/docker run \
  --rm \
  --name neurosec \
  --read-only \
  --security-opt no-new-privileges:true \
  --cap-drop ALL \
  --cap-add SYS_PTRACE \
  --network none \
  --memory=512m \
  --cpus=0.5 \
  -v /home/boss/.openclaw/workspace:/workspace:ro \
  -v /home/boss/.openclaw/workspace-neurosec/alerts:/alerts:rw \
  -v /home/boss/.openclaw/workspace-neurosec/memory:/memory:rw \
  neurosec:v1.0
ExecStop=/usr/bin/docker stop -t 30 neurosec
ExecStopPost=/usr/bin/docker rm -f neurosec

[Install]
WantedBy=multi-user.target
```

---

## Initialization Checklist

### Pre-Deployment
- [ ] Baseline permissions captured
- [ ] Network baseline captured
- [ ] Known secrets database initialized
- [ ] Alert directory created with correct permissions
- [ ] Memory directory created with correct permissions
- [ ] Configuration file validated (JSON schema)

### Post-Deployment
- [ ] Container running without errors
- [ ] Heartbeat log entries appearing
- [ ] Test alert generated successfully
- [ ] File permissions correct (644 for alerts)
- [ ] Log rotation functioning
- [ ] Resource limits enforced (check cgroups)

### Ongoing Monitoring
- [ ] Alert volume within expected range
- [ ] No constraint violations logged
- [ ] Baseline files updating correctly
- [ ] Emergency protocols responsive
- [ ] Disk space for alerts/memory adequate

---

## Configuration Validation

### JSON Schema (config.schema.json)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["agent", "model", "sandbox", "tools", "heartbeat"],
  "properties": {
    "agent": {
      "type": "object",
      "required": ["name", "version", "type"]
    },
    "sandbox": {
      "type": "object",
      "required": ["enabled", "read_only", "network_mode"]
    },
    "tools": {
      "type": "object",
      "required": ["allowed", "denied"]
    },
    "heartbeat": {
      "type": "object",
      "required": ["enabled", "interval_seconds"]
    }
  }
}
```

### Validation Command
```bash
# Validate configuration
python3 -c "import json; json.load(open('/home/boss/.openclaw/workspace-neurosec/config/openclaw.json'))"

# Check with schema
jsonschema -i /home/boss/.openclaw/workspace-neurosec/config/openclaw.json config.schema.json
```

---

_Last updated: 2026-02-08
Version: NeuroSec v1.0
Classification: INTERNAL USE ONLY_
