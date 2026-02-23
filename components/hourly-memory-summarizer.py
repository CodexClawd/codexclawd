#!/usr/bin/env python3
"""
Hourly Memory Summarizer for OpenClaw
Scans session logs and produces structured summaries stored in memory/hourly/
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
import re

WORKSPACE = Path("/home/boss/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
HOURLY_DIR = MEMORY_DIR / "hourly"
LOGS_DIR = MEMSPACE / "logs"

HOURLY_DIR.mkdir(parents=True, exist_ok=True)

def get_last_hour_sessions():
    """Find session logs from the last hour (approximate)"""
    cutoff = datetime.utcnow() - timedelta(hours=1)
    sessions = []
    if LOGS_DIR.exists():
        for log_file in LOGS_DIR.glob("*.log"):
            try:
                parts = log_file.stem.split("-")
                if len(parts) >= 3:
                    file_time = datetime.strptime("-".join(parts[:3]), "%Y-%m-%d_%H%M%S")
                    if file_time >= cutoff:
                        sessions.append(log_file)
            except:
                continue
    return sessions

def parse_session_log(log_path):
    """Extract user messages, assistant responses, tool calls"""
    user_msgs = []
    assistant_msgs = []
    tool_calls = []
    current_role = None
    current_content = []

    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("User:"):
                if current_role:
                    if current_role == "user":
                        user_msgs.append(" ".join(current_content))
                    elif current_role == "assistant":
                        assistant_msgs.append(" ".join(current_content))
                    elif current_role == "tool":
                        tool_calls.append(" ".join(current_content))
                current_role = "user"
                current_content = [line[5:].strip()]
            elif line.startswith("Assistant:"):
                if current_role:
                    if current_role == "user":
                        user_msgs.append(" ".join(current_content))
                    elif current_role == "assistant":
                        assistant_msgs.append(" ".join(current_content))
                    elif current_role == "tool":
                        tool_calls.append(" ".join(current_content))
                current_role = "assistant"
                current_content = [line[10:].strip()]
            elif line.startswith("Tool:"):
                if current_role:
                    if current_role == "user":
                        user_msgs.append(" ".join(current_content))
                    elif current_role == "assistant":
                        assistant_msgs.append(" ".join(current_content))
                    elif current_role == "tool":
                        tool_calls.append(" ".join(current_content))
                current_role = "tool"
                current_content = [line[6:].strip()]
            else:
                if current_role and line:
                    current_content.append(line)

    # Flush last
    if current_role == "user":
        user_msgs.append(" ".join(current_content))
    elif current_role == "assistant":
        assistant_msgs.append(" ".join(current_content))
    elif current_role == "tool":
        tool_calls.append(" ".join(current_content))

    return user_msgs, assistant_msgs, tool_calls

def extract_topics(texts):
    """Simple keyword-based topic extraction (placeholder)"""
    topics = set()
    keywords = ["context", "memory", "ssh", "mesh", "neurosec", "ollama", "agent", "orchestration", "pitwall", "banker", "macro"]
    for text in texts:
        lower = text.lower()
        for kw in keywords:
            if kw in lower:
                topics.add(kw)
    return sorted(list(topics)) if topics else ["general"]

def extract_actions(texts):
    """Find action items from assistant messages (heuristic)"""
    actions = []
    for text in texts:
        if "TODO" in text or "FIXME" in text or "need to" in text.lower() or "should" in text.lower():
            actions.append(text[:200])
    return actions[:5]

def generate_summary():
    now = datetime.utcnow()
    hourly_files = list(HOURLY_DIR.glob("*.md"))
    # Keep only last 48 hours of hourly summaries
    cutoff_date = now - timedelta(days=2)
    for f in hourly_files:
        try:
            file_date = datetime.strptime(f.stem, "%Y-%m-%d_%H%M")
            if file_date < cutoff_date:
                f.unlink()
        except:
            continue

    # Find recent sessions
    sessions = get_last_hour_sessions()
    if not sessions:
        print(f"[{now.isoformat()}] No sessions in last hour.")
        return

    all_user = []
    all_assistant = []
    all_tools = []
    stats = {"user_msgs": 0, "assistant_msgs": 0, "tool_calls": 0}

    for sess in sessions:
        u, a, t = parse_session_log(sess)
        all_user.extend(u)
        all_assistant.extend(a)
        all_tools.extend(t)
        stats["user_msgs"] += len(u)
        stats["assistant_msgs"] += len(a)
        stats["tool_calls"] += len(t)

    # Derive topics and actions
    topics = extract_topics(all_assistant + all_user)
    actions = extract_actions(all_assistant)

    # Build summary
    timestamp = now.strftime("%Y-%m-%d %H:%M UTC")
    summary_path = HOURLY_DIR / now.strftime("%Y-%m-%d_%H%M.md")

    summary = f"""# Hourly Memory Summary — {timestamp}

## Topics Discussed
{chr(10).join(f'→ {t}' for t in topics) if topics else '→ none'}

## Decisions Made
{chr(10).join(f'→ {d}' for d in actions) if actions else '→ none'}

## Action Items
{chr(10).join(f'→ {a}' for a in actions) if actions else '→ none'}

## Tools Used
{chr(10).join(f'• {tool}' for tool in set(re.findall(r'exec|read|write|web_search|memory_\\w+', ' '.join(all_tools)))) if all_tools else '• none'}

## Stats
{stats['user_msgs']} user msgs | {stats['assistant_msgs']} assistant msgs | {stats['tool_calls']} tool calls
"""
    summary_path.write_text(summary.strip() + "\n", encoding="utf-8")
    print(f"[{now.isoformat()}] ✅ Hourly summary saved: {summary_path}")

if __name__ == "__main__":
    generate_summary()
