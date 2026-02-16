#!/usr/bin/env python3
"""
Post-Compaction Context Injector - Token-Budget Aware
Detects OpenClaw context compaction and injects critical memory to maintain continuity.
Designed for 3-7B models with strict token budgets.

Token Budget Allocation (max 1024 tokens for memory injection):
- Hourly summaries (last 24h): 400 tokens max
- Recent messages (15 each): 300 tokens max
- System context: 200 tokens max
- Thinking blocks: 124 tokens max

Author: Memory System for OpenClaw
Version: 1.0.0 (Token-Optimized)
"""

import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Token budget configuration
TOKEN_BUDGET = {
    'hourly_summaries': 400,
    'recent_messages': 300,
    'system_context': 200,
    'thinking_blocks': 124
}

MEMORY_DIR = Path(os.path.expanduser("~/.openclaw/workspace/memory"))
SESSION_DIR = Path(os.path.expanduser("~/.openclaw/logs/sessions"))
STATE_FILE = Path(os.path.expanduser("~/.openclaw/workspace/memory/.compaction_state"))


@dataclass
class TokenBudget:
    """Track token usage during injection."""
    used: int = 0
    limit: int = 1024
    
    def remaining(self) -> int:
        return self.limit - self.used
    
    def allocate(self, tokens: int) -> bool:
        if self.used + tokens <= self.limit:
            self.used += tokens
            return True
        return False


