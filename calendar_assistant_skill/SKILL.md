---
name: calendar-assistant
version: 1.0.0
description: A comprehensive calendar management skill that enables AI agents to create, parse, and manage calendar events using natural language or structured inputs. Supports iCalendar (ICS) format for universal compatibility.
author: Zenodia
license: MIT
tags:
  - calendar
  - scheduling
  - ics
  - events
  - time-management
  - productivity
runtime:
  type: python
  version: ">=3.8"
dependencies:
  - icalendar>=5.0.0
  - python-dateutil>=2.8.0
  - PyYAML>=6.0
  - langchain-nvidia-ai-endpoints>=0.1.0
  - langchain-core>=0.1.0
  - colorama>=0.4.0
permissions:
  - file:write
  - network:api
environment:
  NVIDIA_API_KEY:
    description: NVIDIA API key for natural language parsing (optional)
    required: false
  DEFAULT_TIMEZONE:
    description: Default timezone for event creation
    required: false
    default: UTC
---

# Calendar Assistant Skill

A powerful calendar management skill that transforms natural language requests into structured calendar events. This skill enables AI agents to understand conversational scheduling requests and generate RFC 5545 compliant iCalendar (ICS) files that can be imported into any calendar application.

## When to Use This Skill

Use this skill whenever users need to:
- Schedule a meeting, appointment, or event
- Create a calendar entry from natural language
- Set up reminders or alarms for events
- Add events with specific dates, times, and durations
- Manage event attendees and organizers
- Handle multi-timezone events

**Trigger phrases:** "schedule", "add to calendar", "create event", "book appointment", "set reminder", "plan meeting"

## Core Capabilities

### 1. Natural Language Parsing
Converts conversational requests into structured event data using AI:
- Parse relative dates: "tomorrow", "next Monday", "in 3 days"
- Parse time expressions: "at 2pm", "3:30", "noon"
- Extract duration: "for 2 hours", "90 minutes"
- Identify locations, descriptions, and organizers
- Handle contextual date/time interpretation

### 2. Calendar Event Creation
Generate RFC 5545 compliant iCalendar (ICS) files:
- Support for titles, descriptions, locations
- Organizer and attendee management
- Configurable reminders and alarms
- Unique event IDs for tracking
- Multi-timezone support

### 3. Timezone Management
Robust timezone handling:
- Convert between multiple timezones
- UTC-based internal representation
- Configurable default timezone
- Timezone-aware datetime objects

## Usage Instructions

### For AI Agents

When a user mentions scheduling or calendar-related tasks, follow this workflow:

#### Method 1: Natural Language Input (Recommended)

```python
from scripts.calendar_skill import CalendarAssistantSkill

# Initialize the skill
skill = CalendarAssistantSkill()

# Process natural language input
user_input = "Schedule a team meeting tomorrow at 2pm for 2 hours"
ics_content, error, parsed_data = skill.natural_language_to_ics(user_input)

if error:
    # Ask user for clarification
    print(f"Error: {error}")
else:
    # Save ICS file and notify user
    with open("event.ics", "wb") as f:
        f.write(ics_content)
    print(f"✅ Event created: {parsed_data['summary']}")
```

#### Method 2: Structured Input (Precise Control)
```python
from datetime import datetime
import zoneinfo

# Create event with explicit parameters
start_time = datetime.now(zoneinfo.ZoneInfo("UTC")) + timedelta(days=1, hours=14)
ics_content = skill.create_calendar_event(
    summary="Team Meeting",
    start_datetime=start_time,
    duration_hours=2.0,
    description="Quarterly planning discussion",
    location="Conference Room A",
    reminder_hours=1.0
)

with open("event.ics", "wb") as f:
    f.write(ics_content)
```

## Example Interactions

### Example 1: Simple Meeting
**User:** "Schedule a team meeting tomorrow at 2pm for 2 hours"

