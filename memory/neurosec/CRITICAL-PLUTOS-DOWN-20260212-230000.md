# [CRITICAL] Plutos Node Offline

**Timestamp:** 2026-02-12 23:00:00 UTC  
**Severity:** CRITICAL  
**Node:** Plutos (10.0.0.4)  
**Check:** sentinel-mesh-check

## Finding
Plutos (32GB inference node) is completely unreachable via mesh network.

## Evidence
- ICMP ping: 100% packet loss (2 transmitted, 0 received)
- Ollama API: Connection timeout
- Last successful check: Unknown

## Impact
**IMMEDIATE CAPACITY LOSS**
- Loss of 32GB RAM inference capacity (50% of total mesh compute)
- Remaining capacity: 16GB (clawd) + 8GB (brutus) = 24GB
- Large model inference (>14B) may fail or be unavailable

## Possible Causes
1. VPS shutdown/reboot (provider maintenance?)
2. WireGuard tunnel failure
3. Network partition
4. Host-level crash

## Recommendation
**IMMEDIATE:** SSH to Plutos public IP and check:
```bash
ssh boss@87.106.3.190
systemctl status wg-quick@wg0
systemctl status ollama
```

**IF HOST REACHABLE:** Restart WireGuard, verify Ollama
**IF HOST UNREACHABLE:** Check VPS provider dashboard (IONOS)

## Network Status
| Node | Ping | Ollama |
|------|------|--------|
| Nexus | ✓ | — |
| Clawd | ✓ | ✗ |
| Brutus | ✓ | ✓ |
| Plutos | ✗ | ✗ |

**CERTAINTY: HIGH** — Complete connectivity failure
