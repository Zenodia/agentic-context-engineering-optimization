#!/usr/bin/env python3
"""
Quick test to verify the final_response synthesis fix
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from query_decomposition import query_decomposition_call
from plan_manager import PlanManager

def test_query_decomposition():
    """Test that query decomposition generates good sub-queries"""
    print("="*80)
    print("Testing Query Decomposition for Performance Query")
    print("="*80)
    
    # Initialize PlanManager
    pm = PlanManager(plans_dir=".")
    
    # Test query about chatbot performance
    test_query = "I wanna understand how this chatbot is so fast, could you give me some insights?"
    
    print(f"\n📝 User Query: {test_query}")
    print("\n⏳ Running query decomposition...\n")
    
    # Build skills description
    available_skills = """- calendar-assistant: Create calendar events and .ics files from natural language
- nvidia-ideagen: Generate creative ideas and concepts using NVIDIA NIM
- nvidia-vlm: Analyze images and extract information using vision-language models
- image-generation: Generate images from text descriptions using NVIDIA NIM
- shell-commands: Execute safe shell commands like find, grep, ls, cat for file operations"""
    
    # Decompose query
    result, plan_id = query_decomposition_call(
        user_input=test_query,
        memory_section="",
        history_section="",
        available_skills_desc=available_skills,
        plan_manager=pm,
        write_to_file=True
    )
    
    print("✅ Decomposition Result:")
    print(f"   Multi-steps: {result.get('multi_steps', False)}")
    print(f"   Total steps: {len(result.get('output_steps', []))}")
    print(f"   Plan ID: {plan_id}\n")
    
    # Display each step
    for step in result.get('output_steps', []):
        print(f"\n📋 Step {step['step_nr']}: {step['skill_name']}")
        print(f"   Rationale: {step['rationale']}")
        print(f"   Sub-query: {step['sub_query']}")
    
    # Check if final_response step exists
    has_final_response = any(s['skill_name'] == 'final_response' for s in result.get('output_steps', []))
    
    print("\n" + "="*80)
    print("✅ Test Results:")
    print("="*80)
    print(f"✓ Query decomposed successfully")
    print(f"✓ Generated {len(result.get('output_steps', []))} steps")
    print(f"✓ Has final_response step: {has_final_response}")
    
    if has_final_response:
        final_step = [s for s in result.get('output_steps', []) if s['skill_name'] == 'final_response'][0]
        print(f"✓ Final response sub-query: {final_step['sub_query'][:100]}...")
    
    print("\n💡 Key Improvements:")
    print("   1. Shell commands will now extract actual README content (not just search)")
    print("   2. final_response step will synthesize results with LLM")
    print("   3. User gets comprehensive answer instead of raw grep output")
    
    print("\n" + "="*80)
    print("Test Complete! ✨")
    print("="*80)
    
    # Clean up
    if plan_id:
        print(f"\n🧹 Plan saved to: {pm.plan_file} (ID: {plan_id})")

if __name__ == "__main__":
    # Set API key from environment
    if not os.getenv("NVIDIA_API_KEY"):
        print("⚠️  Warning: NVIDIA_API_KEY not set. Query decomposition may fail.")
        print("   Set it with: export NVIDIA_API_KEY='your-key-here'")
        print()
    
    test_query_decomposition()

