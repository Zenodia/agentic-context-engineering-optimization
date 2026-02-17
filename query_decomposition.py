from langchain_core.prompts import ChatPromptTemplate
from langchain_nvidia_ai_endpoints import ChatNVIDIA
import os, sys 
import json
from pathlib import Path
from typing import Optional, List
from langchain_core.messages import SystemMessage, HumanMessage
from plan_manager import PlanManager
from self_hosted_nim_w_vllm_backend import SelfHostedNIMLLM
from skill_loader import load_skills, SkillLoader

# Global LLM instance - will be initialized by initialize_llm()
llm = None

def initialize_llm(llm_call_method: str = None, api_key: Optional[str] = None, model: str = "nvidia/llama-3.1-nemotron-nano-8b-v1"):
    """
    Initialize the global LLM instance based on method preference.
    
    This is the UNIFIED LLM initialization function used across all modules:
    - query_decomposition.py
    - tranditional_reactagent.py
    - compare_context_engineering_optimization_on_off.py
    - plan_manager.py (doesn't use LLM, but other modules do)
    
    UNIFIED IMPLEMENTATION: All modules use ChatNVIDIA (from langchain_nvidia_ai_endpoints)
    for the "direct" method. This ensures:
    - LangChain-compatible interface
    - Consistent message format handling
    - Seamless integration with LangChain tools and agents
    
    Args:
        llm_call_method: "client" (self-hosted) or "direct" (external API). 
                        If None, uses environment variable USE_SELF_HOSTED_LLM
        api_key: NVIDIA API key (required for "direct" method). 
                If None, uses NVIDIA_API_KEY environment variable
        model: Model name to use (default: nvidia/llama-3.1-nemotron-nano-8b-v1)
    
    Returns:
        Initialized LLM instance:
        - SelfHostedNIMLLM for "client" method (mimics ChatNVIDIA interface)
        - ChatNVIDIA for "direct" method (external NVIDIA API)
    """
    global llm
    
    # Determine method: parameter > environment variable > default to direct
    if llm_call_method is None:
        use_self_hosted = os.environ.get("USE_SELF_HOSTED_LLM", "false").lower() == "true"
        llm_call_method = "client" if use_self_hosted else "direct"
    
    if llm_call_method == "client":
        # Use self-hosted NIM LLM (localhost:8000)
        llm = SelfHostedNIMLLM(model=model)
        print("✅ Using Self-Hosted NIM LLM")
    else:
        # Use external NVIDIA API
        api_key = api_key or os.environ.get("NVIDIA_API_KEY")
        if not api_key:
            raise ValueError(
                "NVIDIA_API_KEY must be set as environment variable or passed to initialize_llm() when using 'direct' method. "
                "Get your key at: https://build.nvidia.com/"
            )
        llm = ChatNVIDIA(
            model=model,
            api_key=api_key,
            temperature=0.3,
            max_completion_tokens=36000
        )
        print("✅ Using ChatNVIDIA (External API)")
    
    return llm

# Initialize LLM on module import (backward compatibility)
# Use environment variable or default to direct method
_llm_method = os.environ.get("USE_SELF_HOSTED_LLM", "false").lower() == "true"
if _llm_method:
    initialize_llm(llm_call_method="client")
else:
    # Try to initialize with direct method, but don't fail if API key is missing
    # (allows modules to import and initialize later)
    try:
        initialize_llm(llm_call_method="direct")
    except ValueError:
        # API key not set - will be initialized later
        pass

