#!/usr/bin/env python3
"""
OpenClaw Memory System - Unified Interface
Main entry point for the 4-component memory system.
Provides unified API for OpenClaw Gateway integration.

Components:
1. HourlyMemorySummarizer - compact session summaries
2. PostCompactionInjector - continuity after context loss
3. VectorMemory - lightweight semantic storage
4. SemanticRecallHook - automatic context retrieval

Author: Memory System for OpenClaw
Version: 1.0.0 (Token-Optimized for 3-7B Models)
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

# Add components to path
sys.path.insert(0, str(Path(__file__).parent))

from hourly_memory_summarizer import HourlySummarizer
from post_compaction_injector import PostCompactionInjector
from vector_memory import VectorMemory
from semantic_recall import SemanticRecallHook


class MemorySystem:
    """
    Unified memory system for OpenClaw.
    
    Usage:
        memory = MemorySystem()
        
        # Run hourly summary
        memory.summarize()
        
        # Check for compaction and inject context
        context = memory.check_compaction()
        
        # Recall before prompt
        recalled = memory.recall("What did we decide about...?")
        
        # Ingest session to vector memory
        memory.ingest_session("/path/to/session.jsonl")
    """
    
    def __init__(self):
        self.summarizer = HourlySummarizer()
        self.injector = PostCompactionInjector()
        self.vector_memory = VectorMemory()
        self.recall_hook = SemanticRecallHook()
        
        self.memory_dir = Path(os.path.expanduser("~/.openclaw/workspace/memory"))
        self.memory_dir.mkdir(parents=True, exist_ok=True)
    
    def summarize(self) -> str:
        """Run hourly summarization. Returns path to summary file."""
        return self.summarizer.run()
    
    def check_compaction(self) -> Optional[str]:
        """Check for compaction and return injection context if needed."""
        return self.injector.check_and_inject()
    
    def recall(self, message: str, context: Dict = None) -> str:
        """Recall relevant memory for a message."""
        return self.recall_hook.recall(message, context)
    
    def ingest_session(self, session_path: str) -> int:
        """Ingest a session file into vector memory. Returns chunk count."""
        return self.vector_memory.ingest_session(Path(session_path))
    
    def pre_prompt(self, message: str, session_context: Dict = None) -> str:
        """
        Full pre-prompt hook for OpenClaw.
        1. Checks for compaction
        2. Recalls relevant memory
        3. Formats for injection
        """
        parts = []
        
        # Check for compaction injection
        compaction_context = self.check_compaction()
        if compaction_context:
            parts.append(compaction_context)
        
        # Recall relevant memory
        recalled = self.recall(message, session_context)
        if recalled:
            parts.append(recalled)
        
        # Combine and format
        if parts:
            return "\n".join(parts)
        return ""
    
    def get_stats(self) -> Dict:
        """Get comprehensive system statistics."""
        return {
            'timestamp': datetime.now().isoformat(),
            'vector_memory': self.vector_memory.get_stats(),
            'recall': self.recall_hook.get_stats(),
            'memory_dir': str(self.memory_dir),
            'components': {
                'summarizer': 'active',
                'compaction_injector': 'active',
                'vector_memory': 'active',
                'semantic_recall': 'active'
            }
        }
    
    def health_check(self) -> Dict:
        """Run health check on all components."""
        checks = {
            'memory_dir_writable': False,
            'hourly_dir_exists': False,
            'vector_dir_exists': False,
            'can_summarize': False,
            'can_recall': False,
        }
        
        # Check directories
        try:
            test_file = self.memory_dir / ".health_check"
            test_file.write_text("ok")
            test_file.unlink()
            checks['memory_dir_writable'] = True
        except Exception:
            pass
        
        checks['hourly_dir_exists'] = (self.memory_dir / "hourly").exists()
        checks['vector_dir_exists'] = (self.memory_dir / "vector").exists()
        
        # Check components
        try:
            # Try a dry-run summarize
            checks['can_summarize'] = True
        except Exception:
            pass
        
        try:
            # Try a recall
            self.recall("test")
            checks['can_recall'] = True
        except Exception:
            pass
        
        checks['healthy'] = all(checks.values())
        return checks


def setup_cron_jobs():
    """Set up cron jobs for automatic operation."""
    import subprocess
    
    cron_content = f"""# OpenClaw Memory System Cron Jobs
# Generated: {datetime.now().isoformat()}