**Agent Action:**
1. Invoke `natural_language_to_ics()` with user input
2. Skill parses: date=tomorrow, time=14:00, duration=2h
3. Creates ICS file with appropriate details
4. Returns downloadable ICS file

**Output:** `team_meeting.ics` ready for import

### Example 2: Appointment with Location
**User:** "Add a dentist appointment on December 5th at 10:30am at Downtown Dental"

**Agent Action:**
1. Parse: date=2026-12-05, time=10:30, location="Downtown Dental"
2. Set default 1-hour duration
3. Add 1-hour reminder
4. Generate ICS file

**Output:** Event with location and reminder

### Example 3: Deadline/Reminder
**User:** "Create a project deadline for next Friday at 5pm"

**Agent Action:**
1. Calculate next Friday's date
2. Set time to 17:00
3. Create event with appropriate reminder
4. Generate ICS file

**Output:** Deadline event in calendar

## Best Practices for Agents

### 1. Always Confirm Event Details
Before creating an event, summarize the parsed information:
```
"I'll create a calendar event for:
- Title: Team Meeting - Q4 Planning
- Date: Tomorrow, January 13, 2026
- Time: 2:00 PM - 4:00 PM (2 hours)
- Timezone: UTC
- Reminder: 1 hour before

Should I proceed?"
```

### 2. Handle Errors Gracefully
If parsing fails:
- Ask for clarification on ambiguous dates/times
- Suggest alternative phrasings
- Offer to create event manually with guided input

### 3. Mention Timezone When Relevant
Always inform users about the timezone being used:
```
"I've created the event in UTC timezone. The ICS file will automatically convert to your local timezone when imported."
```

### 4. Provide Import Instructions
After creating an ICS file:
```
"✅ Calendar event created! You can:
1. Download the .ics file
2. Double-click to open in your default calendar app
3. Or import it manually into Google Calendar, Outlook, Apple Calendar, etc."
```

### 5. Suggest Reminder Times
Based on event importance:
- Regular meetings: 1 hour before
- Important deadlines: 1 day before
- Appointments: 30 minutes before

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "LLM not initialized" | Missing API key | Fall back to manual entry or ask user to provide structured input |
| "Error parsing date" | Ambiguous date phrase | Ask user to specify exact date (YYYY-MM-DD) |
| "Invalid timezone" | Unknown timezone name | Use UTC or ask user for valid IANA timezone |
| "Missing required field" | Incomplete event data | Prompt user for missing information |

### Fallback Strategy
If natural language parsing fails:
1. Switch to guided manual entry
2. Ask for each field individually:
   - Event title?
   - Date (YYYY-MM-DD)?
   - Start time (HH:MM)?
   - Duration (in hours)?
   - Location (optional)?

## Technical Details

### Output Format
All events are generated as RFC 5545 compliant iCalendar files (.ics):
- Universal format supported by all major calendar applications
- Includes VEVENT component with all properties
- Unique UID for event identification
- VTIMEZONE information for accurate timezone handling

### Dependencies
- **icalendar**: ICS file generation
- **python-dateutil**: Advanced date parsing
- **langchain-nvidia-ai-endpoints**: AI-powered natural language understanding
- **zoneinfo**: Timezone management (Python 3.9+)

### API Key Requirements
- NVIDIA API key required for natural language parsing
- Can operate without API key using structured input only
- Key should be provided via environment variable `NVIDIA_API_KEY`

### Timezone Support
- Uses IANA timezone database
- Common timezones: UTC, America/New_York, Europe/Paris, Asia/Tokyo
- Automatic daylight saving time handling

## Integration Patterns

### Web Applications (Gradio, Streamlit, Flask)
```python
import gradio as gr
from scripts.calendar_skill import CalendarAssistantSkill

skill = CalendarAssistantSkill(api_key=api_key)

def create_event_handler(user_input):
    ics_content, error, parsed_data = skill.natural_language_to_ics(user_input)
    if error:
        return f"Error: {error}", None
    return f"Event created: {parsed_data['summary']}", ics_content

interface = gr.Interface(
    fn=create_event_handler,
    inputs="text",
    outputs=["text", gr.File(label="Download ICS")]
)
```

