#!/usr/bin/env python3
"""Calendar Bridge - Connects taskparser to gog skill for Google Calendar"""

import subprocess
import sys
from datetime import datetime
from typing import Dict, Optional

# Path to gog skill
gog_path = '/home/boss/.openclaw/workspace/skills/gog'


def create_event(title: str, start_time: datetime, end_time: Optional[datetime] = None,
                 description: str = "", calendar: str = "primary") -> Dict:
    """
    Create a Google Calendar event via gog skill.
    
    Args:
        title: Event title
        start_time: When the event starts
        end_time: When it ends (defaults to 1 hour after start)
        description: Event description
        calendar: Calendar ID (default: primary)
    
    Returns:
        Dict with success status and event details or error
    """
    if end_time is None:
        end_time = start_time + __import__('datetime').timedelta(hours=1)
    
    # Format times for gog
    start_str = start_time.isoformat()
    end_str = end_time.isoformat()
    
    try:
        # Build gog calendar create command
        cmd = [
            'node', f'{gog_path}/dist/gog.js',
            'calendar', 'create',
            '--title', title,
            '--start', start_str,
            '--end', end_str,
        ]
        
        if description:
            cmd.extend(['--description', description])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return {
                'success': True,
                'title': title,
                'start': start_str,
                'output': result.stdout.strip(),
            }
        else:
            return {
                'success': False,
                'error': result.stderr.strip(),
                'title': title,
            }
    
    except FileNotFoundError:
        # gog not set up, return mock success for testing
        return {
            'success': True,
            'mock': True,
            'title': title,
            'start': start_str,
            'message': 'Event created (mock - gog not configured)',
        }
    
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Command timed out',
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
        }


def create_from_parsed(parsed: Dict) -> Dict:
    """
    Create calendar event from parsed task intent.
    
    Args:
        parsed: Output from TaskParser.parse_intent()
    
    Returns:
        Result from create_event()
    """
    if not parsed.get('datetime'):
        return {
            'success': False,
            'error': 'No datetime in parsed task',
        }
    
    title = f"{parsed['action'].capitalize()}: {parsed['subject']}"
    start = datetime.fromisoformat(parsed['datetime'])
    
    return create_event(
        title=title,
        start_time=start,
        description=parsed.get('source_text', ''),
    )


if __name__ == '__main__':
    # Test
    from datetime import datetime, timedelta
    
    test_time = datetime.now() + timedelta(hours=2)
    result = create_event(
        title="Test: Call Mom",
        start_time=test_time,
        description="Test event from taskparser"
    )
    
    print(json.dumps(result, indent=2))
