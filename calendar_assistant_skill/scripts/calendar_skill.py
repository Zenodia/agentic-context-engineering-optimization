"""
Calendar Assistant Agent Skill
Agent Skills API Compliant with NAT Integration

This is the implementation code that gets called after the agent
reads the SKILL.md instructions and decides to use this skill.

This module provides the CalendarAssistantSkill class for creating and managing
calendar events from natural language or structured inputs. Compliant with
Agent Skills Python API specification and NAT tool auto-discovery.
"""

import os
import sys
from datetime import datetime, timedelta
from icalendar import Calendar, Event, vCalAddress, vText, Alarm
from pathlib import Path
import zoneinfo
import json
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

# Import skill_tool decorator from skill_loader
# Handle import whether running as module or standalone
try:
    from skill_loader import skill_tool
except ImportError:
    # Fallback: Add parent directory to path
    parent_dir = Path(__file__).parent.parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    try:
        from skill_loader import skill_tool
    except ImportError:
        # If still can't import, define a dummy decorator
        def skill_tool(name=None, description=None, return_direct=False):
            def decorator(func):
                func._is_skill_tool = True
                func._tool_name = name or func.__name__
                func._tool_description = description or func.__doc__ or ""
                func._tool_return_direct = return_direct
                return func
            return decorator

try:
    from langchain_nvidia_ai_endpoints import ChatNVIDIA
    from langchain_core.messages import SystemMessage, HumanMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

try:
    import sys
    from pathlib import Path
    # Add parent directory to path to import self_hosted_nim_w_vllm_backend
    parent_dir = Path(__file__).parent.parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    from self_hosted_nim_w_vllm_backend import SelfHostedNIMLLM
    SELF_HOSTED_AVAILABLE = True
except ImportError:
    SELF_HOSTED_AVAILABLE = False

try:
    from colorama import Fore, Style
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    # Fallback for systems without colorama
    class Fore:
        YELLOW = ""
        RESET = ""
    class Style:
        RESET_ALL = ""


