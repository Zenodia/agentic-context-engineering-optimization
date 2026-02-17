#!/usr/bin/env python3
"""
Test script to verify PlanManager integration with query decomposition
Demonstrates that plans are written to stepwised_plan.txt and updated during execution
"""

import os
import sys
from pathlib import Path
from plan_manager import PlanManager
from query_decomposition import query_decomposition_call

# Check for API key
api_key = os.getenv("NVIDIA_API_KEY")
if not api_key:
    print("❌ Error: NVIDIA_API_KEY environment variable not set")
    print("\nPlease set it using:")
    print("  export NVIDIA_API_KEY='your-key-here'")
    sys.exit(1)

def test_plan_creation_and_updates():
    """Test creating a plan and updating step statuses"""
    print("\n" + "="*80)
    print("TESTING PLAN MANAGER INTEGRATION")
    print("="*80)
    
    # Initialize PlanManager
    pm = PlanManager(plans_dir=".")
    
    # Test query 1: Simple single-step query
    print("\n--- Test 1: Single-step query ---")
    query1 = "schedule a meeting tomorrow at 3pm"
    available_skills = "calendar-assistant (for booking meetings), nvidia-ideagen (for idea generation)"
    
    decomposition, plan_id = query_decomposition_call(
        user_input=query1,
        chapter_name="Time Management",
        sub_topic="Calendar Basics",
        available_skills_desc=available_skills,
        plan_manager=pm,
        write_to_file=True
    )
    
    print(f"✓ Plan created with ID: {plan_id}")
    print(f"  Multi-steps: {decomposition['multi_steps']}")
    print(f"  Total steps: {len(decomposition['output_steps'])}")
    
    # Simulate step execution and status updates
    for step in decomposition['output_steps']:
        step_nr = step['step_nr']
        skill_name = step['skill_name']
        
        print(f"\n  Executing step {step_nr}: {skill_name}")
        
        # Mark as in_progress
        pm.update_step_status(plan_id, step_nr, "in_progress")
        
        # Simulate execution result
        if skill_name == "calendar-assistant":
            result = "Calendar event created: Meeting on 2026-02-04 at 15:00"
            pm.update_step_status(plan_id, step_nr, "completed", result)
            print(f"  ✓ Step {step_nr} completed: {result}")
        elif skill_name == "final_response":
            result = "Responded to user query"
            pm.update_step_status(plan_id, step_nr, "completed", result)
            print(f"  ✓ Step {step_nr} completed: {result}")
    
    # Test query 2: Multi-step query
    print("\n\n--- Test 2: Multi-step query ---")
    query2 = "book 1 hour tomorrow afternoon and generate creative ideas for my project"
    
    decomposition2, plan_id2 = query_decomposition_call(
        user_input=query2,
        chapter_name="Project Planning",
        sub_topic="Creative Sessions",
        available_skills_desc=available_skills,
        plan_manager=pm,
        write_to_file=True
    )
    
    print(f"✓ Plan created with ID: {plan_id2}")
    print(f"  Multi-steps: {decomposition2['multi_steps']}")
    print(f"  Total steps: {len(decomposition2['output_steps'])}")
    
    # Simulate step execution with different outcomes
    for step in decomposition2['output_steps']:
        step_nr = step['step_nr']
        skill_name = step['skill_name']
        
        print(f"\n  Executing step {step_nr}: {skill_name}")
        
        # Mark as in_progress
        pm.update_step_status(plan_id2, step_nr, "in_progress")
        
        # Simulate execution results
        if skill_name == "calendar-assistant":
            result = "Calendar event created: Creative Work on 2026-02-04 at 14:00, Duration: 1 hour"
            pm.update_step_status(plan_id2, step_nr, "completed", result)
            print(f"  ✓ Step {step_nr} completed: {result}")
        elif skill_name == "nvidia-ideagen":
            result = "Generated ideas: 1. Brainstorm new features, 2. Research competitors, 3. Design mockups..."
            pm.update_step_status(plan_id2, step_nr, "completed", result)
            print(f"  ✓ Step {step_nr} completed: {result[:80]}...")
        elif skill_name == "final_response":
            result = "Summarized calendar booking and generated ideas"
            pm.update_step_status(plan_id2, step_nr, "completed", result)
            print(f"  ✓ Step {step_nr} completed: {result}")
    
    # Test query 3: Image-related query (simulated)
    print("\n\n--- Test 3: Image-related query (simulated) ---")
    query3 = "generate an image of a sunset over mountains"
    
    decomposition3, plan_id3 = query_decomposition_call(
        user_input=query3,
        chapter_name="Creative Projects",
        sub_topic="Image Generation",
        available_skills_desc=available_skills,
        plan_manager=pm,
        write_to_file=True
    )
    
    print(f"✓ Plan created with ID: {plan_id3}")
    print(f"  Multi-steps: {decomposition3['multi_steps']}")
    print(f"  Total steps: {len(decomposition3['output_steps'])}")
    
    # Simulate step execution with image generation
    for step in decomposition3['output_steps']:
        step_nr = step['step_nr']
        skill_name = step['skill_name']
        
        if skill_name in ['final_response', 'none', 'chitchat']:
            continue
            
        print(f"\n  Executing step {step_nr}: {skill_name}")
        
        # Mark as in_progress
        pm.update_step_status(plan_id3, step_nr, "in_progress")
        
        # Simulate execution results with image paths
        if skill_name == "image-generation":
            # Simulate absolute paths to generated images
            simulated_image_path = "/home/zenodia/Agents/exp_agent_skill/generated_images/sunset_mountains_20260203_143052.png"
            result = f"Generated 1 image(s) at: {simulated_image_path}"
            pm.update_step_status(plan_id3, step_nr, "completed", result)
            print(f"  ✓ Step {step_nr} completed: {result}")
    
    # Test query 4: Image analysis query (simulated)
    print("\n\n--- Test 4: Image analysis query (simulated) ---")
    query4 = "analyze this image and describe what you see"
    
    decomposition4, plan_id4 = query_decomposition_call(
        user_input=query4,
        chapter_name="Computer Vision",
        sub_topic="Image Analysis",
        available_skills_desc="nvidia-vlm (for image analysis and OCR)",
        plan_manager=pm,
        write_to_file=True
    )
    
    print(f"✓ Plan created with ID: {plan_id4}")
    print(f"  Multi-steps: {decomposition4['multi_steps']}")
    print(f"  Total steps: {len(decomposition4['output_steps'])}")
    
    # Simulate step execution with image analysis
    for step in decomposition4['output_steps']:
        step_nr = step['step_nr']
        skill_name = step['skill_name']
        
        if skill_name in ['final_response', 'none', 'chitchat']:
            continue
            
        print(f"\n  Executing step {step_nr}: {skill_name}")
        
        # Mark as in_progress
        pm.update_step_status(plan_id4, step_nr, "in_progress")
        
        # Simulate execution results with uploaded image path
        if skill_name == "nvidia-vlm":
            # Simulate absolute path to uploaded image
            simulated_uploaded_image = "/tmp/gradio/upload_12345/user_photo.jpg"
            result = f"Image analysis of '{simulated_uploaded_image}': This image shows a landscape with mountains and trees..."
            pm.update_step_status(plan_id4, step_nr, "completed", result)
            print(f"  ✓ Step {step_nr} completed")
            print(f"     Image: {simulated_uploaded_image}")
            print(f"     Result: Image shows a landscape with mountains and trees...")
    
    # Retrieve and display plans
    print("\n\n--- Retrieving Plans ---")
    
    retrieved_plan1 = pm.get_plan(plan_id)
    if retrieved_plan1:
        print(f"\n📋 Plan 1:")
        print(f"  Query: {retrieved_plan1['query']}")
        print(f"  Steps:")
        for step in retrieved_plan1['steps']:
            status_emoji = "✅" if step['status'] == "completed" else "⏳"
            print(f"    {status_emoji} Step {step['step_nr']}: {step['skill_name']} - {step['status']}")
            if step.get('result'):
                print(f"       Result: {step['result'][:80]}...")
    
    retrieved_plan2 = pm.get_plan(plan_id2)
    if retrieved_plan2:
        print(f"\n📋 Plan 2:")
        print(f"  Query: {retrieved_plan2['query']}")
        print(f"  Steps:")
        for step in retrieved_plan2['steps']:
            status_emoji = "✅" if step['status'] == "completed" else "⏳"
            print(f"    {status_emoji} Step {step['step_nr']}: {step['skill_name']} - {step['status']}")
            if step.get('result'):
                print(f"       Result: {step['result'][:80]}...")
    
    retrieved_plan3 = pm.get_plan(plan_id3)
    if retrieved_plan3:
        print(f"\n📋 Plan 3 (Image Generation):")
        print(f"  Query: {retrieved_plan3['query']}")
        print(f"  Steps:")
        for step in retrieved_plan3['steps']:
            status_emoji = "✅" if step['status'] == "completed" else "⏳"
            print(f"    {status_emoji} Step {step['step_nr']}: {step['skill_name']} - {step['status']}")
            if step.get('result'):
                print(f"       Result: {step['result'][:120]}...")
    
    retrieved_plan4 = pm.get_plan(plan_id4)
    if retrieved_plan4:
        print(f"\n📋 Plan 4 (Image Analysis):")
        print(f"  Query: {retrieved_plan4['query']}")
        print(f"  Steps:")
        for step in retrieved_plan4['steps']:
            status_emoji = "✅" if step['status'] == "completed" else "⏳"
            print(f"    {status_emoji} Step {step['step_nr']}: {step['skill_name']} - {step['status']}")
            if step.get('result'):
                # For image analysis, highlight the image path
                result = step['result']
                if "Image analysis of" in result:
                    print(f"       Result: {result[:150]}...")
                else:
                    print(f"       Result: {result[:80]}...")
    
    # List all plans
    print("\n\n--- All Plans ---")
    all_plans = pm.list_all_plans()
    print(f"Total plans: {len(all_plans)}")
    for plan in all_plans:
        print(f"  • Plan {plan['plan_number']}: {plan['query'][:60]}... ({plan['total_steps']} steps)")
    
    print("\n" + "="*80)
    print(f"✅ TEST COMPLETE - Check the file: {pm.plan_file}")
    print("="*80)
    
    # Show how to search the file
    print("\n📝 To inspect the plan file, use:")
    print(f"   cat {pm.plan_file}")
    print(f"   grep '@STATUS:' {pm.plan_file}")
    print(f"   grep '@RESULT:' {pm.plan_file}")
    print()


if __name__ == "__main__":
    test_plan_creation_and_updates()

