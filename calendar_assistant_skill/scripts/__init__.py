"""
Calendar Assistant Agent Skill - Scripts Package

This package contains the implementation of the calendar assistant skill
conforming to the Agent Skills Python API specification.
"""

from .calendar_skill import (
    CalendarAssistantSkill,
    get_skill_metadata,
    create_skill_instance
)

__all__ = [
    'CalendarAssistantSkill',
    'get_skill_metadata',
    'create_skill_instance'
]

__version__ = '1.0.0'
__author__ = 'Zenodia'