class CalendarAssistantSkill:
    """
    Calendar management skill for AI agents
    
    This implementation is activated when an agent:
    1. Discovers the skill via SKILL.md metadata in system prompt
    2. Reads the full SKILL.md instructions
    3. Decides the user needs calendar management
    4. Calls this implementation
    
    Attributes:
        api_key (Optional[str]): NVIDIA API key for AI parsing
        default_timezone (str): Default timezone for events (IANA format)
        llm: Language model for natural language processing
        version (str): Skill version
        name (str): Skill identifier
        skill_location (Path): Path to SKILL.md file for agent discovery
    """
    
    def __init__(self, api_key: Optional[str] = None, default_timezone: str = "UTC"):
        """
        Initialize the Calendar Assistant Skill
        
        Args:
            api_key: NVIDIA API key for AI parsing (optional, defaults to NVIDIA_API_KEY env var)
            default_timezone: Default timezone for events (default: UTC)
        
        Raises:
            ValueError: If default_timezone is not a valid IANA timezone
        """
        # Validate timezone
        try:
            zoneinfo.ZoneInfo(default_timezone)
        except zoneinfo.ZoneInfoNotFoundError:
            raise ValueError(f"Invalid timezone: {default_timezone}. Use IANA timezone names.")
        
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        self.default_timezone = default_timezone
        self.llm = None
        
        self.version = "1.0.0"
        self.name = "calendar-assistant"
        
        # Skill location for agent discovery
        self.skill_location = Path(__file__).parent.parent / "SKILL.md"
        
        # Initialize LLM if API key is available or self-hosted is enabled
        use_self_hosted = os.environ.get("USE_SELF_HOSTED_LLM", "false").lower() == "true"
        if (self.api_key and LANGCHAIN_AVAILABLE) or (use_self_hosted and SELF_HOSTED_AVAILABLE):
            self._initialize_llm()
        elif self.api_key and not LANGCHAIN_AVAILABLE and not (use_self_hosted and SELF_HOSTED_AVAILABLE):
            print("Warning: langchain packages not available. Install langchain-nvidia-ai-endpoints for AI parsing.")
    
    def _initialize_llm(self):
        """Initialize the LLM for natural language parsing (ChatNVIDIA or Self-Hosted)"""
        try:
            # Choose LLM based on environment variable or default to ChatNVIDIA
            use_self_hosted = os.environ.get("USE_SELF_HOSTED_LLM", "false").lower() == "true"
            
            if use_self_hosted and SELF_HOSTED_AVAILABLE:
                self.llm = SelfHostedNIMLLM(model="meta/llama-3.1-8b-instruct")
                print("✅ Calendar skill using Self-Hosted NIM LLM")
            elif LANGCHAIN_AVAILABLE and self.api_key:
                self.llm = ChatNVIDIA(
                    model="meta/llama-3.1-405b-instruct",
                    api_key=self.api_key,
                    temperature=0.3,
                    max_completion_tokens=36000
                )
                print("✅ Calendar skill using ChatNVIDIA")
            else:
                raise ValueError("Neither self-hosted LLM nor ChatNVIDIA available")
        except Exception as e:
            print(f"Warning: Could not initialize LLM: {e}")
            self.llm = None
    
    def parse_natural_language(
        self, 
        user_input: str, 
        reference_date: Optional[datetime] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Parse natural language input into structured event data
        
        Args:
            user_input: Natural language description of the event
            reference_date: Reference date for relative dates (default: now)
            
        Returns:
            Tuple of (event_data dict, error string)
            event_data contains: summary, description, start_date, start_time,
                                duration_hours, location, organizer_email, 
                                organizer_name, reminder_hours
        
        Example:
            >>> skill = CalendarAssistantSkill(api_key="your_key")
            >>> data, error = skill.parse_natural_language("Meeting tomorrow at 2pm")
            >>> if not error:
            ...     print(data['summary'])
        """
        if not self.llm:
            return None, "LLM not initialized. Please provide API key and ensure langchain packages are installed."
        
        if reference_date is None:
            reference_date = datetime.now(zoneinfo.ZoneInfo(self.default_timezone))
        
        try:
            current_date = reference_date.strftime("%Y-%m-%d")
            system_prompt = self._build_system_prompt(current_date)
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input)
            ]
            
            response = self.llm.invoke(messages)
            response_text = response.content.strip()
            
            # Extract JSON from potential markdown code blocks
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                response_text = response_text[start:end].strip()
            elif '```' in response_text:
                start = response_text.find('```') + 3
                end = response_text.find('```', start)
                response_text = response_text[start:end].strip()
            
            if COLORAMA_AVAILABLE:
                print(Fore.YELLOW + f"AI extracted calendar info: {response_text}" + Style.RESET_ALL)
            else:
                print(f"AI extracted calendar info: {response_text}")
            
            event_data = json.loads(response_text)
            
            # Validate required fields
            required_fields = ['summary', 'start_date', 'start_time']
            for field in required_fields:
                if field not in event_data:
                    return None, f"Missing required field: {field}"
            
            return event_data, None
            
        except json.JSONDecodeError as e:
            return None, f"Error parsing JSON response: {str(e)}"
        except Exception as e:
            return None, f"Error parsing with AI: {str(e)}"
    
    def create_calendar_event(
        self,
        summary: str,
        start_datetime: datetime,
        duration_hours: float = 1.0,
        description: str = "",
        location: str = "",
        organizer_email: str = "",
        organizer_name: str = "",
        attendees: Optional[List[Dict[str, str]]] = None,
        reminder_hours: float = 1.0,
        recurrence: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Create an iCalendar event (RFC 5545 compliant)
        
        Args:
            summary: Event title (required)
            start_datetime: Start date and time (timezone-aware recommended)
            duration_hours: Event duration in hours (default: 1.0)
            description: Event description
            location: Event location
            organizer_email: Organizer's email address
            organizer_name: Organizer's name
            attendees: List of attendee dicts with 'email', 'name', 'role'
            reminder_hours: Hours before event to trigger reminder (default: 1.0)
            recurrence: Recurrence rules (optional, for future use)
            
        Returns:
            bytes: ICS file content ready to save or send
        
        Raises:
            ValueError: If required parameters are invalid
        
        Example:
            >>> from datetime import datetime, timedelta
            >>> import zoneinfo
            >>> skill = CalendarAssistantSkill()
            >>> start = datetime.now(zoneinfo.ZoneInfo("UTC")) + timedelta(days=1)
            >>> ics = skill.create_calendar_event(
            ...     summary="Team Meeting",
            ...     start_datetime=start,
            ...     duration_hours=2.0
            ... )
            >>> with open("event.ics", "wb") as f:
            ...     f.write(ics)
        """
        if not summary:
            raise ValueError("Event summary is required")
        
        if not isinstance(start_datetime, datetime):
            raise ValueError("start_datetime must be a datetime object")
        
        cal = Calendar()
        cal.add('prodid', '-//Calendar Assistant Agent Skill//EN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        
        event = Event()
        event.add('summary', summary)
        
        # Ensure datetime has timezone
        if start_datetime.tzinfo is None:
            start_datetime = start_datetime.replace(
                tzinfo=zoneinfo.ZoneInfo(self.default_timezone)
            )
        
        event.add('dtstart', start_datetime)
        
        # Calculate end time
        end_datetime = start_datetime + timedelta(hours=duration_hours)
        event.add('dtend', end_datetime)
        
        # Add timestamp (current time in UTC)
        event.add('dtstamp', datetime.now(zoneinfo.ZoneInfo("UTC")))
        
        # Generate unique UID
        uid_base = f"{summary}{start_datetime.isoformat()}"
        uid_hash = hashlib.md5(uid_base.encode()).hexdigest()
        event['uid'] = f"{uid_hash}@calendar-assistant-skill"
        
        if location:
            event.add('location', location)
        
        if description:
            event.add('description', description)
        
        # Add organizer
        if organizer_email:
            organizer = vCalAddress(f'mailto:{organizer_email}')
            if organizer_name:
                organizer.params['CN'] = organizer_name
            event['organizer'] = organizer
        
        # Add attendees
        if attendees:
            for attendee in attendees:
                if 'email' not in attendee:
                    continue
                attendee_addr = vCalAddress(f'mailto:{attendee["email"]}')
                attendee_addr.params['CN'] = attendee.get('name', attendee['email'])
                attendee_addr.params['ROLE'] = attendee.get('role', 'REQ-PARTICIPANT')
                event.add('attendee', attendee_addr, encode=0)
        
        # Add reminder alarm
        if reminder_hours > 0:
            alarm = Alarm()
            alarm.add('action', 'DISPLAY')
            alarm.add('trigger', timedelta(hours=-reminder_hours))
            alarm.add('description', f'Reminder: {summary}')
            event.add_component(alarm)
        
        # Add recurrence if specified
        if recurrence:
            event.add('rrule', recurrence)
        
        cal.add_component(event)
        
        return cal.to_ical()
    
    def create_event_from_data(self, event_data: Dict[str, Any]) -> bytes:
        """
        Create calendar event from parsed data dictionary
        
        Args:
            event_data: Dictionary with event fields from parse_natural_language()
                       Must contain: summary, start_date, start_time
                       Optional: duration_hours, description, location, etc.
            
        Returns:
            bytes: ICS file content
        
        Raises:
            KeyError: If required fields are missing
            ValueError: If date/time parsing fails
        
        Example:
            >>> data = {
            ...     "summary": "Meeting",
            ...     "start_date": "2026-01-13",
            ...     "start_time": "14:00",
            ...     "duration_hours": 1.0
            ... }
            >>> ics = skill.create_event_from_data(data)
        """
        # Parse datetime
        try:
            start_date = datetime.strptime(event_data['start_date'], '%Y-%m-%d')
        except (KeyError, ValueError) as e:
            raise ValueError(f"Invalid or missing start_date: {e}")
        
        if event_data.get('start_time'):
            try:
                hour, minute = map(int, event_data['start_time'].split(':'))
                start_date = start_date.replace(hour=hour, minute=minute)
            except ValueError as e:
                raise ValueError(f"Invalid start_time format: {e}")
        
        # Add timezone
        start_date = start_date.replace(tzinfo=zoneinfo.ZoneInfo(self.default_timezone))
        
        return self.create_calendar_event(
            summary=event_data['summary'],
            start_datetime=start_date,
            duration_hours=float(event_data.get('duration_hours', 1.0)),
            description=event_data.get('description', ''),
            location=event_data.get('location', ''),
            organizer_email=event_data.get('organizer_email', ''),
            organizer_name=event_data.get('organizer_name', ''),
            reminder_hours=float(event_data.get('reminder_hours', 1.0))
        )
    
    def natural_language_to_ics(
        self, 
        user_input: str
    ) -> Tuple[Optional[bytes], Optional[str], Optional[Dict[str, Any]]]:
        """
        Complete pipeline: natural language -> parsed data -> ICS file
        
        This is the main entry point for AI agents using natural language.
        
        Args:
            user_input: Natural language event description
            
        Returns:
            Tuple of (ics_content bytes, error string, parsed_data dict)
            - If successful: (bytes, None, dict)
            - If error: (None, error_message, None) or (None, error_message, partial_data)
        
        Example:
            >>> skill = CalendarAssistantSkill(api_key="your_key")
            >>> ics, error, data = skill.natural_language_to_ics(
            ...     "Schedule team meeting tomorrow at 2pm for 2 hours"
            ... )
            >>> if not error:
            ...     with open("meeting.ics", "wb") as f:
            ...         f.write(ics)
        """
        # Parse natural language
        event_data, error = self.parse_natural_language(user_input)
        
        if error:
            return None, error, None
        
        try:
            # Create ICS file
            ics_content = self.create_event_from_data(event_data)
            return ics_content, None, event_data
        except Exception as e:
            return None, f"Error creating ICS: {str(e)}", event_data
    
    def natural_language_to_ics_batch(
        self,
        user_inputs: List[str],
        use_parallel: bool = True,
        max_workers: Optional[int] = None
    ) -> List[Tuple[Optional[bytes], Optional[str], Optional[Dict[str, Any]]]]:
        """
        Process multiple natural language event descriptions in parallel
        
        This method is optimized for batch operations when creating many events.
        It uses ThreadPoolExecutor for I/O-bound API calls, which is faster than
        multiprocessing for network requests.
        
        Args:
            user_inputs: List of natural language event descriptions
            use_parallel: Whether to use parallel processing (default: True)
            max_workers: Maximum number of worker threads (default: min(4, len(user_inputs)))
        
        Returns:
            List of tuples: (ics_content bytes, error string, parsed_data dict)
            Each tuple follows the same format as natural_language_to_ics()
        
        Example:
            >>> skill = CalendarAssistantSkill(api_key="your_key")
            >>> results = skill.natural_language_to_ics_batch([
            ...     "Meeting tomorrow at 2pm",
            ...     "Lunch Friday at noon",
            ...     "Conference call Monday at 10am"
            ... ])
            >>> for ics, error, data in results:
            ...     if not error:
            ...         # Save each ICS file
            ...         pass
        """
        if not user_inputs:
            return []
        
        # For small batches, use single process
        if len(user_inputs) <= 2 or not use_parallel:
            results = []
            for user_input in user_inputs:
                result = self.natural_language_to_ics(user_input)
                results.append(result)
            return results
        
        # For larger batches, use ThreadPoolExecutor
        if max_workers is None:
            max_workers = min(4, len(user_inputs))  # Limit to avoid overwhelming the API
        
        # Process in parallel using ThreadPoolExecutor
        try:
            results = [None] * len(user_inputs)  # Pre-allocate to maintain order
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks with index tracking
                future_to_index = {
                    executor.submit(self.natural_language_to_ics, user_input): idx
                    for idx, user_input in enumerate(user_inputs)
                }
                
                # Collect results as they complete (maintains order by index)
                for future in as_completed(future_to_index):
                    idx = future_to_index[future]
                    try:
                        result = future.result()
                        results[idx] = result
                    except Exception as e:
                        # Handle individual task failures
                        results[idx] = (None, f"Task failed: {str(e)}", None)
            
            return results
            
        except Exception as e:
            # Fallback to single process on error
            results = []
            for user_input in user_inputs:
                result = self.natural_language_to_ics(user_input)
                results.append(result)
            return results
    
    def _build_system_prompt(self, current_date: str) -> str:
        """
        Build the system prompt with Agent Skills awareness
        
        According to https://agentskills.io/integrate-skills, agents should have
        skill metadata injected into their system prompt for skill discovery.
        
        Args:
            current_date: Current date string for reference
            
        Returns:
            System prompt with optional skill metadata injection
        """
        # Get available skills metadata
        available_skills_xml = self._get_available_skills_xml()
        
        base_prompt = f"""You are a calendar assistant. Parse user requests into structured event data.
Return ONLY a valid JSON object with these fields:
{{
    "summary": "Event title",
    "description": "Event description",
    "start_date": "YYYY-MM-DD",
    "start_time": "HH:MM",
    "duration_hours": float,
    "location": "Location (optional)",
    "organizer_email": "email@example.com (optional)",
    "organizer_name": "Name (optional)",
    "reminder_hours": 1
}}

Current date for reference: {current_date}
Timezone: {self.default_timezone}

Example input: "Schedule a team meeting tomorrow at 2pm for 2 hours about Q4 planning"
Example output: {{"summary": "Team Meeting - Q4 Planning", "start_date": "2026-01-13", "start_time": "14:00", "duration_hours": 2.0, "description": "Quarterly planning discussion", "reminder_hours": 1}}

IMPORTANT: Return ONLY the JSON object, no explanations."""
        
        # Inject available skills metadata if running in agent context
        if available_skills_xml:
            return f"""{base_prompt}

{available_skills_xml}"""
        
        return base_prompt
    
    def _get_available_skills_xml(self) -> str:
        """
        Generate the <available_skills> XML block for agent context injection
        
        This follows the Agent Skills specification:
        https://agentskills.io/integrate-skills#injecting-into-context
        
        Returns:
            XML string with skill metadata, or empty string if SKILL.md not found
        """
        if not self.skill_location.exists():
            return ""
        
        # Parse SKILL.md frontmatter
        try:
            with open(self.skill_location, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    try:
                        import yaml
                        frontmatter = yaml.safe_load(parts[1])
                        name = frontmatter.get('name', 'calendar-assistant')
                        description = frontmatter.get('description', 'Calendar management skill')
                        
                        return f"""<available_skills>
  <skill>
    <name>{name}</name>
    <description>{description}</description>
    <location>{self.skill_location.absolute()}</location>
  </skill>
</available_skills>"""
                    except:
                        pass
        except:
            pass
        
        # Fallback if parsing fails
        return f"""<available_skills>
  <skill>
    <name>calendar-assistant</name>
    <description>A comprehensive calendar management skill that enables AI agents to create, parse, and manage calendar events using natural language or structured inputs.</description>
    <location>{self.skill_location.absolute()}</location>
  </skill>
</available_skills>"""
    
    def get_skill_info(self) -> Dict[str, Any]:
        """
        Get information about this skill's capabilities and status
        
        Returns:
            Dict with skill metadata including:
            - name: Skill identifier
            - version: Skill version
            - capabilities: List of supported operations
            - status: Initialization status
            - llm_available: Whether AI parsing is available
            - default_timezone: Configured timezone
            - skill_location: Path to SKILL.md file
        
        Example:
            >>> skill = CalendarAssistantSkill()
            >>> info = skill.get_skill_info()
            >>> print(info['capabilities'])
        """
        return {
            "name": self.name,
            "version": self.version,
            "capabilities": [
                "parse_natural_language_to_event",
                "create_ics_calendar_event",
                "manage_event_reminders",
                "handle_multi_timezone_events",
                "export_calendar_files",
                "manage_attendees",
                "create_event_alarms"
            ],
            "status": "initialized",
            "api_available": self.api_key is not None,
            "llm_available": self.llm is not None,
            "langchain_available": LANGCHAIN_AVAILABLE,
            "default_timezone": self.default_timezone,
            "skill_location": str(self.skill_location.absolute()) if self.skill_location.exists() else "not found"
        }


# Skill discovery utility for agents
def discover_skills(skill_directories: List[str]) -> List[Dict[str, str]]:
    """
    Discover Agent Skills in specified directories
    
    According to https://agentskills.io/integrate-skills, agents should:
    1. Scan configured directories for SKILL.md files
    2. Parse only the frontmatter (name and description) at startup
    3. Keep initial context usage low (~50-100 tokens per skill)
    
    Args:
        skill_directories: List of directory paths to scan
    
    Returns:
        List of skill metadata dicts with name, description, and location
    """
    skills = []
    
    for directory in skill_directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            continue
        
        # Find all SKILL.md files
        for skill_md in dir_path.rglob("SKILL.md"):
            try:
                with open(skill_md, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract frontmatter
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        try:
                            import yaml
                            frontmatter = yaml.safe_load(parts[1])
                            
                            skills.append({
                                "name": frontmatter.get('name', 'unknown'),
                                "description": frontmatter.get('description', ''),
                                "location": str(skill_md.absolute()),
                                "path": str(skill_md.parent)
                            })
                        except:
                            pass
            except:
                continue
    
    return skills


def generate_skills_xml(skills: List[Dict[str, str]]) -> str:
    """
    Generate XML for injecting into agent system prompt
    
    Format according to https://agentskills.io/integrate-skills#injecting-into-context
    
    Args:
        skills: List of skill metadata from discover_skills()
    
    Returns:
        XML string formatted for system prompt injection
    """
    if not skills:
        return ""
    
    xml_parts = ["<available_skills>"]
    
    for skill in skills:
        xml_parts.append(f"""  <skill>
    <name>{skill['name']}</name>
    <description>{skill['description']}</description>
    <location>{skill['location']}</location>
  </skill>""")
    
    xml_parts.append("</available_skills>")
    
    return "\n".join(xml_parts)


# Convenience functions for skill discovery
def get_skill_metadata() -> Dict[str, Any]:
    """
    Get skill metadata without initialization
    
    Returns:
        Dict with basic skill information
    """
    return {
        "name": "calendar-assistant",
        "version": "1.0.0",
        "description": "Calendar management skill for creating events from natural language",
        "runtime": "python",
        "entry_point": "calendar_skill.py"
    }


def create_skill_instance(api_key: Optional[str] = None, **kwargs) -> CalendarAssistantSkill:
    """
    Factory function to create skill instance
    
    Args:
        api_key: NVIDIA API key (optional)
        **kwargs: Additional initialization parameters
    
    Returns:
        CalendarAssistantSkill instance
    """
    return CalendarAssistantSkill(api_key=api_key, **kwargs)


# ============================================================================
# Note: Removed multiprocessing worker function
# ThreadPoolExecutor uses instance methods directly, no need for static workers
# ============================================================================


# ============================================================================
# NAT Auto-Discovery Tool Functions
# These @skill_tool decorated functions are auto-discovered by the skill loader
# ============================================================================

# Global skill instance for tool functions
_global_skill_instance = None

def _get_skill_instance():
    """Get or create the global skill instance"""
    global _global_skill_instance
    if _global_skill_instance is None:
        api_key = os.getenv("NVIDIA_API_KEY")
        _global_skill_instance = CalendarAssistantSkill(api_key=api_key)
    return _global_skill_instance


@skill_tool(
    name="parse_calendar_event",
    description="Parse natural language into structured calendar event data. Returns event details as a dictionary.",
    return_direct=False
)
def parse_calendar_event(
    user_input: str,
    reference_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parse natural language calendar request into structured data
    
    Args:
        user_input: Natural language description (e.g., "meeting tomorrow at 2pm for 2 hours")
        reference_date: Optional reference date in YYYY-MM-DD format (defaults to today)
    
    Returns:
        Dictionary with parsed event data or error message
    
    Examples:
        >>> parse_calendar_event("team meeting tomorrow at 2pm")
        >>> parse_calendar_event("lunch appointment on Friday at noon", "2026-01-20")
    """
    skill = _get_skill_instance()
    
    # Parse reference date if provided
    ref_dt = None
    if reference_date:
        try:
            ref_dt = datetime.strptime(reference_date, '%Y-%m-%d')
            ref_dt = ref_dt.replace(tzinfo=zoneinfo.ZoneInfo(skill.default_timezone))
        except ValueError:
            return {"error": f"Invalid reference_date format: {reference_date}. Use YYYY-MM-DD"}
    
    event_data, error = skill.parse_natural_language(user_input, reference_date=ref_dt)
    
    if error:
        return {"error": error}
    
    return event_data


@skill_tool(
    name="create_ics_file",
    description="Create an iCalendar (ICS) file from event data. Returns file path or error.",
    return_direct=False
)
def create_ics_file(
    summary: str,
    start_date: str,
    start_time: str = "09:00",
    duration_hours: float = 1.0,
    description: str = "",
    location: str = "",
    reminder_hours: float = 1.0,
    output_filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create an ICS calendar file from structured event data
    
    Args:
        summary: Event title (required)
        start_date: Start date in YYYY-MM-DD format (required)
        start_time: Start time in HH:MM format (default: 09:00)
        duration_hours: Event duration in hours (default: 1.0)
        description: Event description (optional)
        location: Event location (optional)
        reminder_hours: Hours before event to remind (default: 1.0)
        output_filename: Custom filename for ICS file (optional)
    
    Returns:
        Dictionary with file path and success status
    
    Examples:
        >>> create_ics_file("Team Meeting", "2026-01-21", "14:00", 2.0)
        >>> create_ics_file("Lunch", "2026-01-22", "12:00", location="Downtown Cafe")
    """
    skill = _get_skill_instance()
    
    try:
        # Parse date and time
        event_date = datetime.strptime(start_date, '%Y-%m-%d')
        hour, minute = map(int, start_time.split(':'))
        event_date = event_date.replace(hour=hour, minute=minute)
        event_date = event_date.replace(tzinfo=zoneinfo.ZoneInfo(skill.default_timezone))
        
        # Create ICS content
        ics_content = skill.create_calendar_event(
            summary=summary,
            start_datetime=event_date,
            duration_hours=duration_hours,
            description=description,
            location=location,
            reminder_hours=reminder_hours
        )
        
        # Determine output filename
        if not output_filename:
            safe_summary = "".join(c for c in summary if c.isalnum() or c in (' ', '_')).strip()
            safe_summary = safe_summary.replace(' ', '_')[:50]
            output_filename = f"{safe_summary}_{start_date}.ics"
        
        # Ensure .ics extension
        if not output_filename.endswith('.ics'):
            output_filename += '.ics'
        
        # Save file
        output_path = Path(output_filename)
        output_path.write_bytes(ics_content)
        
        return {
            "success": True,
            "file_path": str(output_path.absolute()),
            "file_size": len(ics_content),
            "event_summary": summary,
            "start_datetime": f"{start_date} {start_time}"
        }
        
    except ValueError as e:
        return {"error": f"Invalid date/time format: {str(e)}"}
    except Exception as e:
        return {"error": f"Error creating ICS file: {str(e)}"}


@skill_tool(
    name="natural_language_to_calendar",
    description="Complete pipeline: parse natural language and create ICS file in one step. Most convenient for users. Supports batch processing with ThreadPoolExecutor for multiple events (optimized for I/O-bound API calls).",
    return_direct=False
)
def natural_language_to_calendar(
    user_input: str,
    output_filename: Optional[str] = None,
    batch_inputs: Optional[List[str]] = None,
    use_parallel: bool = True
) -> Dict[str, Any]:
    """
    Parse natural language and create ICS file in one step
    
    Supports both single event and batch processing. For batch processing,
    provide batch_inputs list and the function will process all events in parallel.
    
    Args:
        user_input: Natural language event description (used if batch_inputs is None)
        output_filename: Optional custom filename for ICS file (single event) or prefix (batch)
        batch_inputs: Optional list of event descriptions for batch processing
        use_parallel: Whether to use parallel processing for batches (default: True)
    
    Returns:
        Dictionary with file path(s), event details, and success status
    
    Examples:
        >>> natural_language_to_calendar("Schedule team meeting tomorrow at 2pm for 2 hours")
        >>> natural_language_to_calendar("Dentist appointment Friday at 10:30am", "dentist.ics")
        >>> natural_language_to_calendar("", batch_inputs=["Meeting at 2pm", "Lunch at noon"])
    """
    skill = _get_skill_instance()
    
    # Check if batch processing is requested
    if batch_inputs and len(batch_inputs) > 1:
        # Batch processing mode
        results = skill.natural_language_to_ics_batch(
            batch_inputs,
            use_parallel=use_parallel
        )
        
        # Process all results
        saved_files = []
        errors = []
        
        for i, (ics_content, error, parsed_data) in enumerate(results):
            if error:
                errors.append(f"Event {i+1}: {error}")
                continue
            
            try:
                # Determine output filename for this event
                if output_filename:
                    # Use prefix with index
                    event_filename = f"{output_filename}_{i+1}.ics"
                elif parsed_data:
                    summary = parsed_data.get('summary', 'event')
                    safe_summary = "".join(c for c in summary if c.isalnum() or c in (' ', '_')).strip()
                    safe_summary = safe_summary.replace(' ', '_')[:50]
                    start_date = parsed_data.get('start_date', 'unknown')
                    event_filename = f"{safe_summary}_{start_date}_{i+1}.ics"
                else:
                    event_filename = f"event_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i+1}.ics"
                
                # Ensure .ics extension
                if not event_filename.endswith('.ics'):
                    event_filename += '.ics'
                
                # Save file
                output_path = Path(event_filename)
                output_path.write_bytes(ics_content)
                
                saved_files.append({
                    "file_path": str(output_path.absolute()),
                    "file_size": len(ics_content),
                    "parsed_data": parsed_data,
                    "index": i + 1
                })
            
            except Exception as e:
                errors.append(f"Event {i+1}: Error saving file: {str(e)}")
        
        return {
            "success": len(saved_files) > 0,
            "batch_processed": True,
            "total_events": len(batch_inputs),
            "saved_count": len(saved_files),
            "files": saved_files,
            "errors": errors if errors else None,
            "message": f"✅ Processed {len(saved_files)}/{len(batch_inputs)} calendar events",
            "execution_method": "ThreadPoolExecutor" if use_parallel else "sequential"
        }
    
    else:
        # Single event mode (original behavior)
        # Parse natural language
        ics_content, error, parsed_data = skill.natural_language_to_ics(user_input)
        
        if error:
            return {"error": error}
        
        try:
            # Determine output filename
            if not output_filename and parsed_data:
                summary = parsed_data.get('summary', 'event')
                safe_summary = "".join(c for c in summary if c.isalnum() or c in (' ', '_')).strip()
                safe_summary = safe_summary.replace(' ', '_')[:50]
                start_date = parsed_data.get('start_date', 'unknown')
                output_filename = f"{safe_summary}_{start_date}.ics"
            elif not output_filename:
                output_filename = f"event_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
            
            # Ensure .ics extension
            if not output_filename.endswith('.ics'):
                output_filename += '.ics'
            
            # Save file
            output_path = Path(output_filename)
            output_path.write_bytes(ics_content)
            
            return {
                "success": True,
                "file_path": str(output_path.absolute()),
                "file_size": len(ics_content),
                "parsed_data": parsed_data,
                "message": f"✅ Calendar event created: {output_path.name}"
            }
            
        except Exception as e:
            return {"error": f"Error saving ICS file: {str(e)}"}


@skill_tool(
    name="get_calendar_skill_info",
    description="Get information about the calendar skill capabilities and status",
    return_direct=False
)
def get_calendar_skill_info() -> Dict[str, Any]:
    """
    Get metadata about the calendar assistant skill
    
    Returns:
        Dictionary with skill information including capabilities, status, and configuration
    """
    skill = _get_skill_instance()
    return skill.get_skill_info()


# Example usage function for testing
def example_usage():
    """Example of how to use the Calendar Assistant Skill"""
    
    print("\n" + "="*60)
    print("Calendar Assistant Skill - Agent Skills API Compliant")
    print("="*60 + "\n")
    
    # Demonstrate skill discovery
    print("🔍 Discovering skills...")
    current_dir = Path(__file__).parent.parent
    skills = discover_skills([str(current_dir)])
    
    if skills:
        print(f"✅ Found {len(skills)} skill(s):\n")
        for skill in skills:
            print(f"  - {skill['name']}: {skill['description'][:80]}...")
            print(f"    Location: {skill['location']}\n")
        
        print("📝 Generated XML for agent prompt:")
        print(generate_skills_xml(skills))
        print()
    
    print("="*60 + "\n")
    
    # Check for API key
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        print("⚠️  Note: NVIDIA_API_KEY environment variable not set")
        print("   Natural language parsing will be unavailable\n")
    
    # Initialize skill
    try:
        skill = CalendarAssistantSkill(api_key=api_key, default_timezone="UTC")
        print("✅ Skill initialized successfully\n")
        
        # Show skill info
        info = skill.get_skill_info()
        print("📊 Skill Information:")
        print(json.dumps(info, indent=2))
        print("\n" + "="*60 + "\n")
        
        # Example 1: Create event manually
        print("🧪 Testing manual event creation...")
        start_time = datetime.now(zoneinfo.ZoneInfo("UTC")) + timedelta(days=1, hours=14)
        ics_content = skill.create_calendar_event(
            summary="Team Standup Meeting",
            start_datetime=start_time,
            duration_hours=0.5,
            description="Daily team synchronization",
            location="Conference Room A",
            reminder_hours=1.0
        )
        print(f"✅ Created ICS file ({len(ics_content)} bytes)")
        print("   Event: Team Standup Meeting")
        print(f"   Start: {start_time.strftime('%Y-%m-%d %H:%M %Z')}")
        print(f"   Duration: 30 minutes\n")
        
        # Example 2: Natural language parsing
        if api_key:
            print("🧪 Testing natural language parsing...")
            ics_content, error, parsed_data = skill.natural_language_to_ics(
                "Schedule a client presentation tomorrow at 2pm for 2 hours"
            )
            if error:
                print(f"❌ Error: {error}")
            else:
                print("✅ Successfully parsed and created event:")
                print(f"   {json.dumps(parsed_data, indent=3)}")
                print(f"✅ Created ICS file ({len(ics_content)} bytes)\n")
        else:
            print("⚠️  Skipping natural language test (no API key)")
            print("   Set NVIDIA_API_KEY to test this feature\n")
        
        print("="*60 + "\n")
        print("✅ All tests completed successfully!")
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        exit(1)




# Main execution - supports both CLI JSON mode and example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Calendar Assistant Skill')
    parser.add_argument('--json', action='store_true', 
                       help='JSON mode for subprocess execution')
    parser.add_argument('--example', action='store_true',
                       help='Run example usage')
    
    args = parser.parse_args()
    
    if args.json:
        # JSON CLI mode for subprocess execution (ThreadPoolExecutor-compatible)
        try:
            # Read JSON input from stdin
            input_data = json.loads(sys.stdin.read())
            command = input_data.get('command', '')
            parameters = input_data.get('parameters', {})
            
            # Initialize skill
            api_key = parameters.get('api_key') or os.getenv('NVIDIA_API_KEY')
            skill = CalendarAssistantSkill(api_key=api_key)
            
            # Execute command - support all @skill_tool functions
            output = None
            
            if command == 'natural_language_to_ics':
                # Legacy command name (preserved for backward compatibility)
                query = parameters.get('query', '')
                batch_queries = parameters.get('batch_queries')
                # Backward compatibility: support both old and new parameter names
                use_parallel = parameters.get('use_parallel', 
                                             parameters.get('use_multiprocessing', True))
                
                # Check if batch processing is requested
                if batch_queries and len(batch_queries) > 1:
                    # Batch processing mode
                    results = skill.natural_language_to_ics_batch(
                        batch_queries,
                        use_parallel=use_parallel
                    )
                    
                    # Format results
                    ics_contents = []
                    parsed_data_list = []
                    errors = []
                    
                    for i, (ics_content, error, parsed_data) in enumerate(results):
                        if error:
                            errors.append(f"Event {i+1}: {error}")
                        else:
                            ics_contents.append(ics_content.decode('utf-8') if ics_content else '')
                            parsed_data_list.append(parsed_data)
                    
                    output = {
                        'success': len(ics_contents) > 0,
                        'batch_processed': True,
                        'total_events': len(batch_queries),
                        'successful_count': len(ics_contents),
                        'ics_contents': ics_contents,
                        'parsed_data_list': parsed_data_list,
                        'errors': errors if errors else None
                    }
                else:
                    # Single event mode (original behavior)
                    ics_content, error, parsed_data = skill.natural_language_to_ics(query)
                    
                    if error:
                        output = {
                            'success': False,
                            'error': error
                        }
                    else:
                        output = {
                            'success': True,
                            'ics_content': ics_content.decode('utf-8'),
                            'parsed_data': parsed_data,
                            'output_size': len(ics_content)
                        }
            
            elif command == 'natural_language_to_calendar':
                # New command name matching @skill_tool function
                user_input = parameters.get('user_input', '')
                output_filename = parameters.get('output_filename')
                batch_inputs = parameters.get('batch_inputs')
                # Backward compatibility: support both old and new parameter names
                use_parallel = parameters.get('use_parallel', 
                                             parameters.get('use_multiprocessing', True))
                result = natural_language_to_calendar(
                    user_input, output_filename, batch_inputs, use_parallel
                )
                output = {
                    'success': 'error' not in result,
                    **result
                }
            
            elif command == 'parse_calendar_event':
                user_input = parameters.get('user_input', '')
                reference_date = parameters.get('reference_date')
                result = parse_calendar_event(user_input, reference_date)
                output = {
                    'success': 'error' not in result,
                    **result
                }
            
            elif command == 'create_ics_file':
                summary = parameters.get('summary', '')
                start_date = parameters.get('start_date', '')
                start_time = parameters.get('start_time', '09:00')
                duration_hours = parameters.get('duration_hours', 1.0)
                description = parameters.get('description', '')
                location = parameters.get('location', '')
                reminder_hours = parameters.get('reminder_hours', 1.0)
                output_filename = parameters.get('output_filename')
                
                result = create_ics_file(
                    summary, start_date, start_time, duration_hours,
                    description, location, reminder_hours, output_filename
                )
                output = {
                    'success': 'error' not in result,
                    **result
                }
            
            elif command == 'create_event':
                # Legacy command name (preserved for backward compatibility)
                summary = parameters.get('summary', 'Event')
                start_date = parameters.get('start_date')
                start_time = parameters.get('start_time')
                duration_hours = parameters.get('duration_hours', 1.0)
                
                # Parse datetime
                if start_date and start_time:
                    start_dt = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
                else:
                    start_dt = datetime.now() + timedelta(days=1)
                
                ics_content = skill.create_calendar_event(
                    summary=summary,
                    start_datetime=start_dt,
                    duration_hours=duration_hours,
                    description=parameters.get('description', ''),
                    location=parameters.get('location', ''),
                    reminder_hours=parameters.get('reminder_hours', 1.0)
                )
                
                output = {
                    'success': True,
                    'ics_content': ics_content.decode('utf-8'),
                    'output_size': len(ics_content)
                }
            
            elif command == 'get_calendar_skill_info':
                result = get_calendar_skill_info()
                output = {
                    'success': True,
                    **result
                }
            
            else:
                output = {
                    'success': False,
                    'error': f"Unknown command: {command}. Available commands: natural_language_to_ics, natural_language_to_calendar, parse_calendar_event, create_ics_file, create_event, get_calendar_skill_info"
                }
            
            # Output JSON result (required for subprocess communication)
            print(json.dumps(output))
            
            # Exit with error code if failed
            if not output.get('success', False):
                sys.exit(1)
        
        except Exception as e:
            output = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
            print(json.dumps(output))
            sys.exit(1)
    
    else:
        # Default: Run example usage
        example_usage()

