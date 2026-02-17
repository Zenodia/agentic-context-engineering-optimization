"""
Test script for NVIDIA Image Generation Skill

This script tests the functionality of the image generation skill
without making actual API calls (unless API key is set).
"""

import os
import sys
from pathlib import Path

# Add image_generation_skill to path for imports
skill_dir = Path(__file__).parent / "image_generation_skill"
if str(skill_dir) not in sys.path:
    sys.path.insert(0, str(skill_dir))

from scripts.image_gen_skill import ImageGenerationSkill, get_image_generation_skill_info


def test_skill_initialization():
    """Test skill initialization"""
    print("\n" + "="*60)
    print("TEST 1: Skill Initialization")
    print("="*60)
    
    api_key = os.getenv("NVIDIA_API_KEY")
    
    if not api_key:
        print("⚠️  NVIDIA_API_KEY not set - testing error handling")
        try:
            skill = ImageGenerationSkill()
            print("❌ Should have raised ValueError")
        except ValueError as e:
            print(f"✅ Correctly raised ValueError: {str(e)[:50]}...")
    else:
        print("✅ API key found")
        try:
            skill = ImageGenerationSkill()
            print("✅ Skill initialized successfully")
            return skill
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return None
    
    return None


def test_skill_info(skill):
    """Test skill info retrieval"""
    print("\n" + "="*60)
    print("TEST 2: Skill Information")
    print("="*60)
    
    if skill is None:
        print("⚠️  Skipping (no skill instance)")
        return
    
    try:
        info = skill.get_skill_info()
        print("✅ Skill info retrieved:")
        print(f"  Name: {info['name']}")
        print(f"  Version: {info['version']}")
        print(f"  Model: {info['model']}")
        print(f"  Status: {info['status']}")
        print(f"  Capabilities: {len(info['capabilities'])} capabilities")
        print(f"  Output directory: {info['output_directory']}")
    except Exception as e:
        print(f"❌ Failed to get skill info: {e}")


def test_tool_functions():
    """Test tool function discovery"""
    print("\n" + "="*60)
    print("TEST 3: Tool Function Discovery")
    print("="*60)
    
    try:
        # Test tool function call
        info = get_image_generation_skill_info()
        
        if "error" in info:
            print("⚠️  Tool function works but skill not initialized")
            print(f"  Error: {info['error']}")
        else:
            print("✅ Tool function works:")
            print(f"  Name: {info['name']}")
            print(f"  Version: {info['version']}")
    except Exception as e:
        print(f"❌ Tool function failed: {e}")


def test_image_generation(skill):
    """Test actual image generation (if API key is set)"""
    print("\n" + "="*60)
    print("TEST 4: Image Generation")
    print("="*60)
    
    if skill is None:
        print("⚠️  Skipping (no skill instance)")
        return
    
    # Ask user if they want to test actual generation
    print("\n⚠️  This will make an actual API call to NVIDIA.")
    response = input("Do you want to test image generation? (y/n): ")
    
    if response.lower() != 'y':
        print("⏭️  Skipping image generation test")
        return
    
    try:
        prompt = "a simple coffee shop interior"
        print(f"\n🎨 Generating image with prompt: '{prompt}'")
        print("⏳ Please wait...")
        
        result = skill.generate_image(
            prompt=prompt,
            width=512,  # Small size for faster testing
            height=512,
            steps=4
        )
        
        if result["success"]:
            print("✅ Image generated successfully!")
            print(f"  📁 Saved to: {result['image_path']}")
            print(f"  📝 Metadata:")
            print(f"    - Model: {result['metadata']['model']}")
            print(f"    - Dimensions: {result['metadata']['width']}x{result['metadata']['height']}")
            print(f"    - Steps: {result['metadata']['steps']}")
            print(f"    - Seed: {result['metadata']['seed']}")
        else:
            print(f"❌ Generation failed: {result.get('error')}")
    
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")


def test_filename_sanitization(skill):
    """Test filename sanitization"""
    print("\n" + "="*60)
    print("TEST 5: Filename Sanitization")
    print("="*60)
    
    if skill is None:
        print("⚠️  Skipping (no skill instance)")
        return
    
    test_cases = [
        "a simple coffee shop",
        "image with / invalid chars",
        "image with <> brackets",
        "very long prompt that should be truncated to a reasonable length for filename",
        "  spaces  around  ",
        "..."
    ]
    
    print("Testing filename sanitization:")
    for test in test_cases:
        sanitized = skill._sanitize_filename(test)
        print(f"  '{test[:40]}' -> '{sanitized}'")
    
    print("✅ Filename sanitization test complete")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("NVIDIA Image Generation Skill - Test Suite")
    print("="*60)
    
    # Run tests
    skill = test_skill_initialization()
    test_skill_info(skill)
    test_tool_functions()
    test_filename_sanitization(skill)
    test_image_generation(skill)
    
    print("\n" + "="*60)
    print("Test Suite Complete")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

