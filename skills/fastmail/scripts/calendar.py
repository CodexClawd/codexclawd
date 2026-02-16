"""
Fastmail CalDAV Calendar Integration

Create, read, update, delete calendar events via CalDAV.
Same credentials as SMTP (Fastmail app password works for both).
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
from urllib.parse import urlparse
import caldav

# Default CalDAV URL for Fastmail
CALDAV_URL = "https://caldav.fastmail.com"
DEFAULT_CALENDAR = "calendar"  # Default calendar name

def get_credentials():
    """Read Fastmail credentials from config file."""
    creds_file = os.path.expanduser("~/.config/fastmail/creds")
    try:
        with open(creds_file, 'r') as f:
            line = f.read().strip()
            email, password = line.split(':', 1)
            return email, password
    except Exception as e:
        print(f"Error reading credentials: {e}")
        sys.exit(1)

def get_caldav_client():
    """Initialize CalDAV client with Fastmail credentials."""
    email, password = get_credentials()
    
    client = caldav.DAVClient(
        url=CALDAV_URL,
        username=email,
        password=password
    )
    return client

def get_default_calendar(client=None):
    """Get the default calendar."""
    if client is None:
        client = get_caldav_client()
    
    principal = client.principal()
    calendars = principal.calendars()
    
    if not calendars:
        print("No calendars found!")
        return None
    
    # Return first calendar (usually the default)
    return calendars[0]

def create_event(summary, start_time, end_time=None, description="", location=""):
    """
    Create a calendar event.
    
    Args:
        summary: Event title
        start_time: datetime or ISO string
        end_time: datetime or ISO string (optional, defaults to 1 hour)
        description: Event description
        location: Event location
    """
    client = get_caldav_client()
    calendar = get_default_calendar(client)
    
    if calendar is None:
        return False
    
    # Parse start time
    if isinstance(start_time, str):
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    else:
        start_dt = start_time
    
    # Parse or default end time
    if end_time:
        if isinstance(end_time, str):
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        else:
            end_dt = end_time
    else:
        end_dt = start_dt + timedelta(hours=1)
    
    # Create the event
    event = calendar.save_event(
        dtstart=start_dt,
        dtend=end_dt,
        summary=summary,
        description=description,
        location=location
    )
    
    print(f"✓ Created event: {summary}")
    print(f"  When: {start_dt.strftime('%Y-%m-%d %H:%M')} - {end_dt.strftime('%H:%M')}")
    if location:
        print(f"  Where: {location}")
    
    return True

def list_events(days=7):
    """List upcoming events."""
    client = get_caldav_client()
    calendar = get_default_calendar(client)
    
    if calendar is None:
        return
    
    start = datetime.now()
    end = start + timedelta(days=days)
    
    events = calendar.date_search(start=start, end=end)
    
    print(f"\nUpcoming events ({len(events)} found):")
    print("=" * 50)
    
    for event in events:
        vevent = event.vobject_instance.vevent
        summary = vevent.summary.value if hasattr(vevent, 'summary') else "No title"
        start = vevent.dtstart.value
        
        if hasattr(start, 'strftime'):
            date_str = start.strftime('%a %d.%m.%Y %H:%M')
        else:
            date_str = str(start)
        
        print(f"• {date_str}: {summary}")
    
    print()

def main():
    parser = argparse.ArgumentParser(description='Fastmail Calendar CLI')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Create event
    create_parser = subparsers.add_parser('create', help='Create an event')
    create_parser.add_argument('--title', '-t', required=True, help='Event title')
    create_parser.add_argument('--start', '-s', required=True, help='Start time (ISO format or YYYY-MM-DD HH:MM)')
    create_parser.add_argument('--end', '-e', help='End time (optional, defaults to 1 hour)')
    create_parser.add_argument('--description', '-d', default='', help='Event description')
    create_parser.add_argument('--location', '-l', default='', help='Event location')
    
    # List events
    list_parser = subparsers.add_parser('list', help='List upcoming events')
    list_parser.add_argument('--days', '-d', type=int, default=7, help='Number of days to look ahead')
    
    args = parser.parse_args()
    
    if args.command == 'create':
        # Parse start time
        try:
            if ' ' in args.start:
                start = datetime.strptime(args.start, '%Y-%m-%d %H:%M')
            else:
                start = datetime.fromisoformat(args.start)
        except ValueError:
            print(f"Invalid start time format: {args.start}")
            print("Use: YYYY-MM-DD HH:MM (e.g., 2026-02-18 19:00)")
            sys.exit(1)
        
        # Parse end time if provided
        end = None
        if args.end:
            try:
                if ' ' in args.end:
                    end = datetime.strptime(args.end, '%Y-%m-%d %H:%M')
                else:
                    end = datetime.fromisoformat(args.end)
            except ValueError:
                print(f"Invalid end time format: {args.end}")
                sys.exit(1)
        
        create_event(args.title, start, end, args.description, args.location)
    
    elif args.command == 'list':
        list_events(args.days)
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
