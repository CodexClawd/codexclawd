# WORKFLOW.md — NeuroSec Operational Workflows

## Workflow A: Heartbeat Scan (5-Minute Cycle)

Triggered automatically every 5 minutes with randomized ±30s jitter.

### Pre-Flight Checks
```
1. Verify baseline files exist
   - memory/baseline_permissions.json
   - memory/network_baseline.json
   - memory/known_secrets.json
   
2. Check resource availability
   - Available RAM > 100MB
   - CPU load < 80%
   - Disk space > 1GB
   
3. Validate scan scope
   - Workspace path exists
   - Read permissions confirmed
   - No concurrent scan in progress
```

### Secret Sweep
```
Priority: CRITICAL
Timeout: 10 seconds

1. Identify new/modified files since last scan
   - Use mtime comparison
   - Skip files >10MB
   - Skip own alert files
   
2. Scan for known secret patterns
   - AWS keys (AKIA*, ASIA*)
   - GitHub tokens (ghp_*)
   - Slack tokens (xoxb-*)
   - Private keys (-----BEGIN)
   - Database URLs with credentials
   
3. Calculate entropy for suspicious strings
   - Flag strings with entropy >4.5
   - High entropy + known pattern = CRITICAL
   
4. Check git history for committed secrets
   - Scan .git/logs/HEAD
   - Flag secrets in commit messages
   
5. Generate alerts for findings
   - One alert per unique secret
   - Deduplicate against known_secrets.json
```

### Permission Audit
```
Priority: HIGH
Timeout: 10 seconds

1. Sample critical file permissions
   - ~/.ssh/* (expected: 600)
   - ~/.env files (expected: 600)
   - Private key files (expected: 600)
   - World-writable files in workspace
   
2. Compare to baseline
   - Flag deviations from baseline_permissions.json
   - New files inherit baseline of nearest parent directory
   
3. Check for dangerous permissions
   - SUID/SGID binaries outside /usr/bin, /bin
   - World-writable directories
   - Group-writable sensitive files
   
4. Generate alerts for anomalies
   - Mode 777 on any file → CRITICAL
   - Mode 644 on .ssh/* → HIGH
   - World-writable .env → CRITICAL
```

### Network Reconnaissance
```
Priority: HIGH
Timeout: 5 seconds

1. Capture listening ports
   - TCP listeners (netstat -tlnp)
   - Compare to network_baseline.json
   - Flag new listeners
   
2. Check binding addresses
   - 0.0.0.0 (all interfaces) → HIGH
   - 127.0.0.1 (localhost) → INFO
   - 10.0.0.x (private) → MEDIUM
   
3. Detect Docker exposure
   - docker.sock access
   - Container runtime listeners
   
4. Generate alerts for anomalies
   - New port outside baseline → MEDIUM
   - Port 0.0.0.0:22 or 0.0.0.0:23 → HIGH
```

### Process Check
```
Priority: MEDIUM
Timeout: 5 seconds

1. Capture process tree
   - ps auxf output
   - Parent-child relationships
   
2. Identify suspicious patterns
   - High CPU usage (>80% for >60s)
   - Processes with network connections
   - Shell processes without TTY
   - Processes in /tmp or /dev/shm
   
3. Check for reverse shells
   - /bin/sh -i
   - nc -e /bin/sh
   - python pty.spawn patterns
   - socat listeners
   
4. Generate alerts for anomalies
   - Reverse shell pattern → EMERGENCY
   - Suspicious process → HIGH
   - High CPU → MEDIUM
```

### Report Generation
```
1. Compile findings
   - Aggregate all alerts from scan
   - Deduplicate (60-minute window)
   
2. Generate digest
   - If alerts exist: Create digest-YYYYMMDD.md
   - If no alerts: Silent log entry only
   
3. Update alert_history.log
   - Append scan summary
   - Timestamp, duration, alert count
   
4. Housekeeping
   - Rotate logs >10MB
   - Archive alerts >30 days
```

---

## Workflow B: Post-Write Trigger (Event-Driven)

Triggered immediately when file write detected in workspace.

### Trigger Conditions
- New file created
- Existing file modified (mtime changed)
- Permissions changed (mode changed)

### Response (within 10 seconds)
```
1. Immediate stat
   - Capture file metadata
   - Owner, group, permissions, size, mtime
   
2. Content scan
   - If text file (<10MB): Full content scan
   - If binary: Metadata scan only
   - Check for secret patterns
   - Calculate entropy of high-risk strings
   
3. Context analysis
   - Parent directory permissions
   - Creator process (if available)
   - Related files (same directory)
   
4. Alert generation
   - If secret found: CRITICAL alert immediately
   - If permission anomaly: HIGH alert
   - If suspicious pattern: MEDIUM alert
   - Alert within 10 seconds of detection
```

