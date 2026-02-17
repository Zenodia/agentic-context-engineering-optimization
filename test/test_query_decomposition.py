#!/usr/bin/env python3
"""
Test Script for Query Decomposition in Agent Skills Chatbot
Tests the new multi-skill query decomposition capability
"""

import os
import sys
from pathlib import Path

# Check for API key
api_key = os.getenv("NVIDIA_API_KEY")
if not api_key:
    print("❌ Error: NVIDIA_API_KEY environment variable not set")
    print("\nPlease set it using:")
    print("  PowerShell: $env:NVIDIA_API_KEY='your-key-here'")
    print("  CMD:        set NVIDIA_API_KEY=your-key-here")
    print("  Linux/Mac:  export NVIDIA_API_KEY='your-key-here'")
    sys.exit(1)

# Import the chatbot
from gradio_agent_chatbot import AgentSkillsChatbot

def print_decomposition(query: str, result: dict):
    """Pretty print decomposition result"""
    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print(f"{'='*80}")
    
    is_multi = result.get('multi_steps', False)
    steps = result.get('output_steps', [])
    
    print(f"\n📊 Analysis: {'🔀 Multi-Step' if is_multi else '📍 Single-Step'} ({len(steps)} step{'s' if len(steps) != 1 else ''})")
    print(f"\n📋 Execution Plan:")
    
    for step in steps:
        step_nr = step.get('step_nr', '?')
        skill = step.get('skill_name', 'unknown')
        rationale = step.get('rationale', 'N/A')
        sub_query = step.get('sub_query', query)
        
        print(f"\n  Step {step_nr}: {skill}")
        print(f"    Rationale: {rationale}")
        print(f"    Sub-query: {sub_query}")


def main():
    """Test query decomposition with various queries"""
    
    print("\n" + "="*80)
    print("Query Decomposition Test Suite")
    print("="*80)
    
    # Initialize chatbot
    project_dir = Path(__file__).parent
    print(f"\n📂 Initializing from: {project_dir}")
    
    try:
        chatbot = AgentSkillsChatbot(
            skills_base_path=str(project_dir),
            api_key=api_key
        )
        print(f"✅ Chatbot initialized with {len(chatbot.skills)} skills")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Test cases
    test_queries = [
        # Simple greetings
        "hello",
        "how are you?",
        
        # Single-skill queries
        "Schedule a meeting tomorrow at 2pm for 2 hours",
        "Generate 5 ideas for sustainable living",
        
        # Multi-skill queries (the main feature!)
        "Book myself for 1 hour tomorrow for me to do creative work. Generate some ideas for me to start with",
        "Schedule a brainstorming session Friday at 3pm and give me 5 startup ideas to discuss",
        "Create a calendar event for project planning next Monday at 10am and suggest innovative approaches",
        
        # Edge cases
        "what is 2+2?",
        "tell me a joke",
    ]
    
    print("\n" + "="*80)
    print("Testing Query Decomposition")
    print("="*80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'─'*80}")
        print(f"Test {i}/{len(test_queries)}")
        
        try:
            result = chatbot.decompose_query(query)
            print_decomposition(query, result)
        except Exception as e:
            print(f"\n❌ Error decomposing query: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("✅ Query Decomposition Tests Complete!")
    print("="*80)
    
    print("\n📝 Summary:")
    print("- The query decomposition system analyzes each query")
    print("- It determines if single or multiple skills are needed")
    print("- Complex queries are broken into atomic steps")
    print("- Each step is assigned to the appropriate skill")
    print("\n🚀 Next: Run 'python gradio_agent_chatbot.py' to see full execution!")


if __name__ == "__main__":
    main()