query_decompostion_prompt = """You are a Query Decomposition Agent specialized in analyzing user queries and creating step-by-step plans.

Your task is to determine if the query requires multiple skills or can be handled by a single skill.

<Available Skills>

{available_skills_desc}

IMPORTANT: These are the ONLY skills available. You CANNOT use any other skills not listed here.
If a query requires capabilities beyond these skills, you MUST use the "none" skill.

Additional skills:
- chitchat: For casual conversation, greetings, small talk
- final_response: For directly responding to the user (used as the final step)
- none: Use when query cannot be fulfilled with available skills

</Available Skills>

<Instructions>

1. Analyze Query Complexity:
   - ATOMIC queries: require only 1 skill (e.g., "book a meeting" or "generate ideas")
   - COMPLEX queries: require 2+ skills (e.g., "book time and generate ideas")

2. For ATOMIC Queries:
   - Set "multi_steps" to false
   - Identify the primary skill needed
   - If it's a simple greeting or question, use "final_response"
   
3. For COMPLEX Queries:
   - Set "multi_steps" to true
   - Decompose into atomic steps
   - Each step uses EXACTLY ONE skill
   - Order steps logically
   - Last step should typically be "final_response" if needed for synthesis

</Instructions>

<Output Format>

Respond with ONLY valid JSON in this format:

{{
  "multi_steps": true/false,
  "output_steps": [
    {{
      "step_nr": 1,
      "skill_name": "skill-name-here",
      "rationale": "why this skill is used",
      "sub_query": "specific query for this step"
    }}
  ]
}}

</Output Format>

<Examples>

Example 1 - Greeting :
User: "hello, so what can you do?"
Response:
{{
  "multi_steps": false,
  "output_steps": [
    {{
      "step_nr": 1,
      "skill_name": "final_response",   
      "rationale": "Simple greeting, no skills needed",
      "sub_query": "hello, so what can you do?"
    }}
  ]
}}

Example 2 -  Atomic (single skill)  :
User: "schedule a meeting tomorrow at 2pm"
Response:
{{
  "multi_steps": false,
  "output_steps": [
    {{
      "step_nr": 1,
      "skill_name": "calendar-assistant",
      "rationale": "User wants to book a calendar event",
      "sub_query": "schedule a meeting tomorrow at 2pm"
    }}
  ]
}}


Example 3 - query about the implementation of this chatbot or the code base  :
User: "I wanna understand how this chatbot is so fast, could you give me some insights?"
Response:
{{
  "multi_steps": true,
  "output_steps": [
    {{
      "step_nr": 1,
      "skill_name": "shell-commands",
      "rationale": "Locate the README.md file which contains the chatbot's architecture and performance documentation",
      "sub_query": "identify where the README.md file is located"
    }},    
    {{
      "step_nr": 2,
      "skill_name": "shell-commands",
      "rationale": "Extract the performance and architecture sections from README.md to understand the speed optimizations",
      "sub_query": "extract the performance and architecture sections from README.md file in the root directory of this folder"
    }},
    {{
      "step_nr": 3,
      "skill_name": "final_response",
      "rationale": "Synthesize the extracted information into a comprehensive explanation of the chatbot's performance",
      "sub_query": "provide a comprehensive explanation of how the chatbot achieves its superior speed, including key technical details and optimizations"
    }}
  ]
}}


Example 4- Complex (multiple skills):
User: "book myself for 1 hour tomorrow for creative work. Generate some ideas for me to start with"
Response:
{{
  "multi_steps": true,
  "output_steps": [
    {{
      "step_nr": 1,
      "skill_name": "calendar-assistant",
      "rationale": "First book the time slot for creative work",
      "sub_query": "book 1 hour tomorrow for creative work"
    }},
    {{
      "step_nr": 2,
      "skill_name": "nvidia-ideagen",
      "rationale": "Generate creative ideas to help user get started",
      "sub_query": "Generate ideas for creative work"
    }},
    {{
      "step_nr": 3,
      "skill_name": "final_response",
      "rationale": "Combine results from both skills",
      "sub_query": "Summarize booked time and generated ideas"
    }}
  ]
}}

</Examples>


<Context>
{memory_section}{history_section}
</Context>

Now analyze this query:
{user_input}"""

def _format_skills_description(skill_loader: SkillLoader, user_groups: Optional[List[str]] = None) -> str:
    """
    Format skills from SkillLoader into a readable description for the prompt.
    
    Args:
        skill_loader: SkillLoader instance
        user_groups: Optional user groups for access control
    
    Returns:
        Formatted string describing available skills
    """
    skills = skill_loader.list_skills(user_groups)
    
    if not skills:
        return "No skills available."
    
    skill_descriptions = []
    for skill in sorted(skills, key=lambda s: s.name):
        desc = skill.description.strip() if skill.description else "No description available"
        skill_descriptions.append(f"- {skill.name}: {desc}")
    
    return "\n".join(skill_descriptions)


