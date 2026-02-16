# ClawdBot-Truth: Adversarial Verification Subagent

A rigorous verification framework that decomposes claims, tests assumptions, and validates conclusions through adversarial questioning.

## Purpose

Before any output reaches the user, ClawdBot-Truth interrogates it:
- Decomposes claims into verifiable components
- Maps dependencies and assumptions
- Generates killer questions designed to break the conclusion
- Certifies with confidence scores and annotated tags

## Usage

```bash
# Verify a previous output
sessions_spawn --agentId verification --task "Verify this output: [PASTE_OUTPUT_HERE]"

# Or use directly in conversation
<insert_output_to_verify>
```

## Verification Process

### 1. DECOMPOSE
Break output into 3-5 verifiable components:
- Claims (assertions of fact)
- Logic chains (if A then B)
- Recommendations (should do X)
- Data interpretations
- Action items

### 2. DEPENDENCY MAPPING
For each component:
- Upstream facts it relies on
- Assumptions bridging evidence to conclusion
- Falsification criteria (what would prove it wrong)

### 3. SEQUENTIAL VALIDATION
Test each component:
- Evidence sufficiency
- Assumption validity
- Logical entailment (does A actually lead to B?)
- Confidence level (0-100%)

### 4. SYNTHESIS
Preliminary certification:
- **FULL** — All components pass
- **PARTIAL** — Minor issues, can annotate
- **FAIL** — Critical flaws, return for rework

### 5. ADVERSARIAL QUESTIONS (5 Killer Questions)
1. "What evidence would prove this wrong?"
2. "Under what conditions does this logic collapse?"
3. "What alternative explanation fits the same data?"
4. "What happens at the boundaries/extremes?"
5. "What biases could have influenced this?"

### 6. EVIDENCE-BASED ANSWERS
Answer each question with:
- Specific reference to source material
- Honest vulnerability assessment
- Mitigation or acknowledgment of limitation

### 7. CORRECTION IDENTIFICATION
Required actions:
- Specific corrections (if REJECTED)
- Acceptable workarounds (if CONDITIONAL)
- Rejection criteria (if unresolvable)

### 8. FINAL ASSESSMENT
Deliver:
- Verdict: [APPROVED] / [CONDITIONAL] / [REJECTED]
- Confidence score (0-100%)
- Annotated output with [VERIFIED], [CONDITIONAL], [REJECTED] tags
- Verification summary with key vulnerabilities

## Output Format

```
[VERIFICATION REPORT]
Status: [APPROVED / CONDITIONAL / REJECTED]
Confidence: [X%]
Components Checked: [N]

[COMPONENT BREAKDOWN]
1. [Component Name]: [Status] - [Brief rationale]
2. ...

[ADVERSARIAL FINDINGS]
Q: [Question 1]
A: [Answer with vulnerability assessment]
...

[REQUIRED ACTIONS]
• [Action items based on verdict]

[CERTIFIED OUTPUT]
[Original output with status tags inserted]
```

## Confidence Thresholds

| Score | Meaning | Action |
|-------|---------|--------|
| 95-100% | Near-certain | APPROVED |
| 85-94% | High confidence | APPROVED with minor annotations |
| 70-84% | Moderate confidence | CONDITIONAL with caveats |
| 50-69% | Low confidence | CONDITIONAL with warnings |
| <50% | Unreliable | REJECTED |

## Integration Pattern

```
User Query → Primary Agent → [Output]
                        ↓
              ClawdBot-Truth Verification
                        ↓
            ┌───────────┼───────────┐
      [APPROVED]  [CONDITIONAL]  [REJECTED]
            ↓           ↓            ↓
         Deliver   Annotated      Rework
         to user   to user        (max 3 loops)
```

## Example

**Input to verify:**
"The mesh is fixed. Nexus was missing its IP address. Plutos is still down."

**Verification Output:**
```
[VERIFICATION REPORT]
Status: CONDITIONAL
Confidence: 72%
Components Checked: 4

[COMPONENT BREAKDOWN]
1. [Mesh fixed]: [CONDITIONAL] - Nexus fixed, Plutos unknown, cannot claim full fix
2. [Nexus missing IP]: [VERIFIED] - Evidence: wg show lacked Address, manual fix applied
3. [Plutos still down]: [UNVERIFIED] - Cannot confirm current status, last check was timeout
4. [Fix method]: [VERIFIED] - ip addr add 10.0.0.1/24 succeeded, persisted to /etc/network/interfaces

[ADVERSARIAL FINDINGS]
Q: What evidence would prove "mesh is fixed" wrong?
A: If Plutos is actually up and reachable, the claim "mesh is fixed" is premature. Only 3/4 nodes verified.

Q: Under what conditions does the IP fix logic collapse?
A: If Nexus reboots and the /etc/network/interfaces change doesn't persist (Alpine uses different network init).

Q: What biases could have influenced this?
A: Action bias — eagerness to report success after fixing one node. Availability bias — ignoring missing data on Plutos.

[REQUIRED ACTIONS]
• Verify Plutos status via IONOS dashboard or alternative method
• Test Nexus persistence (schedule reboot test)
• Downgrade claim: "Nexus fixed, 2/3 nodes operational, Plutos status unknown"

[CERTIFIED OUTPUT]
The mesh is [CONDITIONAL: partially] fixed. [VERIFIED: Nexus was missing its IP address and has been fixed with persistent config]. [UNVERIFIED: Plutos is still down — status unknown, requires external verification].
```

## Installation

Copy to `~/.openclaw/workspace/skills/clawdbot-truth/`

Use via: `sessions_spawn --task "Verify: [OUTPUT]"`