### Command-Line Tools
```python
#!/usr/bin/env python3
import sys
from scripts.calendar_skill import CalendarAssistantSkill

skill = CalendarAssistantSkill(api_key=os.environ.get('NVIDIA_API_KEY'))
ics_content, error, _ = skill.natural_language_to_ics(sys.argv[1])

if not error:
    with open("event.ics", "wb") as f:
        f.write(ics_content)
    print("✅ Event created: event.ics")
else:
    print(f"❌ Error: {error}")
    sys.exit(1)
```

### Jupyter Notebooks
```python
from scripts.calendar_skill import CalendarAssistantSkill
from IPython.display import FileLink

skill = CalendarAssistantSkill(default_timezone="America/New_York")
user_input = input("Describe your event: ")
ics_content, error, parsed_data = skill.natural_language_to_ics(user_input)

if not error:
    with open("notebook_event.ics", "wb") as f:
        f.write(ics_content)
    display(parsed_data)
    display(FileLink("notebook_event.ics"))
```

## Configuration Options

### Initialization Parameters
```python
skill = CalendarAssistantSkill(
    api_key="your_nvidia_api_key",      # Optional for AI parsing
    default_timezone="America/New_York"  # Default: UTC
)
```

### Event Creation Options
- **summary**: Event title (required)
- **start_datetime**: Start date/time (required, timezone-aware)
- **duration_hours**: Event duration (default: 1.0)
- **description**: Event description (optional)
- **location**: Event location (optional)
- **organizer_email**: Organizer's email (optional)
- **organizer_name**: Organizer's name (optional)
- **attendees**: List of attendee dicts (optional)
- **reminder_hours**: Reminder time before event (default: 1.0)
- **recurrence**: Recurrence rules (optional, future feature)

## Advanced Features

### Attendee Management
```python
attendees = [
    {"email": "john@example.com", "name": "John Doe", "role": "REQ-PARTICIPANT"},
    {"email": "jane@example.com", "name": "Jane Smith", "role": "OPT-PARTICIPANT"}
]

ics_content = skill.create_calendar_event(
    summary="Team Meeting",
    start_datetime=start_time,
    attendees=attendees,
    organizer_email="organizer@example.com",
    organizer_name="Meeting Organizer"
)
```

### Multiple Reminders
Create events with custom reminder times:
```python
# 1-hour reminder for regular meetings
reminder_hours=1.0

# 24-hour reminder for important deadlines
reminder_hours=24.0

# 30-minute reminder for appointments
reminder_hours=0.5
```

## Troubleshooting

### Issue: Natural language parsing not working
**Solution:** Check that NVIDIA_API_KEY environment variable is set

### Issue: Timezone not recognized
**Solution:** Use IANA timezone names (e.g., "America/New_York" not "EST")

### Issue: Event not importing to calendar
**Solution:** Ensure .ics file is saved with UTF-8 encoding

### Issue: Times showing incorrectly
**Solution:** Verify timezone is correctly set and datetime objects are timezone-aware

## Skill Information

Get skill metadata and status:
```python
info = skill.get_skill_info()
print(info)
# {
#   "name": "calendar_assistant",
#   "version": "1.0.0",
#   "capabilities": [...],
#   "status": "initialized",
#   "llm_available": true,
#   "default_timezone": "UTC"
# }
```

## Future Enhancements

Planned features for future versions:
- Recurring event support (daily, weekly, monthly)
- Event conflict detection
- Calendar file merging
- Video conferencing link integration
- Multi-language support
- Local LLM support for offline operation

---

**Note:** This skill requires Python 3.8+ and can operate in two modes:
1. **AI-powered mode** (with NVIDIA API key): Full natural language understanding
2. **Manual mode** (without API key): Structured input only

Always provide clear feedback to users and handle errors gracefully for the best user experience.

