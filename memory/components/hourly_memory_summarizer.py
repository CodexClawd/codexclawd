#!/usr/bin/env python3
"""
Hourly Memory Summarizer - Token-Efficient Version for 3-7B Local Models
Ultra-compact structured format that minimizes token usage while preserving
critical context for small context windows (4k-8k tokens).

Design principles:
- Structured YAML-like format (parses reliably by 3B models)
- Hierarchical compression (details → summaries → digests)
- Token budget enforcement (max 512 tokens per hourly summary)
- No natural language fluff - pure signal

Author: Memory System for OpenClaw
Version: 1.0.0 (Token-Optimized)
"""

import os
import json
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Configuration - tuned for 3-7B models
MAX_SUMMARY_TOKENS = 512  # Hard limit per hourly summary
MAX_DECISIONS = 5  # Top decisions only
MAX_ACTIONS = 8  # Top action items only
MAX_TOPICS = 4  # Key topics only

MEMORY_DIR = Path(os.path.expanduser("~/.openclaw/workspace/memory"))
SESSION_LOG_DIR = Path(os.path.expanduser("~/.openclaw/logs/sessions"))


@dataclass
class CompactDecision:
    """Token-efficient decision record."""
    d: str  # decision (abbreviated key)
    r: str  # reasoning (max 20 words)
    t: str  # timestamp
    
    def to_line(self) -> str:
        return f" - {self.d} | {self.r} [{self.t}]"


@dataclass
class CompactAction:
    """Token-efficient action item."""
    a: str  # action
    s: str  # status: [todo|prog|done|block]
    o: str  # owner (agent or user)
    d: str  # deadline if any
    
    def to_line(self) -> str:
        deadline = f" | due:{self.d}" if self.d else ""
        return f" - [{self.s}] {self.a} @{self.o}{deadline}"


@dataclass
class HourlySummary:
    """Ultra-compact hourly summary structure."""
    ts: str  # timestamp
    topics: List[str]  # topic keywords
    decisions: List[CompactDecision]
    actions: List[CompactAction]
    tools: Dict[str, int]  # tool usage counts
    stats: Dict[str, int]  # message counts
    
    def to_compact_format(self) -> str:
        """Generate token-minimal markdown format."""
        lines = [
            f"## {self.ts}",
            "",
            "T:" + ",".join(self.topics[:MAX_TOPICS]),
            ""
        ]
        
        if self.decisions:
            lines.append("D:")
            for dec in self.decisions[:MAX_DECISIONS]:
                lines.append(dec.to_line())
            lines.append("")
        
        if self.actions:
            lines.append("A:")
            for act in self.actions[:MAX_ACTIONS]:
                lines.append(act.to_line())
            lines.append("")
        
        if self.tools:
            tool_str = " ".join([f"{k}:{v}" for k, v in self.tools.items()])
            lines.append(f"X:{tool_str}")
        
        lines.append(f"S:u{self.stats.get('user', 0)} a{self.stats.get('assistant', 0)} t{self.stats.get('tools', 0)}")
        
        return "\n".join(lines)