class CompactionDetector:
    """Detect when OpenClaw has compacted the conversation context."""
    
    def __init__(self):
        self.state_file = STATE_FILE
        self.session_dir = SESSION_DIR
    
    def check_compaction(self) -> Tuple[bool, Dict]:
        """
        Check if compaction has occurred.
        Returns: (compacted, metadata)
        """
        # Read previous state
        prev_state = self._load_state()
        
        # Get current session state
        current_state = self._get_current_state()
        
        # Detect compaction indicators
        compacted = self._detect_compaction(prev_state, current_state)
        
        # Update state
        self._save_state(current_state)
        
        return compacted, current_state
    
    def _load_state(self) -> Dict:
        """Load previous compaction state."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {'message_count': 0, 'timestamp': None}
    
    def _save_state(self, state: Dict):
        """Save current compaction state."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(state, f)
    
    def _get_current_state(self) -> Dict:
        """Get current session state from OpenClaw."""
        # Try to get from OpenClaw API or session files
        state = {
            'message_count': 0,
            'session_id': None,
            'timestamp': datetime.now().isoformat()
        }
        
        # Check session files
        if self.session_dir.exists():
            latest_session = self._get_latest_session()
            if latest_session:
                state['session_id'] = latest_session.stem
                state['message_count'] = self._count_messages(latest_session)
        
        return state
    
    def _get_latest_session(self) -> Optional[Path]:
        """Get most recent session file."""
        sessions = sorted(
            self.session_dir.glob("*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        return sessions[0] if sessions else None
    
    def _count_messages(self, session_path: Path) -> int:
        """Count messages in session file."""
        count = 0
        try:
            with open(session_path, 'r') as f:
                for line in f:
                    if line.strip():
                        count += 1
        except Exception:
            pass
        return count
    
    def _detect_compaction(self, prev: Dict, current: Dict) -> bool:
        """Detect if compaction occurred."""
        # Compaction indicators:
        # 1. Message count decreased significantly
        # 2. Session ID changed
        # 3. Large gap in message count (>50% reduction)
        
        if prev.get('session_id') != current.get('session_id'):
            return True
        
        prev_count = prev.get('message_count', 0)
        current_count = current.get('message_count', 0)
        
        if prev_count > 20 and current_count < prev_count * 0.5:
            return True
        
        return False


class ContextAssembler:
    """Assemble context injection package within token budget."""
    
    def __init__(self):
        self.memory_dir = MEMORY_DIR
    
    def assemble_injection(self, budget: TokenBudget = None) -> str:
        """
        Assemble context injection within token budget.
        Returns formatted context string ready for injection.
        """
        if budget is None:
            budget = TokenBudget()
        
        parts = []
        
        # 1. Hourly summaries (highest priority)
        hourly = self._get_hourly_summaries(budget.allocate(TOKEN_BUDGET['hourly_summaries']))
        if hourly:
            parts.append(f"## MEMORY\n{hourly}")
        
        # 2. Recent messages
        recent = self._get_recent_messages(budget.allocate(TOKEN_BUDGET['recent_messages']))
        if recent:
            parts.append(f"## RECENT\n{recent}")
        
        # 3. System context
        system = self._get_system_context(budget.allocate(TOKEN_BUDGET['system_context']))
        if system:
            parts.append(f"## CONTEXT\n{system}")
        
        # 4. Thinking blocks (if budget remains)
        thinking = self._get_thinking_blocks(budget.remaining())
        if thinking:
            parts.append(f"## REASONING\n{thinking}")
        
        return "\n\n".join(parts)
    
    def _get_hourly_summaries(self, token_limit: int) -> str:
        """Get last 24h of hourly summaries, truncated to token limit."""
        cutoff = datetime.now() - timedelta(hours=24)
        summaries = []
        
        hourly_dir = self.memory_dir / "hourly"
        if not hourly_dir.exists():
            return ""
        
        # Get recent daily files
        for day_file in sorted(hourly_dir.glob("*.md"), reverse=True):
            try:
                file_date = datetime.strptime(day_file.stem, "%Y-%m-%d")
                if file_date >= cutoff.date():
                    content = day_file.read_text()
                    # Extract individual hourly summaries
                    for summary in content.split("## ")[1:]:
                        if summary.strip():
                            summaries.append("## " + summary.strip())
            except Exception:
                continue
        
        # Truncate to token limit (rough estimate: 4 chars per token)
        result = "\n".join(summaries)
        max_chars = token_limit * 4
        if len(result) > max_chars:
            result = result[:max_chars] + " ... [truncated]"
        
        return result
    
    def _get_recent_messages(self, token_limit: int) -> str:
        """Get recent user/assistant messages."""
        session_dir = SESSION_DIR
        if not session_dir.exists():
            return ""
        
        latest = sorted(
            session_dir.glob("*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if not latest:
            return ""
        
        user_msgs = []
        assistant_msgs = []
        
        try:
            with open(latest[0], 'r') as f:
                lines = f.readlines()
                
                # Get last 15 of each type
                for line in reversed(lines):
                    if len(user_msgs) >= 15 and len(assistant_msgs) >= 15:
                        break
                    
                    try:
                        event = json.loads(line)
                        event_type = event.get('type', '')
                        content = event.get('content', '')[:100]  # Truncate each message
                        
                        if event_type == 'user_message' and len(user_msgs) < 15:
                            user_msgs.insert(0, f"U: {content}")
                        elif event_type == 'assistant_message' and len(assistant_msgs) < 15:
                            assistant_msgs.insert(0, f"A: {content}")
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass
        
        result = "\n".join(user_msgs[-15:] + assistant_msgs[-15:])
        max_chars = token_limit * 4
        if len(result) > max_chars:
            result = result[-max_chars:]  # Keep most recent
        
        return result
    
    def _get_system_context(self, token_limit: int) -> str:
        """Get system-level context."""
        context_parts = []
        
        # Agent registry
        registry_path = self.memory_dir / "global" / "agent_registry.md"
        if registry_path.exists():
            content = registry_path.read_text()[:200]
            context_parts.append(f"Agents: {content}")
        
        # Task log - active items only
        task_path = self.memory_dir / "global" / "task_log.md"
        if task_path.exists():
            lines = task_path.read_text().split('\n')
            active = [l for l in lines if '[ ]' in l or '[prog]' in l][:5]
            if active:
                context_parts.append("Tasks: " + " | ".join(active))
        
        # Mesh status
        mesh_path = self.memory_dir / "global" / "mesh_status_latest.json"
        if mesh_path.exists():
            try:
                status = json.loads(mesh_path.read_text())
                nodes = status.get('nodes', {})
                online = sum(1 for n in nodes.values() if n.get('status') == 'online')
                context_parts.append(f"Mesh: {online}/{len(nodes)} nodes online")
            except Exception:
                pass
        
        result = " | ".join(context_parts)
        max_chars = token_limit * 4
        if len(result) > max_chars:
            result = result[:max_chars]
        
        return result
    
    def _get_thinking_blocks(self, token_limit: int) -> str:
        """Get recent thinking/reasoning blocks."""
        session_dir = SESSION_DIR
        if not session_dir.exists() or token_limit < 50:
            return ""
        
        latest = sorted(
            session_dir.glob("*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if not latest:
            return ""
        
        thinking_blocks = []
        
        try:
            with open(latest[0], 'r') as f:
                lines = f.readlines()
                for line in reversed(lines):
                    if len(thinking_blocks) >= 15:
                        break
                    
                    try:
                        event = json.loads(line)
                        if event.get('type') == 'thinking':
                            content = event.get('content', '')[:80]
                            thinking_blocks.insert(0, f"- {content}")
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass
        
        result = "\n".join(thinking_blocks[-15:])
        max_chars = token_limit * 4
        if len(result) > max_chars:
            result = result[-max_chars:]
        
        return result


class PostCompactionInjector:
    """Main injector class - detects compaction and injects context."""
    
    def __init__(self):
        self.detector = CompactionDetector()
        self.assembler = ContextAssembler()
    
    def check_and_inject(self) -> Optional[str]:
        """
        Check for compaction and return injection context if detected.
        Returns None if no compaction detected.
        """
        compacted, metadata = self.detector.check_compaction()
        
        if not compacted:
            return None
        
        print(f"[COMPACTION DETECTED] Session: {metadata.get('session_id')}")
        print(f"[COMPACTION DETECTED] Messages: {metadata.get('message_count')}")
        
        # Assemble injection package
        injection = self.assembler.assemble_injection()
        
        # Log the injection
        self._log_injection(metadata, injection)
        
        return injection
    
    def _log_injection(self, metadata: Dict, injection: str):
        """Log injection event for debugging."""
        log_dir = self.assembler.memory_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / "compaction_injections.jsonl"
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': metadata.get('session_id'),
            'message_count': metadata.get('message_count'),
            'injection_size': len(injection),
            'injection_preview': injection[:200] + "..." if len(injection) > 200 else injection
        }
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Post-Compaction Context Injector")
    parser.add_argument("--check-only", action="store_true",
                       help="Only check for compaction")
    parser.add_argument("--force-inject", action="store_true",
                       help="Force injection regardless of detection")
    
    args = parser.parse_args()
    
    injector = PostCompactionInjector()
    
    if args.force_inject:
        injection = injector.assembler.assemble_injection()
        print("=== FORCED INJECTION ===")
        print(injection)
    elif args.check_only:
        compacted, metadata = injector.detector.check_compaction()
        if compacted:
            print(f"COMPACTION DETECTED: {metadata}")
        else:
            print("No compaction detected")
    else:
        injection = injector.check_and_inject()
        if injection:
            print("=== CONTEXT INJECTION ===")
            print(injection)
        else:
            print("No compaction - no injection needed")


if __name__ == "__main__":
    main()
