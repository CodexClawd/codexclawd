#!/usr/bin/env python3
"""
Task Handler - Integration for BRUTUS to catch and schedule tasks

Usage from BRUTUS:
    from task_handler import handle_task_intent
    result = handle_task_intent("call dad tomorrow 10am")
    # result contains parsed data + asks user for confirmation
"""

import sys
import json
sys.path.insert(0, '/home/boss/.openclaw/workspace/skills/taskparser')

from taskparser import TaskParser
from calendar_bridge import create_from_parsed
from reminder_bridge import set_from_parsed


def detect_task_intent(text: str) -> bool:
    """Detect if text looks like a task/intent"""
    task_patterns = [
        r'\b(call|email|text|message)\b',
        r'\b(remind|remember|don\'t forget)\b',
        r'\b(should|need to|have to|must)\b.*\b(tomorrow|today|friday|monday|by)\b',
        r'\b(appointment|meeting|schedule)\b',
        r'\b(buy|get|pick up)\b.*\b(tomorrow|today|this week)\b',
    ]
    
    import re
    text_lower = text.lower()
    
    for pattern in task_patterns:
        if re.search(pattern, text_lower):
            return True
    
    return False


def format_task_prompt(parsed: dict) -> str:
    """Format a nice prompt asking if user wants to schedule it"""
    action = parsed['action']
    subject = parsed['subject']
    dt = parsed.get('datetime')
    
    if dt:
        from datetime import datetime
        dt_obj = datetime.fromisoformat(dt)
        time_str = dt_obj.strftime('%A %B %d at %I:%M %p')  # "Friday February 07 at 10:00 AM"
    else:
        time_str = "(no time specified)"
    
    emoji_map = {
        'call': '📞',
        'email': '📧',
        'buy': '🛒',
        'appointment': '📅',
        'remind': '⏰',
        'exercise': '💪',
        'clean': '🧹',
        'pay': '💰',
    }
    
    emoji = emoji_map.get(action, '✅')
    
    prompt = f"""{emoji} **Task Detected:**

""{subject}""

📅 When: {time_str}
⚡ Action: {action}

Want me to:
• Add to your Google Calendar?
• Set a reminder beforehand?

Reply **yes** to schedule both, or tell me what to skip."""
    
    return prompt


def auto_schedule(parsed: dict, set_calendar: bool = True, set_reminder: bool = True) -> dict:
    """
    Auto-schedule the parsed task.
    
    Returns dict with results:
    {
        'calendar': {'success': True, 'event_id': '...'},
        'reminder': {'success': True, 'reminder_time': '...'},
    }
    """
    from datetime import datetime, timedelta
    
    results = {
        'calendar': {'success': False},
        'reminder': {'success': False},
    }
    
    # Flo is in CET (UTC+1), so subtract 1 hour for UTC cron times
    CET_OFFSET = timedelta(hours=1)
    
    if set_calendar and parsed.get('datetime'):
        try:
            cal_result = create_from_parsed(parsed)
            results['calendar'] = cal_result
        except Exception as e:
            results['calendar']['error'] = str(e)
    
    if set_reminder and parsed.get('datetime'):
        try:
            # Convert CET to UTC for cron
            dt_str = parsed['datetime']
            dt_cet = datetime.fromisoformat(dt_str)
            dt_utc = dt_cet - CET_OFFSET
            
            # Update parsed with UTC time for reminder bridge
            parsed_utc = parsed.copy()
            parsed_utc['datetime'] = dt_utc.isoformat()
            
            rem_result = set_from_parsed(parsed_utc)
            rem_result['scheduled_for_cet'] = dt_cet.isoformat()
            rem_result['scheduled_for_utc'] = dt_utc.isoformat()
            results['reminder'] = rem_result
        except Exception as e:
            results['reminder']['error'] = str(e)
    
    return results


def handle_task_intent(text: str, auto_create: bool = False) -> dict:
    """
    Main entry point - detect, parse, and optionally schedule a task.
    
    Args:
        text: User's message
        auto_create: If True, skip confirmation and just do it
    
    Returns:
        Dict with all the info BRUTUS needs to respond
    """
    parser = TaskParser()
    parsed = parser.parse_intent(text)
    
    result = {
        'is_task': True,
        'parsed': parsed,
        'prompt': format_task_prompt(parsed),
        'scheduled': False,
    }
    
    if auto_create:
        schedule_results = auto_schedule(parsed)
        result['scheduled'] = True
        result['schedule_results'] = schedule_results
    
    return result


# Quick test
if __name__ == '__main__':
    test = "I need to call my dad tomorrow 10am"
    result = handle_task_intent(test)
    print(result['prompt'])
    print("\n" + "="*50)
    print("Raw parsed:")
    print(json.dumps(result['parsed'], indent=2))
