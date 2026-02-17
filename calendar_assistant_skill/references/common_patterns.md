# Common Calendar Patterns

This reference provides common patterns for the Calendar Assistant Skill.

## Natural Language Parsing Patterns

### Relative Dates

- **Tomorrow**: Current date + 1 day
- **Next Monday/Tuesday/etc**: Next occurrence of that weekday
- **In 3 days**: Current date + 3 days
- **Next week**: 7 days from now
- **Next month**: Same day next month

### Time Expressions

- **2pm, 2:00pm, 14:00**: 14:00 in 24-hour format
- **Noon**: 12:00
- **Midnight**: 00:00
- **Morning**: 09:00 (default)
- **Afternoon**: 14:00 (default)
- **Evening**: 18:00 (default)

### Duration Patterns

- **For 1 hour**: duration_hours = 1.0
- **For 2 hours**: duration_hours = 2.0
- **30 minutes**: duration_hours = 0.5
- **90 minutes**: duration_hours = 1.5
- **All day**: Use DATE value instead of DATETIME

## Event Type Templates

### Meeting Template
```python
{
    "summary": "Team Meeting",
    "duration_hours": 1.0,
    "reminder_hours": 1.0,
    "description": "Regular team sync",
}
```

### Appointment Template
```python
{
    "summary": "Doctor Appointment",
    "duration_hours": 0.5,
    "reminder_hours": 2.0,
    "location": "Medical Center",
}
```

### Deadline Template
```python
{
    "summary": "Project Deadline",
    "duration_hours": 0,  # Point in time
    "reminder_hours": 24.0,
    "description": "Final submission due",
}
```

### Conference Template
```python
{
    "summary": "Tech Conference",
    "duration_hours": 8.0,
    "reminder_hours": 24.0,
    "location": "Convention Center",
}
```

## Reminder Strategies

| Event Type | Default Reminder | Notes |
|------------|------------------|-------|
| Meeting | 1 hour before | Standard workplace |
| Appointment | 30-60 min before | Travel time consideration |
| Deadline | 1 day before | Allow preparation time |
| All-day event | Morning of | Start-of-day reminder |
| Multi-day | 1 day before start | Planning reminder |

## Common Scheduling Scenarios

### Quick Meeting
**Input**: "Schedule a team meeting tomorrow at 2pm"
**Parsing**:
- summary: "Team Meeting"
- start_date: tomorrow
- start_time: "14:00"
- duration_hours: 1.0 (default)

### Appointment with Location
**Input**: "Dentist appointment on Friday at 10:30am at Downtown Dental"
**Parsing**:
- summary: "Dentist Appointment"
- start_date: next Friday
- start_time: "10:30"
- location: "Downtown Dental"
- duration_hours: 1.0

### Long Event
**Input**: "Company retreat from Dec 15-17"
**Parsing**:
- summary: "Company Retreat"
- start_date: "2026-12-15"
- duration_hours: 72.0 (3 days)

## Timezone Handling Patterns

### Local to UTC Conversion
```python
from datetime import datetime
import zoneinfo

local_time = datetime(2026, 1, 20, 14, 0, 0, tzinfo=zoneinfo.ZoneInfo("America/New_York"))
utc_time = local_time.astimezone(zoneinfo.ZoneInfo("UTC"))
```

### Multi-timezone Events
```python
# Meeting at 2pm EST for participants in different zones
start_time_est = datetime(2026, 1, 20, 14, 0, 0, tzinfo=zoneinfo.ZoneInfo("America/New_York"))
# Automatically converts when imported to other calendars
```

## Validation Patterns

### Date Validation
```python
def validate_date_range(start: datetime, end: datetime) -> bool:
    """Ensure end is after start"""
    return end > start
```

### Business Hours Check
```python
def is_business_hours(dt: datetime) -> bool:
    """Check if time is within business hours (9am-5pm M-F)"""
    return (dt.weekday() < 5 and 9 <= dt.hour < 17)
```

### Conflict Detection
```python
def has_conflict(new_event, existing_events) -> bool:
    """Check if new event overlaps with existing events"""
    for event in existing_events:
        if events_overlap(new_event, event):
            return True
    return False
```

## Error Recovery Patterns

### Ambiguous Date
**Input**: "Schedule meeting next Friday"
**If multiple Fridays possible**:
- Clarify: "Did you mean January 24 or January 31?"
- Default: Use nearest Friday

### Missing Information
**Input**: "Schedule a meeting tomorrow"
**Missing**: time, duration
**Strategy**: Use intelligent defaults
- time: 14:00 (afternoon default)
- duration: 1.0 hour

### Invalid Time
**Input**: "Meeting at 25:00"
**Strategy**: Assume typo, suggest correction
- "Did you mean 15:00 (3pm) or 01:00 (1am)?"

## Performance Optimization

### Batch Event Creation
```python
events = []
for event_data in event_list:
    events.append(create_event(event_data))

# Write all at once
save_events_batch(events)
```

### Caching Timezone Data
```python
# Cache timezone objects to avoid repeated lookups
timezone_cache = {}

def get_timezone(tz_name: str):
    if tz_name not in timezone_cache:
        timezone_cache[tz_name] = zoneinfo.ZoneInfo(tz_name)
    return timezone_cache[tz_name]
```

## Integration Patterns

### Google Calendar
- Import via web interface or API
- Supports all standard iCalendar features
- Timezone handling is automatic

### Outlook/Office 365
- Import .ics files directly
- Exchange server sync
- Attendee responses tracked

### Apple Calendar
- Native .ics support
- iCloud sync
- Reminders app integration

### Mobile Apps
- iOS Calendar: Direct .ics opening
- Android Calendar: Via file manager or email
- Cross-platform: Import from cloud storage

