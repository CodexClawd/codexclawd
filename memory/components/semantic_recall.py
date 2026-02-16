#!/usr/bin/env python3
"""
Semantic Recall Hook - Automatic Memory Retrieval
Automatically retrieves relevant context from vector memory before each prompt.
Designed for minimal token overhead and fast local inference.

Features:
- Query extraction from incoming messages
- Multi-source retrieval (vector + hourly + recent)
- Token budget enforcement
- Deduplication and ranking
- Caching for repeated queries

Integration: Hook into OpenClaw's pre-prompt pipeline

Author: Memory System for OpenClaw
Version: 1.0.0 (Token-Optimized)
"""

import os
import json
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass

# Import vector memory
from vector_memory import VectorMemory, MEMORY_DIR

# Configuration
MAX_RECALL_TOKENS = 400  # Max tokens for recalled context
CACHE_TTL_MINUTES = 5  # Cache recall results
RECENT_CONTEXT_MESSAGES = 5  # Always include N most recent


@dataclass
class RecallResult:
    """Result of a semantic recall operation."""
    query: str
    sources: List[Dict]
    total_tokens: int
    cache_hit: bool
    retrieval_time_ms: int


class QueryExtractor:
    """Extract search queries from user messages."""
    
    def __init__(self):
        # Patterns that indicate memory needs
        self.memory_indicators = [
            r'(?i)(?:what|when|where|why|how)\s+(?:did|was|were|have|had)',
            r'(?i)(?:remind|remember|recall|forget)',
            r'(?i)(?:earlier|before|previously|last|yesterday)',
            r'(?i)(?:said|mentioned|told|discussed|decided)',
            r'(?i)(?:about|regarding)\s+(?:the|that|this)',
        ]
        
        # Entity patterns for keyword extraction
        self.entity_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Capitalized phrases
            r'\b\w+(?:_\w+)+\b',  # snake_case
            r'\b\w+(?:\.\w+)+\b',  # dot.notation
        ]
    
    def needs_recall(self, message: str) -> bool:
        """Check if message likely needs memory retrieval."""
        for pattern in self.memory_indicators:
            if re.search(pattern, message):
                return True
        return False
    
    def extract_queries(self, message: str) -> List[str]:
        """Extract search queries from message."""
        queries = [message[:200]]  # Full message
        
        # Extract entities
        entities = set()
        for pattern in self.entity_patterns:
            matches = re.findall(pattern, message)
            entities.update(matches)
        
        # Add entity combinations as secondary queries
        if len(entities) >= 2:
            entity_list = list(entities)[:4]
            queries.append(" ".join(entity_list))
        
        # Add individual important entities
        for entity in list(entities)[:3]:
            if len(entity) > 4:
                queries.append(entity)
        
        return queries


class RecallCache:
    """Simple LRU cache for recall results."""
    
    def __init__(self, ttl_minutes: int = CACHE_TTL_MINUTES):
        self.ttl = timedelta(minutes=ttl_minutes)
        self.cache: Dict[str, Tuple[RecallResult, datetime]] = {}
    
    def get(self, key: str) -> Optional[RecallResult]:
        """Get cached result if not expired."""
        if key in self.cache:
            result, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                # Mark as cache hit
                return RecallResult(
                    query=result.query,
                    sources=result.sources,
                    total_tokens=result.total_tokens,
                    cache_hit=True,
                    retrieval_time_ms=0
                )
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, result: RecallResult):
        """Cache a result."""
        self.cache[key] = (result, datetime.now())
    
    def clear(self):
        """Clear all cached results."""
        self.cache.clear()


