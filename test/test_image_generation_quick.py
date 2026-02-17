#!/usr/bin/env python3
"""
Quick test to verify image generation works end-to-end
"""

import os
import sys
from pathlib import Path

# Add image_generation_skill to path
skill_dir = Path(__file__).parent / "image_generation_skill"
if str(skill_dir) not in sys.path:
    sys.path.insert(0, str(skill_dir))

from scripts.image_gen_skill import ImageGenerationSkill

def test_generation():
    api_key = os.getenv("NVIDIA_API_KEY")
    
    if not api_key:
        print("❌ NVIDIA_API_KEY not set")
        return
    
    print("Testing Image Generation Skill...")
    print("="*70)
    
    try:
        # Initialize skill
        skill = ImageGenerationSkill(api_key=api_key)
        print("✅ Skill initialized\n")
        
        # Generate test image
        print("🎨 Generating image: 'a simple coffee shop interior'")
        result = skill.generate_image(
            prompt="a simple coffee shop interior",
            width=1024,
            height=1024,
            seed=0,
            steps=4
        )
        
        print("\n" + "="*70)
        if result["success"]:
            print("✅ SUCCESS! Image generated")
            print(f"📁 Saved to: {result['image_path']}")
            print(f"📊 Metadata: {result['metadata']}")
        else:
            print("❌ FAILED")
            print(f"Error: {result.get('error')}")
            if 'response' in result:
                print(f"Response keys: {list(result['response'].keys())}")
        print("="*70)
        
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_generation()

