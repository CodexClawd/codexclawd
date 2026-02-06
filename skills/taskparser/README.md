# Task Intent Parser

Converts Flo's natural language task ramblings into structured data with calendar events and reminders.

## What It Does

Takes stuff like:
- `"call mom tomorrow"`
- `"email HR by friday"`
- `"grocery shopping this weekend"`

And turns it into:
- Structured task data
- Google Calendar event
- Telegram reminder

## Files

| File | Purpose |
|------|---------|
| `taskparser.py` | Main parsing logic |
| `calendar_bridge.py` | Creates Google Calendar events via gog |
| `reminder_bridge.py` | Sets up cron reminders |
| `test_examples.py` | Test cases |

## Usage

### Command Line

```bash
cd /home/boss/.openclaw/workspace/skills/taskparser
python3 taskparser.py "call mom tomorrow"
```

### From Python

```python
from taskparser import TaskParser

parser = TaskParser()
result = parser.parse_intent("email HR by friday")

print(result)
# {
#   'action': 'email',
#   'subject': 'HR',
#   'datetime': '2026-02-14T10:00:00',
#   'urgency': 'medium',
#   'source_text': 'email HR by friday'
# }
```

### Full Pipeline

```python
from taskparser import TaskParser
from calendar_bridge import create_from_parsed
from reminder_bridge import set_from_parsed

parser = TaskParser()
parsed = parser.parse_intent("call mom tomorrow")

# Create calendar event
calendar_result = create_from_parsed(parsed)

# Set reminder
reminder_result = set_from_parsed(parsed)
```

## Test It

```bash
python3 test_examples.py
```

## For BRUTUS

When Flo says something task-like, use this:

```python
# In your response to Flo
from skills.taskparser.taskparser import TaskParser
from skills.taskparser.calendar_bridge import create_from_parsed
from skills.taskparser.reminder_bridge import set_from_parsed

parser = TaskParser()
result = parser.parse_intent(flo_message)

if result['datetime']:
    # Ask Flo if he wants it scheduled
    print(f"Want me to add '{result['subject']}' to your calendar for {result['datetime']}?")
```

## Dependencies

- dateparser (auto-installed)
- gog skill (for calendar)
- openclaw cron (for reminders)

## Notes

- Defaults to 10am if no time specified
- Reminders set 1 hour before task
- Uses mock mode if gog/openclaw not configured