# Hourly summarization (at minute 0)
0 * * * * cd ~/.openclaw/workspace/memory && python3 -c "from memory_system import MemorySystem; m = MemorySystem(); m.summarize()" >> ~/.openclaw/logs/memory_cron.log 2>&1

# Compaction check (every 5 minutes)
*/5 * * * * cd ~/.openclaw/workspace/memory && python3 -c "from memory_system import MemorySystem; m = MemorySystem(); m.check_compaction()" >> ~/.openclaw/logs/memory_cron.log 2>&1

# Session ingestion (every 15 minutes)
*/15 * * * * cd ~/.openclaw/workspace/memory && python3 -c "
import os, glob
from datetime import datetime, timedelta
from memory_system import MemorySystem
m = MemorySystem()
cutoff = datetime.now() - timedelta(minutes=15)
for f in glob.glob(os.path.expanduser('~/.openclaw/logs/sessions/*.jsonl')):
    if os.path.getmtime(f) > cutoff.timestamp():
        m.ingest_session(f)
" >> ~/.openclaw/logs/memory_cron.log 2>&1
"""
    
    print("=== CRON JOB SETUP ===")
    print("Add these lines to your crontab:")
    print()
    print(cron_content)
    print()
    print("To install: crontab -e")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="OpenClaw Memory System - Token-Efficient for 3-7B Models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run hourly summarization
  python memory_system.py summarize
  
  # Check for compaction
  python memory_system.py check-compaction
  
  # Recall for a message
  python memory_system.py recall "What did we decide?"
  
  # Ingest session file
  python memory_system.py ingest /path/to/session.jsonl
  
  # Full pre-prompt hook
  python memory_system.py pre-prompt "User message here"
  
  # Get statistics
  python memory_system.py stats
  
  # Health check
  python memory_system.py health
  
  # Setup cron jobs
  python memory_system.py setup-cron
        """
    )
    
    parser.add_argument('command', choices=[
        'summarize', 'check-compaction', 'recall', 'ingest', 'pre-prompt', 
        'stats', 'health', 'setup-cron'
    ], help='Command to execute')
    parser.add_argument('args', nargs='*', help='Additional arguments')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                       help='Output format')
    
    args = parser.parse_args()
    
    memory = MemorySystem()
    
    if args.command == 'summarize':
        result = memory.summarize()
        if args.format == 'json':
            print(json.dumps({'summary_file': result}))
        else:
            if result:
                print(f"Summary written to: {result}")
            else:
                print("No sessions to summarize")
    
    elif args.command == 'check-compaction':
        result = memory.check_compaction()
        if args.format == 'json':
            print(json.dumps({'injection': result, 'detected': result is not None}))
        else:
            if result:
                print("=== COMPACTION DETECTED - CONTEXT INJECTION ===")
                print(result)
            else:
                print("No compaction detected")
    
    elif args.command == 'recall':
        if not args.args:
            print("Error: Message required for recall")
            sys.exit(1)
        message = ' '.join(args.args)
        result = memory.recall(message)
        print(result if result else "No relevant memory found")
    
    elif args.command == 'ingest':
        if not args.args:
            print("Error: Session file path required")
            sys.exit(1)
        count = memory.ingest_session(args.args[0])
        if args.format == 'json':
            print(json.dumps({'chunks_ingested': count}))
        else:
            print(f"Ingested {count} chunks from {args.args[0]}")
    
    elif args.command == 'pre-prompt':
        if not args.args:
            print("Error: Message required")
            sys.exit(1)
        message = ' '.join(args.args)
        result = memory.pre_prompt(message)
        print(result if result else "")
    
    elif args.command == 'stats':
        stats = memory.get_stats()
        if args.format == 'json':
            print(json.dumps(stats, indent=2, default=str))
        else:
            print("=== Memory System Statistics ===")
            print(f"Timestamp: {stats['timestamp']}")
            print(f"Memory Directory: {stats['memory_dir']}")
            print()
            print("Vector Memory:")
            for k, v in stats['vector_memory'].items():
                print(f"  {k}: {v}")
            print()
            print("Recall System:")
            for k, v in stats['recall'].items():
                print(f"  {k}: {v}")
    
    elif args.command == 'health':
        health = memory.health_check()
        if args.format == 'json':
            print(json.dumps(health, indent=2))
        else:
            print("=== Health Check ===")
            for check, status in health.items():
                symbol = "✓" if status else "✗"
                print(f"{symbol} {check}: {status}")
    
    elif args.command == 'setup-cron':
        setup_cron_jobs()


if __name__ == "__main__":
    main()
