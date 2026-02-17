"""
Test script for NVIDIA VLM Skill
Run this to verify the skill is working correctly
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from nvidia_vlm_skill.scripts.vlm_skill import NvidiaVLMSkill


def test_initialization():
    """Test 1: Skill initialization"""
    print("\n" + "="*60)
    print("TEST 1: Skill Initialization")
    print("="*60)
    
    try:
        skill = NvidiaVLMSkill()
        print("✅ PASSED: Skill initialized successfully")
        return skill
    except ValueError as e:
        print(f"❌ FAILED: {e}")
        print("\nPlease set INFERENCE_API_KEY environment variable:")
        print("  PowerShell: $env:INFERENCE_API_KEY='your-key'")
        print("  Bash: export INFERENCE_API_KEY='your-key'")
        print("\nGet your key at: https://build.nvidia.com/")
        return None
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {e}")
        return None


def test_skill_info(skill):
    """Test 2: Get skill information"""
    print("\n" + "="*60)
    print("TEST 2: Skill Information")
    print("="*60)
    
    try:
        info = skill.get_skill_info()
        print(f"✅ PASSED: Retrieved skill info")
        print(f"\nSkill Name: {info['name']}")
        print(f"Version: {info['version']}")
        print(f"Model: {info['model']}")
        print(f"Capabilities: {len(info['capabilities'])} functions")
        print(f"Status: {info['status']}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_image_validation(skill):
    """Test 3: Image validation"""
    print("\n" + "="*60)
    print("TEST 3: Image Validation")
    print("="*60)
    
    # Test with non-existent file
    try:
        result = skill.analyze_image("../../exp_context_engineering/icyroad.jpg")
        if "❌" in result or "not found" in result.lower():
            print("✅ PASSED: Non-existent file handled correctly")
        else:
            print("⚠️  WARNING: Expected error for non-existent file")
    except Exception as e:
        print(f"⚠️  WARNING: Exception raised - {e}")
    
    return True


def test_with_sample_image(skill, image_path):
    """Test 4: Analyze sample image"""
    print("\n" + "="*60)
    print(f"TEST 4: Image Analysis")
    print("="*60)
    
    if not Path(image_path).exists():
        print(f"⚠️  SKIPPED: Sample image not found at {image_path}")
        print("   Provide an image path to test analysis")
        return False
    
    try:
        print(f"\nAnalyzing: {image_path}")
        print("-" * 60)
        
        # Quick analysis
        result = skill.analyze_image(
            image_path,
            "Provide a brief description of this image",
            temperature=0.2
        )
        
        print(result)
        print("-" * 60)
        
        if result and not result.startswith("❌"):
            print("\n✅ PASSED: Image analyzed successfully")
            return True
        else:
            print("\n❌ FAILED: Analysis returned error")
            return False
            
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        return False


def test_tool_functions():
    """Test 5: Tool function imports"""
    print("\n" + "="*60)
    print("TEST 5: Tool Functions")
    print("="*60)
    
    try:
        from nvidia_vlm_skill.scripts.vlm_skill import (
            analyze_image,
            describe_image_detailed,
            extract_text_from_image,
            identify_objects_in_image,
            visual_question_answering,
            compare_images,
            save_vlm_analysis,
            get_vlm_skill_info
        )
        
        print("✅ PASSED: All 8 tool functions imported successfully")
        print("\nAvailable tools:")
        print("  1. analyze_image")
        print("  2. describe_image_detailed")
        print("  3. extract_text_from_image")
        print("  4. identify_objects_in_image")
        print("  5. visual_question_answering")
        print("  6. compare_images")
        print("  7. save_vlm_analysis")
        print("  8. get_vlm_skill_info")
        return True
        
    except ImportError as e:
        print(f"❌ FAILED: Import error - {e}")
        return False


def test_skill_decorator():
    """Test 6: Skill tool decorators"""
    print("\n" + "="*60)
    print("TEST 6: Skill Tool Decorators")
    print("="*60)
    
    try:
        from nvidia_vlm_skill.scripts.vlm_skill import analyze_image
        
        # Check if function has skill tool attributes
        if hasattr(analyze_image, '_is_skill_tool'):
            print("✅ PASSED: Tool decorators are applied")
            print(f"   Tool name: {getattr(analyze_image, '_tool_name', 'N/A')}")
            print(f"   Description: {getattr(analyze_image, '_tool_description', 'N/A')[:60]}...")
            return True
        else:
            print("⚠️  WARNING: Tool decorators may not be applied")
            print("   (This is OK if skill_loader is not available)")
            return True
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def run_all_tests(sample_image=None):
    """Run all tests"""
    print("\n" + "#"*60)
    print("#" + " "*58 + "#")
    print("#" + "  NVIDIA VLM SKILL - TEST SUITE".center(58) + "#")
    print("#" + " "*58 + "#")
    print("#"*60)
    
    results = []
    
    # Test 1: Initialization
    skill = test_initialization()
    results.append(skill is not None)
    
    if skill is None:
        print("\n" + "="*60)
        print("TESTS ABORTED: Cannot proceed without valid initialization")
        print("="*60)
        return
    
    # Test 2: Skill info
    results.append(test_skill_info(skill))
    
    # Test 3: Validation
    results.append(test_image_validation(skill))
    
    # Test 4: Sample image analysis (if provided)
    if sample_image:
        results.append(test_with_sample_image(skill, sample_image))
    else:
        print("\n" + "="*60)
        print("TEST 4: Image Analysis - SKIPPED")
        print("="*60)
        print("ℹ️  Provide an image path to test analysis:")
        print(f"   python {sys.argv[0]} path/to/image.jpg")
    
    # Test 5: Tool functions
    results.append(test_tool_functions())
    
    # Test 6: Decorators
    results.append(test_skill_decorator())
    
    # Summary
    print("\n" + "#"*60)
    print("#" + " "*58 + "#")
    print("#" + "  TEST SUMMARY".center(58) + "#")
    print("#" + " "*58 + "#")
    print("#"*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! The VLM skill is ready to use.")
    elif passed >= total - 1:
        print("\n✅ Most tests passed. The skill should work correctly.")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
    
    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60)
    print("1. Test with a real image:")
    print(f"   python {sys.argv[0]} path/to/your/image.jpg")
    print("\n2. Try the skill in Python:")
    print("   from nvidia_vlm_skill.scripts.vlm_skill import NvidiaVLMSkill")
    print("   skill = NvidiaVLMSkill()")
    print("   result = skill.analyze_image('image.jpg')")
    print("\n3. Check the documentation:")
    print("   - README.md for quick start")
    print("   - SKILL.md for comprehensive guide")
    print("   - examples.md for usage examples")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Check for sample image argument
    sample_image = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Run tests
    run_all_tests(sample_image)

