[CRITICAL-SERVICE-2026-02-19T15-00-00Z.md]
---
SEVERITY: CRITICAL
CATEGORY: Service Outage
IMPACT: Ollama inference API on Brutus (10.0.0.3) is completely unresponsive. Node cannot serve model inference requests.
EVIDENCE: curl test: HTTP Status: 000, Total Time: 2.002272s (timeout)
LOCATION: 10.0.0.3 (Brutus), port 11434
RECOMMENDATION: Immediate restart of Ollama service on Brutus, check disk/memory pressure, and verify process health. If restart fails, isolate node for deeper diagnostics.
CERTAINTY: High (direct connection failure)
TIMESTAMP: 2026-02-19T15:00:00Z
---
