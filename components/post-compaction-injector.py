#!/usr/bin/env python3
"""
Post-Compaction Context Injector
Detects session compaction and injects recent memory to maintain continuity.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path("/home/boss/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
HOURLY_DIR = MEMORY_DIR / "hourly"
VECTOR_DIR = MEMORY_DIR / "vector"
COMPACTION_FILE = MEMORY_DIR / ".compaction_state"

def read_compaction_state():
    if COMPACTION_FILE.exists():
        try:
            data = json.loads(COMPACTION_FILE.read_text())
            return data.get("compaction_count", 0), data.get("last_compaction_ts")
        except:
            pass
    return 0, None

def write_compaction_state(count, ts=None):
    if ts is None:
        ts = datetime.utcnow().isoformat()
    COMPACTION_FILE.write_text(json.dumps({
        "compaction_count": count,
        "last_compaction_ts": ts
    }))

def get_last_hourly_summaries(hours=24):
    """Get the most recent hourly summaries within the last N hours"""
    summaries = []
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    if not HOURLY_DIR.exists():
        return summaries
    for f in sorted(HOURLY_DIR.glob("*.md")):
        try:
            dt = datetime.strptime(f.stem, "%Y-%m-%d_%H%M")
            if dt >= cutoff:
                summaries.append(f.read_text(encoding="utf-8"))
        except:
            continue
    return summaries[-6:]  # up to 6 recent hourly summaries

def get_recent_messages_from_logs(limit=30):
    """Grab the most recent user/assistant messages from the logs directory"""
    logs = WORKSPACE / "logs"
    if not logs.exists():
        return []
    entries = []
    for log_file in logs.glob("*.log"):
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            # Split into message blocks
            blocks = content.split("User:")[1:]  # skip first empty
            for block in blocks:
                parts = block.split("Assistant:", 1)
                user_msg = parts[0].strip() if len(parts) > 0 else ""
                assistant_msg = parts[1].split("Tool:")[0].strip() if len(parts) > 1 else ""
                if user_msg:
                    entries.append(("user", user_msg))
                if assistant_msg:
                    entries.append(("assistant", assistant_msg))
        except:
            continue
    # Return most recent entries
    return [(role, msg) for role, msg in entries[-limit:]]

def build_injection_context(compaction_count, last_ts):
    """Assemble the context package to inject"""
    context_parts = []

    context_parts.append("## System Note: Session Continuity Restoration")
    context_parts.append(f"You are rejoining after a compaction event (#{compaction_count}). Context below restores recent history.\n")

    summaries = get_last_hourly_summaries(hours=24)
    if summaries:
        context_parts.append("### Recent Hourly Summaries (last 6)")
        for s in summaries:
            # Take just the first few lines of each summary
            lines = s.splitlines()[:15]
            context_parts.append("\n".join(lines))
            context_parts.append("---")
        context_parts.append("")

    recent_msgs = get_recent_messages_from_logs(limit=30)
    if recent_msgs:
        context_parts.append("### Recent Messages")
        for role, msg in recent_msgs:
            preview = (msg[:200] + "…") if len(msg) > 200 else msg
            context_parts.append(f"{role.upper()}: {preview}")
        context_parts.append("")

    return "\n".join(context_parts).strip()

def detect_and_inject():
    """Main entry: detect compaction and print injection context for the agent"""
    comp_count, last_ts = read_compaction_state()

    # For demo: always treat as new compaction (in real use, compare current context size to stored)
    # Here we just increment and provide context
    new_count = comp_count + 1
    write_compaction_state(new_count, datetime.utcnow().isoformat())

    ctx = build_injection_context(new_count, last_ts)
    if ctx:
        print(ctx)
    else:
        print("## System: No recent memory to restore.")

if __name__ == "__main__":
    detect_and_inject()