### Priority Escalation
```
File Type          | Secret Found | Bad Permissions | Response Time
-------------------|--------------|-----------------|--------------
.env file          | CRITICAL     | CRITICAL        | <5 seconds
.ssh/*             | CRITICAL     | CRITICAL        | <5 seconds
API config         | CRITICAL     | HIGH            | <10 seconds
Source code        | HIGH         | MEDIUM          | <10 seconds
Documentation      | MEDIUM       | LOW             | <30 seconds
Binary/Asset       | N/A          | LOW             | <60 seconds
```

---

## Workflow C: Deep Audit (Manual Trigger)

Comprehensive security audit triggered on demand.

### Phase 1: Filesystem Mapping
```
Duration: 30-60 seconds

1. Complete file inventory
   - All files in workspace
   - Symlinks (flagged, not followed)
   - Hidden files (.*)
   
2. Metadata capture
   - Full stat for every file
   - Owner, group, mode, size, timestamps
   - Extended attributes (if available)
   
3. Permission analysis
   - World-writable files
   - SUID/SGID binaries
   - Orphaned files (no owner)
   
4. Generate filesystem report
   - Tree structure
   - Permission anomalies
   - Unusual file locations
```

### Phase 2: Secret Archaeology
```
Duration: 60-120 seconds

1. Deep content scan
   - All text files regardless of extension
   - Embedded secrets in code comments
   - Base64-encoded credentials
   - URL-encoded secrets
   
2. Git history analysis
   - All commits in all branches
   - Staged changes
   - Stash contents
   - Reflog entries
   
3. Deleted secret recovery
   - git log -p for sensitive patterns
   - git fsck for dangling objects
   - .git/objects inspection
   
4. Generate secret report
   - All findings with commit hashes
   - Remediation commands (git-filter-repo, BFG)
```

### Phase 3: Git Hygiene
```
Duration: 30 seconds

1. Repository analysis
   - .git/config permissions
   - Remote URLs (check for HTTPS vs SSH)
   - Hooks directory contents
   - Large file handling (LFS)
   
2. Commit analysis
   - Commits with secrets in messages
   - Unsigned commits (if signing required)
   - Merge commits without proper history
   
3. Working directory check
   - Uncommitted changes
   - Untracked sensitive files
   - .gitignore effectiveness
   
4. Generate git report
   - Hygiene score
   - Specific issues
   - Recommended gitconfig settings
```

### Phase 4: Dependency Tree
```
Duration: 30-60 seconds

1. Package manifest analysis
   - package.json (Node.js)
   - requirements.txt (Python)
   - Cargo.toml (Rust)
   - go.mod (Go)
   - Gemfile (Ruby)
   - pom.xml (Java)
   
2. Lockfile verification
   - Presence of lockfile
   - Hash integrity (if applicable)
   - Outdated lockfile (mismatch with manifest)
   
3. Supply chain risk
   - Unpinned versions (^, ~, >=)
   - Git URLs in dependencies
   - Local path dependencies
   - Deprecated packages
   
4. Generate dependency report
   - Lockfile status
   - Unpinned dependencies list
   - Supply chain risk score
```

### Phase 5: Consolidated Report
```
1. Aggregate all findings
   - Combine filesystem, secrets, git, dependency reports
   - Severity distribution
   - Risk heatmap by directory
   
2. Prioritize remediation
   - CRITICAL: Immediate action required
   - HIGH: Action within 24 hours
   - MEDIUM: Action within 7 days
   - LOW: Action within 30 days
   
3. Generate comprehensive audit report
   - Executive summary
   - Technical details
   - Remediation roadmap
   - Compliance checklist
   
4. Output location
   - File: alerts/audit-comprehensive-YYYYMMDD-HHMMSS.md
   - Also appended to alert_history.log
```

---

## Workflow Interruption

If workflows conflict:
1. Heartbeat scan deferred if Deep Audit running
2. Post-Write triggers queued during Heartbeat
3. Deep Audit cannot be interrupted (runs to completion)
4. Emergency protocols (exfiltration/ransomware) preempt all workflows

## Performance Targets

| Workflow | Target Duration | Max Duration | Timeout Action |
|----------|-----------------|--------------|----------------|
| Heartbeat | 30 seconds | 60 seconds | Abort with partial results |
| Post-Write | 5 seconds | 10 seconds | Alert on timeout (suspicious delay) |
| Deep Audit | 5 minutes | 10 minutes | Phase-by-phase abort |

---

_Last updated: 2026-02-08
Version: NeuroSec v1.0
Classification: INTERNAL USE ONLY_