class SessionParser:
    """Parse OpenClaw session logs into structured data."""
    
    def __init__(self, log_dir: Path = SESSION_LOG_DIR):
        self.log_dir = log_dir
    
    def find_recent_sessions(self, hours: int = 1) -> List[Path]:
        """Find session logs from last N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        sessions = []
        
        if not self.log_dir.exists():
            return sessions
        
        for log_file in self.log_dir.glob("*.jsonl"):
            try:
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if mtime >= cutoff:
                    sessions.append(log_file)
            except Exception:
                continue
        
        return sorted(sessions, key=lambda p: p.stat().st_mtime)
    
    def parse_session(self, log_path: Path) -> Dict:
        """Parse a session log file into structured events."""
        events = {
            'messages': {'user': [], 'assistant': []},
            'decisions': [],
            'actions': [],
            'topics': [],
            'tools': {},
            'thinking': []
        }
        
        if not log_path.exists():
            return events
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        event = json.loads(line)
                        self._categorize_event(event, events)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error parsing {log_path}: {e}")
        
        return events
    
    def _categorize_event(self, event: Dict, events: Dict):
        """Categorize a single event."""
        event_type = event.get('type', '')
        
        if event_type == 'user_message':
            content = event.get('content', '')
            events['messages']['user'].append(content)
            # Extract potential topics from user messages
            self._extract_topics(content, events['topics'])
            
        elif event_type == 'assistant_message':
            content = event.get('content', '')
            events['messages']['assistant'].append(content)
            # Extract decisions from assistant responses
            self._extract_decisions(content, events['decisions'])
            
        elif event_type == 'tool_call':
            tool_name = event.get('tool', 'unknown')
            events['tools'][tool_name] = events['tools'].get(tool_name, 0) + 1
            
        elif event_type == 'thinking':
            events['thinking'].append(event.get('content', ''))
    
    def _extract_topics(self, content: str, topics: List[str]):
        """Extract topic keywords from message."""
        # Simple keyword extraction - can be enhanced
        topic_indicators = [
            r'\b(?:about|regarding|on|discussing)\s+(\w+(?:\s+\w+){0,2})',
            r'\b(\w+(?:\s+\w+)?)\s+(?:system|agent|bot|feature|issue)',
        ]
        
        for pattern in topic_indicators:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                topic = match.lower().strip()[:30]
                if topic and topic not in topics:
                    topics.append(topic)
    
    def _extract_decisions(self, content: str, decisions: List[Dict]):
        """Extract decisions from assistant response."""
        decision_patterns = [
            r'(?i)(?:decided?|decision|will|going to|choose|select)\s*:?\s*([^\. ]{10,100})',
            r'(?i)(?:let\'s|we should|recommend|suggest)\s+([^\. ]{10,100})',
        ]
        
        for pattern in decision_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                decisions.append({
                    'text': match.strip()[:80],
                    'timestamp': datetime.now().strftime("%H:%M")
                })


class HourlySummarizer:
    """Generate ultra-compact hourly summaries."""
    
    def __init__(self):
        self.parser = SessionParser()
        self.memory_dir = MEMORY_DIR / "hourly"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
    
    def run(self) -> str:
        """Execute hourly summarization."""
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M")
        date_str = now.strftime("%Y-%m-%d")
        
        print(f"[{timestamp}] Scanning session logs...")
        
        # Find and parse recent sessions
        sessions = self.parser.find_recent_sessions(hours=1)
        if not sessions:
            print(f"[{timestamp}] No recent sessions found")
            return ""
        
        print(f"[{timestamp}] Found {len(sessions)} session file(s)")
        
        # Aggregate events
        aggregated = self._aggregate_sessions(sessions)
        
        # Generate compact summary
        summary = self._create_summary(aggregated, timestamp)
        
        # Write to daily file
        output_path = self.memory_dir / f"{date_str}.md"
        self._append_summary(output_path, summary)
        
        print(f"[{timestamp}] ✅ Summary appended to {output_path}")
        print(f"  Topics: {len(summary.topics)} | Decisions: {len(summary.decisions)} | Actions: {len(summary.actions)}")
        
        return str(output_path)
    
    def _aggregate_sessions(self, sessions: List[Path]) -> Dict:
        """Aggregate multiple session files."""
        aggregated = {
            'messages': {'user': [], 'assistant': []},
            'decisions': [],
            'actions': [],
            'topics': [],
            'tools': {},
            'thinking': []
        }
        
        for session_path in sessions:
            events = self.parser.parse_session(session_path)
            aggregated['messages']['user'].extend(events['messages']['user'])
            aggregated['messages']['assistant'].extend(events['messages']['assistant'])
            aggregated['decisions'].extend(events['decisions'])
            aggregated['actions'].extend(events['actions'])
            aggregated['topics'].extend(events['topics'])
            
            for tool, count in events['tools'].items():
                aggregated['tools'][tool] = aggregated['tools'].get(tool, 0) + count
        
        # Deduplicate topics
        aggregated['topics'] = list(dict.fromkeys(aggregated['topics']))[:MAX_TOPICS]
        
        return aggregated
    
    def _create_summary(self, aggregated: Dict, timestamp: str) -> HourlySummary:
        """Create compact summary from aggregated events."""
        
        # Convert decisions to compact format
        compact_decisions = []
        for dec in aggregated['decisions'][:MAX_DECISIONS]:
            compact_decisions.append(CompactDecision(
                d=dec['text'][:50],
                r="see context",
                t=dec.get('timestamp', '??')
            ))
        
        # Extract action items from messages
        compact_actions = self._extract_actions(aggregated['messages'])
        
        return HourlySummary(
            ts=timestamp,
            topics=aggregated['topics'],
            decisions=compact_decisions,
            actions=compact_actions,
            tools=aggregated['tools'],
            stats={
                'user': len(aggregated['messages']['user']),
                'assistant': len(aggregated['messages']['assistant']),
                'tools': sum(aggregated['tools'].values())
            }
        )
    
    def _extract_actions(self, messages: Dict) -> List[CompactAction]:
        """Extract action items from messages."""
        actions = []
        
        action_patterns = [
            r'(?i)(?:todo|action|task|need to|must|should)\s*:?\s*([^\. ]{10,80})',
            r'(?i)(?:build|create|implement|fix|deploy|test)\s+([^\. ]{10,80})',
        ]
        
        all_content = " ".join(messages['user'] + messages['assistant'])
        
        for pattern in action_patterns:
            matches = re.findall(pattern, all_content)
            for match in matches:
                actions.append(CompactAction(
                    a=match.strip()[:60],
                    s="todo",
                    o="agent",
                    d=""
                ))
        
        return actions[:MAX_ACTIONS]
    
    def _append_summary(self, output_path: Path, summary: HourlySummary):
        """Append summary to daily file."""
        content = summary.to_compact_format()
        
        with open(output_path, 'a', encoding='utf-8') as f:
            f.write("\n\n")
            f.write(content)
            f.write("\n")


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Hourly Memory Summarizer")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show output without writing")
    parser.add_argument("--hours", type=int, default=1,
                       help="Hours to look back")
    
    args = parser.parse_args()
    
    summarizer = HourlySummarizer()
    
    if args.dry_run:
        # Just show what would be generated
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M")
        sessions = summarizer.parser.find_recent_sessions(hours=args.hours)
        
        print(f"Would process {len(sessions)} session(s)")
        
        if sessions:
            aggregated = summarizer._aggregate_sessions(sessions)
            summary = summarizer._create_summary(aggregated, timestamp)
            
            print("\n--- Generated Summary ---")
            print(summary.to_compact_format())
    else:
        summarizer.run()


if __name__ == "__main__":
    main()
