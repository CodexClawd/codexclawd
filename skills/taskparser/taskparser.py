#!/usr/bin/env python3
"""Task Intent Parser - Converts natural language to structured tasks

Usage:
    python taskparser.py "call mom tomorrow"
    python taskparser.py "email HR by friday"
"""

import sys
import re
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import subprocess

# Add venv to path
sys.path.insert(0, '/home/boss/.openclaw/workspace/venv/lib/python3.12/site-packages')

try:
    import dateparser
except ImportError:
    print("Installing dateparser...")
    subprocess.run([sys.executable, "-m", "pip", "install", "dateparser", "-q"])
    import dateparser


class TaskParser:
    """Parse natural language tasks into structured data"""
    
    def __init__(self):
        self.action_keywords = {
            'call': ['call', 'phone', 'ring', 'facetime'],
            'email': ['email', 'mail', 'write to', 'message'],
            'remind': ['remind', 'remember', 'dont forget'],
            'buy': ['buy', 'purchase', 'get', 'pick up'],
            'meet': ['meet', 'appointment', 'schedule', 'book'],
            'pay': ['pay', 'send money', 'transfer'],
            'clean': ['clean', 'tidy', 'organize'],
            'exercise': ['workout', 'exercise', 'gym', 'run'],
        }
        
        self.urgency_keywords = {
            'high': ['asap', 'urgent', 'important', 'critical', 'today'],
            'medium': ['soon', 'this week', 'tomorrow'],
            'low': ['whenever', 'sometime', 'eventually'],
        }
    
    def parse_intent(self, text: str) -> Dict:
        """Main entry point - parse natural language into structured task"""
        text_lower = text.lower()
        
        # Extract components
        action = self._extract_action(text_lower)
        subject = self._extract_subject(text)
        dt, time_context = self._extract_datetime(text)
        urgency = self._extract_urgency(text_lower, dt)
        
        result = {
            'action': action,
            'subject': subject,
            'datetime': dt.isoformat() if dt else None,
            'time_context': time_context,
            'urgency': urgency,
            'source_text': text,
            'parsed_at': datetime.now().isoformat(),
        }
        
        return result
    
    def _extract_action(self, text: str) -> str:
        """Extract the action verb from text"""
        for action, keywords in self.action_keywords.items():
            for kw in keywords:
                if kw in text:
                    return action
        
        # Default actions based on patterns
        if 'remind' in text:
            return 'remind'
        if any(word in text for word in ['by', 'before', 'due']):
            return 'deadline'
        
        return 'task'  # generic fallback
    
    def _extract_subject(self, text: str) -> str:
        """Extract what the task is about"""
        # Remove common prefixes
        prefixes = [
            r'^i should\s+',
            r'^i need to\s+',
            r'^remind me to\s+',
            r'^dont forget to\s+',
            r'^need to\s+',
            r'^have to\s+',
        ]
        
        subject = text
        for prefix in prefixes:
            subject = re.sub(prefix, '', subject, flags=re.IGNORECASE)
        
        # Remove time expressions for cleaner subject
        time_patterns = [
            r'\b(tomorrow|today|tonight|yesterday)\b',
            r'\b(on |at |by )?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            r'\b(in \d+ (minutes?|hours?|days?|weeks?))\b',
            r'\b(next week|this week|this month)\b',
            r'\bat \d{1,2}(:\d{2})?\s*(am|pm)?\b',
        ]
        
        for pattern in time_patterns:
            subject = re.sub(pattern, '', subject, flags=re.IGNORECASE)
        
        # Clean up
        subject = re.sub(r'\s+', ' ', subject).strip()
        subject = subject.strip('.!?,')
        
        return subject if subject else text
    
    def _extract_datetime(self, text: str) -> Tuple[Optional[datetime], str]:
        """Extract datetime from text using dateparser and patterns"""
        text_lower = text.lower()
        now = datetime.now()
        
        # Pattern matching for common phrases (faster than dateparser)
        
        # Days of week
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for i, day in enumerate(days):
            if day in text_lower:
                target_day = i
                current_day = now.weekday()
                days_ahead = (target_day - current_day) % 7
                if days_ahead == 0:  # If today, move to next week
                    days_ahead = 7
                dt = now + timedelta(days=days_ahead)
                dt = dt.replace(hour=10, minute=0, second=0, microsecond=0)
                
                # Check for time
                time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', text_lower)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2) or 0)
                    ampm = time_match.group(3)
                    if ampm == 'pm' and hour < 12:
                        hour += 12
                    dt = dt.replace(hour=hour, minute=minute)
                
                return dt, f'{day}_pattern'
        
        # Tomorrow
        if 'tomorrow' in text_lower:
            dt = now + timedelta(days=1)
            dt = dt.replace(hour=10, minute=0, second=0, microsecond=0)
            
            # Check for "at Xpm/am"
            time_match = re.search(r'at\s+(\d{1,2}):?(\d{2})?\s*(am|pm)?', text_lower)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2) or 0)
                ampm = time_match.group(3)
                if ampm == 'pm' and hour < 12:
                    hour += 12
                dt = dt.replace(hour=hour, minute=minute)
            
            return dt, 'tomorrow_default'
        
        # Today with time
        if 'today' in text_lower:
            dt = now
            time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', text_lower)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2) or 0)
                ampm = time_match.group(3)
                if ampm == 'pm' and hour < 12:
                    hour += 12
                dt = dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
            else:
                dt = dt.replace(hour=18, minute=0, second=0, microsecond=0)
            return dt, 'today_default'
        
        # Bare time (e.g., "at 8pm")
        time_match = re.search(r'at\s+(\d{1,2}):?(\d{2})?\s*(am|pm)?', text_lower)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            ampm = time_match.group(3)
            if ampm == 'pm' and hour < 12:
                hour += 12
            dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if dt < now:
                dt += timedelta(days=1)  # Tomorrow if time passed
            return dt, 'time_only'
        
        # This weekend -> Saturday
        if 'weekend' in text_lower:
            days_to_sat = (5 - now.weekday()) % 7
            if days_to_sat == 0:
                days_to_sat = 7
            dt = now + timedelta(days=days_to_sat)
            dt = dt.replace(hour=10, minute=0, second=0, microsecond=0)
            return dt, 'weekend_default'
        
        # Try dateparser as fallback
        settings = {
            'PREFER_DATES_FROM': 'future',
            'RETURN_AS_TIMEZONE_AWARE': False,
        }
        
        parsed = dateparser.parse(text, settings=settings)
        
        if parsed:
            # If no time specified, default to reasonable time
            if parsed.hour == 0 and parsed.minute == 0:
                if 'morning' in text_lower:
                    parsed = parsed.replace(hour=9, minute=0)
                elif 'evening' in text_lower or 'night' in text_lower:
                    parsed = parsed.replace(hour=20, minute=0)
                elif 'afternoon' in text_lower:
                    parsed = parsed.replace(hour=14, minute=0)
                else:
                    parsed = parsed.replace(hour=10, minute=0)
            
            return parsed, 'dateparser'
        
        return None, 'unspecified'
    
    def _extract_urgency(self, text: str, dt: Optional[datetime]) -> str:
        """Determine urgency level"""
        for level, keywords in self.urgency_keywords.items():
            for kw in keywords:
                if kw in text:
                    return level
        
        # Check if it's soon
        if dt:
            delta = dt - datetime.now()
            if delta.days < 1:
                return 'high'
            elif delta.days < 3:
                return 'medium'
        
        return 'medium'  # default
    
    def format_summary(self, result: Dict) -> str:
        """Pretty print the parsed result"""
        lines = [
            f"📋 Task: {result['subject']}",
            f"🏷️  Action: {result['action']}",
        ]
        
        if result['datetime']:
            dt = datetime.fromisoformat(result['datetime'])
            lines.append(f"📅 When: {dt.strftime('%Y-%m-%d %H:%M')}")
        else:
            lines.append(f"📅 When: (not specified)")
        
        lines.append(f"⚡ Urgency: {result['urgency']}")
        
        return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python taskparser.py 'call mom tomorrow'")
        print("       python taskparser.py 'email HR by friday'")
        sys.exit(1)
    
    text = ' '.join(sys.argv[1:])
    parser = TaskParser()
    result = parser.parse_intent(text)
    
    print(parser.format_summary(result))
    print("\n" + "="*50)
    print("JSON output:")
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
