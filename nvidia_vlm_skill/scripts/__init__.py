"""
NVIDIA VLM Skill Package
Vision Language Model capabilities for AI agents
"""

from .vlm_skill import (
    NvidiaVLMSkill,
    analyze_image,
    describe_image_detailed,
    extract_text_from_image,
    identify_objects_in_image,
    visual_question_answering,
    compare_images,
    get_vlm_skill_info
)

__all__ = [
    'NvidiaVLMSkill',
    'analyze_image',
    'describe_image_detailed',
    'extract_text_from_image',
    'identify_objects_in_image',
    'visual_question_answering',
    'compare_images',
    'get_vlm_skill_info'
]

__version__ = '1.0.0'

