"""
NVIDIA Idea Generation Skill Package
Agent Skills API Compliant Implementation
"""

from .ideagen_skill import (
    NvidiaIdeaGenSkill,
    discover_skills,
    generate_skills_xml,
    generate_ideas_quick
)

__version__ = "1.0.0"
__all__ = [
    "NvidiaIdeaGenSkill",
    "discover_skills",
    "generate_skills_xml",
    "generate_ideas_quick"
]