class TokenBudgetManager:
    """Manage token budget for recalled context."""
    
    def __init__(self, max_tokens: int = MAX_RECALL_TOKENS):
        self.max_tokens = max_tokens
        self.used_tokens = 0
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars per token)."""
        return len(text) // 4
    
    def can_add(self, text: str) -> bool:
        """Check if text fits in remaining budget."""
        return self.used_tokens + self.estimate_tokens(text) <= self.max_tokens
    
    def add(self, text: str) -> bool:
        """Add text to budget if possible."""
        tokens = self.estimate_tokens(text)
        if self.used_tokens + tokens <= self.max_tokens:
            self.used_tokens += tokens
            return True
        return False
    
    def remaining(self) -> int:
        """Get remaining token budget."""
        return self.max_tokens - self.used_tokens


class SemanticRecallHook:
    """Main recall hook - integrates with OpenClaw pre-prompt."""
    
    def __init__(self):
        self.vector_memory = VectorMemory()
        self.query_extractor = QueryExtractor()
        self.cache = RecallCache()
        self.memory_dir = MEMORY_DIR
    
    def recall(self, message: str, context: Dict = None) -> str:
        """
        Main entry point - recall relevant memory for a message.
        Returns formatted context string ready for injection.
        """
        import time
        start_time = time.time()
        
        # Check if recall is needed
        if not self.query_extractor.needs_recall(message):
            return ""
        
        # Check cache
        cache_key = hashlib.md5(message.encode()).hexdigest()
        cached = self.cache.get(cache_key)
        if cached:
            return self._format_recall_result(cached)
        
        # Extract queries
        queries = self.query_extractor.extract_queries(message)
        
        # Retrieve from multiple sources
        budget = TokenBudgetManager()
        all_sources = []
        
        # 1. Vector memory search (highest relevance)
        for query in queries[:2]:  # Limit to top 2 queries
            results = self.vector_memory.search(query, top_k=3)
            for r in results:
                source_text = f"[{r['timestamp']}] {r['text']}"
                if budget.can_add(source_text):
                    all_sources.append({
                        'text': source_text,
                        'relevance': r['relevance'],
                        'source': 'vector',
                        'timestamp': r['timestamp']
                    })
                    budget.add(source_text)
        
        # 2. Recent hourly summaries (if budget remains)
        if budget.remaining() > 100:
            hourly = self._get_recent_hourly(budget.remaining())
            for h in hourly:
                if budget.can_add(h['text']):
                    all_sources.append(h)
                    budget.add(h['text'])
        
        # 3. Recent conversation context (always include last N)
        recent = self._get_recent_context(RECENT_CONTEXT_MESSAGES)
        
        # Deduplicate and rank
        seen_texts = set()
        unique_sources = []
        for s in sorted(all_sources, key=lambda x: x['relevance'], reverse=True):
            text_hash = hashlib.md5(s['text'][:50].encode()).hexdigest()
            if text_hash not in seen_texts:
                seen_texts.add(text_hash)
                unique_sources.append(s)
        
        # Build result
        retrieval_time = int((time.time() - start_time) * 1000)
        result = RecallResult(
            query=queries[0] if queries else message,
            sources=unique_sources[:5],
            total_tokens=budget.used_tokens,
            cache_hit=False,
            retrieval_time_ms=retrieval_time
        )
        
        # Cache result
        self.cache.set(cache_key, result)
        
        # Format output
        return self._format_recall_result(result, recent)
    
    def _get_recent_hourly(self, token_budget: int) -> List[Dict]:
        """Get recent hourly summaries."""
        cutoff = datetime.now() - timedelta(hours=24)
        summaries = []
        
        hourly_dir = self.memory_dir / "hourly"
        if not hourly_dir.exists():
            return summaries
        
        for day_file in sorted(hourly_dir.glob("*.md"), reverse=True):
            try:
                file_date = datetime.strptime(day_file.stem, "%Y-%m-%d")
                if file_date >= cutoff.date():
                    content = day_file.read_text()
                    # Parse hourly sections
                    for section in content.split("## ")[1:]:
                        lines = section.strip().split('\n')
                        if lines:
                            timestamp = lines[0].strip()
                            body = ' '.join(lines[1:]).strip()[:150]
                            summaries.append({
                                'text': f"[{timestamp}] {body}",
                                'relevance': 0.5,
                                'source': 'hourly',
                                'timestamp': timestamp
                            })
            except Exception:
                continue
        
        return summaries[:3]  # Max 3 hourly summaries
    
    def _get_recent_context(self, n_messages: int) -> List[str]:
        """Get N most recent messages from current session."""
        session_dir = Path(os.path.expanduser("~/.openclaw/logs/sessions"))
        if not session_dir.exists():
            return []
        
        latest = sorted(
            session_dir.glob("*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if not latest:
            return []
        
        messages = []
        try:
            with open(latest[0], 'r') as f:
                lines = f.readlines()
                for line in reversed(lines):
                    if len(messages) >= n_messages:
                        break
                    try:
                        event = json.loads(line)
                        event_type = event.get('type', '')
                        content = event.get('content', '')[:80]
                        if event_type == 'user_message':
                            messages.insert(0, f"U: {content}")
                        elif event_type == 'assistant_message':
                            messages.insert(0, f"A: {content}")
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass
        
        return messages
    
    def _format_recall_result(self, result: RecallResult, recent: List[str] = None) -> str:
        """Format recall result for injection."""
        if not result.sources and not recent:
            return ""
        
        lines = ["## RECALLED"]
        
        if result.sources:
            lines.append("")
            for s in result.sources:
                lines.append(f"• {s['text']}")
        
        if recent:
            lines.append("")
            lines.append("RECENT:")
            for r in recent:
                lines.append(f"  {r}")
        
        lines.append("")
        lines.append(f"[recall: {len(result.sources)} sources, ~{result.total_tokens}t, {result.retrieval_time_ms}ms]")
        
        return "\n".join(lines)
    
    def get_stats(self) -> Dict:
        """Get recall system statistics."""
        return {
            'vector_memory': self.vector_memory.get_stats(),
            'cache_entries': len(self.cache.cache),
            'max_recall_tokens': MAX_RECALL_TOKENS
        }


class OpenClawIntegration:
    """Integration layer for OpenClaw Gateway."""
    
    def __init__(self):
        self.recall_hook = SemanticRecallHook()
    
    def pre_prompt_hook(self, message: str, session_context: Dict = None) -> str:
        """
        Hook to call before sending prompt to LLM.
        Returns context to prepend to prompt.
        """
        recalled = self.recall_hook.recall(message, session_context)
        return recalled
    
    def format_for_openclaw(self, message: str, recalled_context: str) -> str:
        """
        Format message with recalled context for OpenClaw.
        """
        if not recalled_context:
            return message
        
        # Compact format that small models can parse
        return f"{recalled_context}\n---\nUSER: {message}"


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Semantic Recall Hook")
    parser.add_argument("message", nargs="?", help="Message to recall for")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--test-integration", action="store_true",
                       help="Test OpenClaw integration")
    
    args = parser.parse_args()
    
    hook = SemanticRecallHook()
    
    if args.message:
        print(f"🔍 Recalling for: '{args.message}'")
        print()
        result = hook.recall(args.message)
        if result:
            print(result)
        else:
            print("No relevant memory found.")
    
    elif args.stats:
        stats = hook.get_stats()
        print("Semantic Recall Statistics:")
        print(json.dumps(stats, indent=2, default=str))
    
    elif args.test_integration:
        integration = OpenClawIntegration()
        test_msg = "What did we decide about the memory system yesterday?"
        print(f"Test message: {test_msg}")
        print()
        recalled = integration.pre_prompt_hook(test_msg)
        formatted = integration.format_for_openclaw(test_msg, recalled)
        print("=== FORMATTED FOR OPENCLAW ===")
        print(formatted)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