def query_decomposition_call(
    user_input: str, 
    memory_section: str = "", 
    history_section: str = "./stepwise_plan_history.txt",
    available_skills_desc: Optional[str] = None,
    skill_loader: Optional[SkillLoader] = None,
    skills_base_path: Optional[str | Path] = None,
    exclude_skills: Optional[List[str]] = None,
    user_groups: Optional[List[str]] = None,
    plan_manager: Optional[PlanManager] = None,
    write_to_file: bool = True
):
    """
    Call the LLM with the query and system prompt to decompose the query into steps.
    
    Args:
        user_input: User query string
        memory_section: Memory context section
        history_section: Conversation history section
        available_skills_desc: Description of available skills (used if skill_loader not provided)
        skill_loader: Optional SkillLoader instance to dynamically load skills
        skills_base_path: Optional path to skills directory (auto-loads if skill_loader not provided)
        exclude_skills: Optional list of skill names to exclude (e.g., ['nvidia_vlm_skill', 'image_generation_skill'])
        user_groups: Optional user groups for access control
        plan_manager: Optional PlanManager instance to write plans to file
        write_to_file: Whether to write the plan to file (default: True)
    
    Returns:
        Tuple of (parsed_response, plan_id) where plan_id is None if not written to file
    """
    # Determine skills description
    if skill_loader is None and skills_base_path is not None:
        # Auto-load skills from path
        skill_loader = load_skills(skills_base_path, exclude_skills=exclude_skills)
    
    if skill_loader is not None:
        # Generate skills description from skill loader
        available_skills_desc = _format_skills_description(skill_loader, user_groups)
    elif available_skills_desc is None:
        # Fallback to default
        available_skills_desc = "Default skills: calendar-assistant, nvidia-ideagen"
    
    # Format the system prompt with actual values
    formatted_prompt = query_decompostion_prompt.format(
        available_skills_desc=available_skills_desc,
        memory_section=memory_section if memory_section else "",
        history_section=history_section if history_section else "",
        user_input=user_input
    )
    
    messages = [
        SystemMessage(content=formatted_prompt),
        HumanMessage(content=user_input)
    ]
    
    response = llm.invoke(messages)
    
    try:
        # Try to parse the response as JSON
        parsed_response = json.loads(response.content)
        
        # Ensure it's a proper dictionary
        if not isinstance(parsed_response, dict):
            # Wrap in proper format
            parsed_response = {
                "multi_steps": False,
                "output_steps": [parsed_response] if isinstance(parsed_response, dict) else []
            }
        
        # Write to file if requested and plan_manager is provided
        plan_id = None
        if write_to_file and plan_manager:
            context = {
                "memory_summary": memory_section[:200] if memory_section else "",  # Truncate for storage
                "history_summary": history_section[:200] if history_section else ""  # Truncate for storage
            }
            plan_id = plan_manager.write_plan(
                user_query=user_input,
                decomposition_result=parsed_response,
                context=context
            )
        
        return parsed_response, plan_id
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {response.content}")
        error_response = {
            "multi_steps": False,
            "output_steps": [
                {
                    "step_nr": 1,
                    "skill_name": "final_response",
                    "rationale": f"Error processing query: {str(e)}",
                    "sub_query": user_input
                }
            ]
        }
        
        # Write error response to file if requested
        plan_id = None
        if write_to_file and plan_manager:
            context = {
                "memory_summary": memory_section[:200] if memory_section else "",
                "history_summary": history_section[:200] if history_section else ""
            }
            plan_id = plan_manager.write_plan(
                user_query=user_input,
                decomposition_result=error_response,
                context=context
            )
        
        return error_response, plan_id


