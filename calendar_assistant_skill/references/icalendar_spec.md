# iCalendar (RFC 5545) Reference

This document provides key information about the iCalendar format for the Calendar Assistant Skill.

## Format Overview

iCalendar is an internet standard (RFC 5545) for exchanging calendar and scheduling information between users and computers. Files use the `.ics` extension.

## Core Components

### VCALENDAR

The root component that contains all calendar data.

```
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Calendar Assistant//EN
...
END:VCALENDAR
```

### VEVENT

Represents a calendar event within VCALENDAR.

```
BEGIN:VEVENT
UID:unique-identifier@domain
DTSTART:20260120T140000Z
DTEND:20260120T160000Z
SUMMARY:Team Meeting
DESCRIPTION:Quarterly planning discussion
LOCATION:Conference Room A
ORGANIZER:mailto:organizer@example.com
ATTENDEE:mailto:participant@example.com
BEGIN:VALARM
ACTION:DISPLAY
TRIGGER:-PT1H
DESCRIPTION:Reminder: Team Meeting
END:VALARM
END:VEVENT
```

## Key Properties

### Required Properties

- **UID**: Unique identifier for the event
- **DTSTAMP**: Creation timestamp
- **DTSTART**: Event start date/time

### Optional Properties

- **DTEND**: Event end date/time
- **DURATION**: Event duration (alternative to DTEND)
- **SUMMARY**: Event title
- **DESCRIPTION**: Detailed description
- **LOCATION**: Event location
- **ORGANIZER**: Event organizer
- **ATTENDEE**: Event participants
- **STATUS**: Event status (TENTATIVE, CONFIRMED, CANCELLED)
- **PRIORITY**: Priority level (0-9)
- **CLASS**: Access classification (PUBLIC, PRIVATE, CONFIDENTIAL)

## Date/Time Formats

### UTC Format
```
DTSTART:20260120T140000Z
```
The 'Z' suffix indicates UTC timezone.

### Timezone-Aware Format
```
DTSTART;TZID=America/New_York:20260120T090000
```

### All-Day Event
```
DTSTART;VALUE=DATE:20260120
```

## Alarms (VALARM)

Reminders can be added to events:

```
BEGIN:VALARM
ACTION:DISPLAY
TRIGGER:-PT1H          # 1 hour before
DESCRIPTION:Reminder text
END:VALARM
```

Trigger formats:
- `-PT15M`: 15 minutes before
- `-PT1H`: 1 hour before
- `-P1D`: 1 day before
- `-PT0M`: At event time

## Attendees

```
ATTENDEE;CN="John Doe";ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=TRUE:mailto:john@example.com
```

Parameters:
- **CN**: Common name (display name)
- **ROLE**: REQ-PARTICIPANT, OPT-PARTICIPANT, NON-PARTICIPANT, CHAIR
- **PARTSTAT**: NEEDS-ACTION, ACCEPTED, DECLINED, TENTATIVE, DELEGATED
- **RSVP**: TRUE or FALSE

## Recurrence Rules (RRULE)

For repeating events:

```
RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=10
```

Common patterns:
- Daily: `FREQ=DAILY`
- Weekly: `FREQ=WEEKLY;BYDAY=MO,WE,FR`
- Monthly: `FREQ=MONTHLY;BYMONTHDAY=15`
- Yearly: `FREQ=YEARLY;BYMONTH=12;BYMONTHDAY=25`

## Best Practices

1. **Always include UID**: Use domain-based unique identifiers
2. **Use DTSTAMP**: Set to current UTC time when creating
3. **Specify timezones**: Use TZID for non-UTC times
4. **Validate dates**: Ensure start comes before end
5. **Proper escaping**: Escape special characters in text fields
6. **Line folding**: Lines should be max 75 octets (managed by library)

## Common IANA Timezones

- **US Eastern**: America/New_York
- **US Pacific**: America/Los_Angeles
- **UK**: Europe/London
- **Central Europe**: Europe/Paris
- **Japan**: Asia/Tokyo
- **Australia**: Australia/Sydney
- **UTC**: UTC or Etc/UTC

## Error Handling

Common issues:
- Missing required fields (UID, DTSTAMP, DTSTART)
- Invalid date/time formats
- Timezone not found
- Malformed RRULE
- Invalid property values

## Resources

- RFC 5545: https://tools.ietf.org/html/rfc5545
- iCalendar Validator: https://icalendar.org/validator.html
- Python icalendar library: https://pypi.org/project/icalendar/

