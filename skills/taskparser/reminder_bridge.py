#!/usr/bin/env python3
"""Reminder Bridge - Sets up cron reminders for tasks"""

import subprocess
import sys
from datetime import datetime, timedelta
from typing import Dict, Optional


def set_reminder(message: str, when: datetime, channel: str = "telegram") -> Dict:
    """
    Set up a reminder via cron.
    
    Args:
        message: What to remind about
        when: When to send the reminder
        channel: Where to send (telegram, etc.)
    
    Returns:
        Dict with success status
    """
    try:
        # Schedule reminder 1 hour before the task by default
        reminder_time = when - timedelta(hours=1)
        
        # Don't set if it's already in the past
        if reminder_time < datetime.now():
            return {
                'success': False,
                'skipped': True,
                'reason': 'Reminder time already passed',
            }
        
        # Build cron command via openclaw
        # This would use the cron tool to schedule
        cmd = [
            'openclaw', 'cron', 'add',
            '--at', reminder_time.isoformat(),
            '--message', f'Reminder: {message}',
        ]
        
        # For now, return mock since we're building
        return {
            'success': True,
            'mock': True,
            'message': message,
            'reminder_time': reminder_time.isoformat(),
            'task_time': when.isoformat(),
            'note': 'Cron reminder scheduled (mock - implement with openclaw cron)',
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
        }


def set_from_parsed(parsed: Dict, pre_notify_minutes: int = 60) -> Dict:
    """
    Set reminder from parsed task intent.
    
    Args:
        parsed: Output from TaskParser.parse_intent()
        pre_notify_minutes: How many minutes before to remind (default: 60)
    
    Returns:
        Result from set_reminder()
    """
    if not parsed.get('datetime'):
        return {
            'success': False,
            'error': 'No datetime in parsed task',
        }
    
    message = f"{parsed['action'].capitalize()}: {parsed['subject']}"
    task_time = datetime.fromisoformat(parsed['datetime'])
    reminder_time = task_time - timedelta(minutes=pre_notify_minutes)
    
    return set_reminder(
        message=message,
        when=reminder_time,
    )


if __name__ == '__main__':
    # Test
    from datetime import datetime, timedelta
    
    test_time = datetime.now() + timedelta(hours=2)
    result = set_reminder(
        message="Test: Call Mom",
        when=test_time,
    )
    
    print(json.dumps(result, indent=2))