if __name__ == "__main__":
    # Initialize PlanManager
    pm = PlanManager(plans_dir=".")
    
    # Example: Load skills dynamically from a skills directory
    # Uncomment and adjust path as needed:
    # skills_path = Path("./skills")  # or wherever your skills are located
    # skill_loader = load_skills(
    #     skills_path,
    #     exclude_skills=['nvidia_vlm_skill', 'image_generation_skill']  # Exclude API-based skills
    # )
    # print(f"✅ Loaded {len(skill_loader.list_skills())} skills from {skills_path}")
    
    # Test queries demonstrating different complexity levels
    test_cases = [
        {
            "query": "hello! how are you?",
            "skills": "calendar-assistant (for booking meetings), nvidia-ideagen (for idea generation)",
            "memory": "",
            "history": "",
            "description": "Simple greeting"
        },
        {
            "query": "schedule a meeting tomorrow at 3pm",
            "skills": "calendar-assistant (for booking meetings), nvidia-ideagen (for idea generation)",
            "memory": "",
            "history": "",
            "description": "Single skill - calendar booking"
        },
        {
            "query": "book 2 hours tomorrow afternoon and give me creative ideas for my project",
            "skills": "calendar-assistant (for booking meetings), nvidia-ideagen (for idea generation)",
            "memory": "",
            "history": "",
            "description": "Complex query - multiple skills (calendar + ideagen)"
        },
        {
            "query": "I want to brainstorm some innovative solutions",
            "skills": "calendar-assistant (for booking meetings), nvidia-ideagen (for idea generation)",
            "memory": "",
            "history": "",
            "description": "Single skill - idea generation"
        },
        {
            "query": "schedule a 1-hour creative session for tomorrow morning, generate startup ideas, and create a calendar reminder",
            "skills": "calendar-assistant (for booking meetings), nvidia-ideagen (for idea generation)",
            "memory": "",
            "history": "",
            "description": "Complex query - calendar, ideagen, and synthesis"
        },
        {
            "query": "tell me a joke",
            "skills": "calendar-assistant (for booking meetings), nvidia-ideagen (for idea generation)",
            "memory": "",
            "history": "",
            "description": "Chitchat - casual conversation"
        },
        {
            "query": "order me a pizza and check the weather",
            "skills": "calendar-assistant (for booking meetings), nvidia-ideagen (for idea generation)",
            "memory": "",
            "history": "",
            "description": "Query that cannot be fulfilled - requires unavailable skills"
        },
    ]
    
    print("\n" + "="*80)
    print("QUERY DECOMPOSITION TESTING - Updated Prompt from gradio_agent_chatbot.py")
    print("="*80)
    print(f"Plans will be written to: {pm.plan_file}")
    print("="*80)
    print("\n💡 Tip: To use skill_loader, pass skills_base_path or skill_loader parameter")
    print("   Example: query_decomposition_call(..., skills_base_path='./skills', exclude_skills=['nvidia_vlm_skill'])")
    print("="*80)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─'*80}")
        print(f"Test Case {i}: {test['description']}")
        print(f"{'─'*80}")
        print(f"Query: \"{test['query']}\"")
        print(f"Available Skills: {test['skills']}")
        
        # Use manual skills description (backward compatible)
        # To use skill_loader instead, replace available_skills_desc with:
        # skills_base_path="./skills", exclude_skills=['nvidia_vlm_skill', 'image_generation_skill']
        result, plan_id = query_decomposition_call(
            user_input=test['query'],
            memory_section=test.get('memory', ''),
            history_section=test.get('history', ''),
            available_skills_desc=test['skills'],
            plan_manager=pm,
            write_to_file=True
        )
        
        print(f"\n📋 Decomposition Result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"\n🆔 Plan ID: {plan_id}")
        
        # Pretty print the steps
        if result and isinstance(result, dict):
            print(f"\n✨ Summary: {'Multi-step' if result.get('multi_steps') else 'Simple'} ({len(result.get('output_steps', []))} steps)")
            for step in result.get('output_steps', []):
                skill_name = step.get('skill_name', 'N/A')
                rationale = step.get('rationale', 'N/A')
                sub_query = step.get('sub_query', 'N/A')
                print(f"   Step {step.get('step_nr')}: {skill_name}")
                print(f"      Rationale: {rationale}")
                print(f"      Sub-query: {sub_query}")
        print()
    
    print("\n" + "="*80)
    print("Testing Complete!")
    print("="*80)
    
    # Demonstrate plan retrieval and manipulation
    print("\n" + "="*80)
    print("DEMONSTRATING PLAN MANAGEMENT FEATURES")
    print("="*80)
    
    # List all plans
    print("\n--- Listing all plans ---")
    all_plans = pm.list_all_plans()
    for plan in all_plans:
        print(f"  Plan {plan['plan_number']}: {plan['query'][:60]}... ({plan['total_steps']} steps, multi: {plan['multi_steps']})")
    
    # Find plans by query
    print("\n--- Finding plans containing 'meeting' ---")
    found = pm.find_plan_by_query("meeting")
    print(f"Found {len(found)} plan(s): {found}")
    
    # Retrieve a specific plan
    if found:
        print("\n--- Retrieving first found plan ---")
        retrieved = pm.get_plan(found[0])
        if retrieved:
            print(f"Query: {retrieved['query']}")
            print(f"Steps:")
            for step in retrieved['steps']:
                print(f"  {step['step_nr']}. {step['skill_name']} - {step['rationale']}")
    
    # Show grep examples
    print("\n" + "="*80)
    print("GREP/BASH SEARCH EXAMPLES")
    print("="*80)
    print(pm.get_search_examples())
    
    print("\n" + "="*80)
    print(f"All plans saved to: {pm.plan_file}")
    print("="*80)
