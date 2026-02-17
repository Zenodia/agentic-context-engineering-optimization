"""
NVIDIA Image Generation Skill - Scripts Package

This package contains the implementation of the image generation skill
using NVIDIA's Flux.1 Schnell model.
"""

from .image_gen_skill import (
    ImageGenerationSkill,
    generate_image,
    generate_multiple_images,
    get_image_generation_skill_info
)

__all__ = [
    'ImageGenerationSkill',
    'generate_image',
    'generate_multiple_images',
    'get_image_generation_skill_info'
]

__version__ = '1.0.0'

