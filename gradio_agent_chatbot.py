#!/usr/bin/env python3
"""
Agent Skills Chatbot - Enhanced with SkillLoader Integration + Query Decomposition
Demonstrates agentic tool usage with skill discovery and execution
Now using skill_loader.py for OpenSkills + AI Planner integration
Supports complex multi-skill queries via query decomposition
"""

import os
import sys
import re
import json
import gradio as gr
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from openai import OpenAI
from datetime import datetime
import tempfile

# Import the new SkillLoader infrastructure
from skill_loader import SkillLoader
from plan_manager import PlanManager
from query_decomposition import query_decomposition_call

# Note: No longer importing skills for direct execution
# Now using subprocess execution to offload LLM context window


class AgentSkillsChatbot:
    """
    Enhanced Agent Skills Chatbot using SkillLoader
    
    Implements the 5-step Agent Skills integration process:
    1. Discover skills in configured directories
    2. Load metadata (name and description) at startup
    3. Match user tasks to relevant skills
    4. Activate skills by loading full instructions
    5. Execute scripts and access resources as needed
    
    Reference: https://agentskills.io/integrate-skills#overview
    """
    
    def __init__(self, skills_base_path: str, api_key: Optional[str] = None):
        """
        Initialize chatbot with SkillLoader
        
        Args:
            skills_base_path: Base path containing skill directories
            api_key: NVIDIA API key (defaults to NVIDIA_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "NVIDIA_API_KEY must be set as environment variable or passed to constructor. "
                "Get your key at: https://build.nvidia.com/"
            )
        
        # STEP 1: Discover skills in configured directories
        print(f"🔍 Step 1: Discovering skills from: {skills_base_path}")
        self.skill_loader = SkillLoader(Path(skills_base_path))
        
        # STEP 2: Load metadata (name and description) at startup
        print(f"📋 Step 2: Loading metadata at startup")
        self.skills = self.skill_loader.list_skills()
        print(f"✅ Discovered {len(self.skills)} skill(s):")
        for skill in self.skills:
            print(f"   📦 {skill.name} - {skill.skill_type}")
            print(f"      {skill.description[:80]}...")
        
        # Initialize OpenAI client with NVIDIA endpoint
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.api_key
        )
        self.model = "nvidia/llama-3.1-nemotron-nano-8b-v1"
        
        # Note: No longer initializing skill instances for direct execution
        # Now using subprocess execution to offload LLM context
        print("✅ Using subprocess execution (offloading LLM context)")
        
        # Initialize PlanManager for tracking query decomposition plans
        self.plan_manager = PlanManager(plans_dir=".")
        self.current_plan_id = None  # Track current plan ID for step updates
    
    
    # ========================================================================
    # QUERY DECOMPOSITION: Break complex queries into atomic steps
    # ========================================================================
    
    def decompose_query(self, user_query: str) -> Dict[str, Any]:
        """
        Decompose complex user query into atomic steps with skill assignments
        
        Analyzes if query requires multiple skills and creates execution plan.
        Example: "book myself for 1 hour tomorrow for creative work. Generate some ideas"
        -> Step 1: calendar-assistant to book time
        -> Step 2: nvidia-ideagen to generate ideas
        
        Args:
            user_query: User's question or request
            
        Returns:
            Dict with:
                - multi_steps: bool (whether query needs multiple skills)
                - output_steps: list of steps with skill_name and rationale
        """
        # Build available skills description for the decomposition prompt
        available_skills_desc = ""
        for skill in self.skills:
            available_skills_desc += f"- {skill.name}: {skill.description}\n"
        
        # Use the centralized query_decomposition_call which handles LLM and file writing
        decomposition_result, plan_id = query_decomposition_call(
            user_input=user_query,
            memory_section="",
            history_section="",
            available_skills_desc=available_skills_desc,
            plan_manager=self.plan_manager,
            write_to_file=True
        )
        
        # Store plan_id for step status updates
        self.current_plan_id = plan_id
        
        return decomposition_result
    
    # ========================================================================
    # STEP 3: Match user tasks to relevant skills
    # Reference: https://agentskills.io/integrate-skills#overview
    # ========================================================================
    
    def step3_match_skill(self, user_query: str) -> Tuple[Optional[str], dict]:
        """
        STEP 3: Match user task to relevant skill
        
        Analyzes user query and scores each skill based on keyword matching
        and semantic similarity to skill descriptions.
        
        Args:
            user_query: User's question or request
            
        Returns:
            Tuple of (skill_name, match_info_dict)
            match_info includes: score, matched_keywords, reasoning
        """
        query_lower = user_query.lower()
        
        # Define trigger keywords for each skill
        triggers = {
            'calendar-assistant': [
                'calendar', 'meeting', 'appointment', 'schedule', 'event',
                'book', 'create event', 'add to calendar', 'set up meeting',
                'remind', 'deadline'
            ],
            'nvidia-ideagen': [
                'idea', 'brainstorm', 'generate ideas', 'creative', 'concept',
                'ideation', 'innovation', 'suggest', 'come up with', 'think of'
            ],
            'nvidia-vlm': [
                'analyze image', 'what is in', 'describe image', 'identify',
                'extract text', 'ocr', 'read text', 'what does this show',
                'image analysis', 'visual', 'picture', 'photo'
            ],
            'image-generation': [
                'generate image', 'create image', 'make image', 'draw',
                'generate picture', 'create picture', 'visualize', 'design',
                'produce image', 'image of'
            ]
        }
        
        # Score each discovered skill based on trigger keyword matches
        skill_scores = {}
        skill_matches = {}
        
        for skill in self.skills:
            if skill.name in triggers:
                keywords = triggers[skill.name]
                matched_kw = [kw for kw in keywords if kw in query_lower]
                score = len(matched_kw)
                
                if score > 0:
                    skill_scores[skill.name] = score
                    skill_matches[skill.name] = {
                        'score': score,
                        'matched_keywords': matched_kw,
                        'description': skill.description[:100]
                    }
        
        # Return skill with highest score
        if skill_scores:
            best_skill = max(skill_scores, key=skill_scores.get)
            match_info = skill_matches[best_skill]
            match_info['reasoning'] = f"Matched {match_info['score']} keyword(s): {', '.join(match_info['matched_keywords'][:3])}"
            return best_skill, match_info
        
        return None, {'reasoning': 'No skill matched the query'}
    
    # ========================================================================
    # STEP 4: Activate skills by loading full instructions
    # Reference: https://agentskills.io/integrate-skills#overview
    # ========================================================================
    
    def step4_activate_skill(self, skill_name: str) -> dict:
        """
        STEP 4: Activate skill by loading full instructions with progressive disclosure
        
        Loads the complete SKILL.md content including all instructions,
        capabilities, and usage guidelines. Generates progressive prompt
        injection with tool descriptions and resource listings.
        
        Args:
            skill_name: Name of skill to activate
            
        Returns:
            Dict with activation info: instructions_loaded, content_length, progressive_prompt
        """
        skill = self.skill_loader.get_skill(skill_name)
        
        if not skill:
            return {
                'success': False,
                'error': f"Skill '{skill_name}' not found",
                'instructions_loaded': False
            }
        
        # Generate progressive prompt with full tool descriptions
        progressive_prompt = self.skill_loader.generate_progressive_prompt(
            skill_name,
            include_tools=True,
            include_resources=True
        )
        
        activation_info = {
            'success': True,
            'skill_name': skill_name,
            'skill_type': skill.skill_type,
            'instructions_loaded': bool(skill.skill_md_content),
            'base_content_length': len(skill.skill_md_content) if skill.skill_md_content else 0,
            'progressive_prompt_length': len(progressive_prompt),
            'progressive_prompt': progressive_prompt,
            'has_config': bool(skill.config),
            'has_references': (skill.skill_path / 'references').exists(),
            'has_assets': (skill.skill_path / 'assets').exists()
        }
        
        # Check for tools
        tools = self.skill_loader.discover_tools(skill_name)
        activation_info['tools_discovered'] = len(tools)
        activation_info['tool_names'] = [t._tool_name for t in tools[:5]]  # First 5
        
        # Get entry script for subprocess execution
        entry_script = self.skill_loader.get_skill_entry_script(skill_name)
        activation_info['has_entry_script'] = entry_script is not None
        if entry_script:
            activation_info['entry_script'] = str(entry_script.name)
        
        return activation_info
    
    def build_system_prompt(
        self, 
        activated_skill: Optional[str] = None,
        progressive_prompt: Optional[str] = None
    ) -> str:
        """
        Build system prompt with skills XML from SkillLoader
        Includes activated skill's progressive prompt disclosure if provided
        
        Args:
            activated_skill: Name of skill to activate (if any)
            progressive_prompt: Progressive prompt with full tool descriptions
            
        Returns:
            Complete system prompt string
        """
        # Base system prompt
        base_prompt = f"""You are an intelligent AI assistant with access to specialized skills.

When responding to user queries:
1. Analyze if the query matches any available skill's purpose
2. If a skill is activated, follow its instructions precisely
3. The skill will be executed via subprocess - you help interpret results
4. If no skill matches, respond normally using your general knowledge

Current date: {datetime.now().strftime("%Y-%m-%d")}
Current time: {datetime.now().strftime("%H:%M:%S")}

"""
        
        # Add skills XML from SkillLoader
        skills_xml = self.skill_loader.generate_skills_xml()
        prompt = base_prompt + skills_xml + "\n"
        
        # If a skill is activated, add progressive prompt disclosure
        if activated_skill and progressive_prompt:
            prompt += f"\n{'='*60}\n"
            prompt += f"# ACTIVATED SKILL: {activated_skill}\n"
            prompt += f"{'='*60}\n\n"
            prompt += "## Progressive Disclosure - Full Skill Information:\n\n"
            prompt += progressive_prompt
            prompt += f"\n\n{'='*60}\n"
            prompt += "## Execution Method\n\n"
            prompt += "This skill will be executed via subprocess to offload your context window.\n"
            prompt += "You should help interpret the results and provide helpful responses to the user.\n"
            prompt += f"{'='*60}\n"
        
        return prompt
    
    # ========================================================================
    # STEP 5: Execute scripts and access resources as needed
    # Reference: https://agentskills.io/integrate-skills#overview
    # ========================================================================
    
    def step5_execute_calendar_skill(self, user_query: str) -> dict:
        """
        STEP 5: Execute calendar skill via subprocess
        
        Args:
            user_query: User's calendar request
            
        Returns:
            Dict with execution results: success, output, resources_used
        """
        execution_info = {
            'tool_used': 'natural_language_to_ics',
            'resources_used': [],
            'execution_time': datetime.now().isoformat(),
            'execution_method': 'subprocess'
        }
        
        try:
            # Execute via subprocess
            result = self.skill_loader.execute_skill_subprocess(
                skill_name='calendar-assistant',
                command='natural_language_to_ics',
                parameters={
                    'query': user_query,
                    'api_key': self.api_key
                },
                timeout=30
            )
            
            if not result['success']:
                execution_info['success'] = False
                execution_info['error'] = result.get('error', 'Unknown error')
                return execution_info
            
            # Parse output
            output = result['output']
            
            # Handle both JSON and raw output
            if isinstance(output, dict):
                execution_info['success'] = True
                execution_info['parsed_data'] = output.get('parsed_data', {})
                execution_info['ics_content'] = output.get('ics_content', '').encode('utf-8')
                execution_info['output_size'] = len(execution_info['ics_content'])
            else:
                execution_info['success'] = True
                execution_info['ics_content'] = output.encode('utf-8') if isinstance(output, str) else output
                execution_info['output_size'] = len(execution_info['ics_content'])
            
            # Check what resources were available
            skill = self.skill_loader.get_skill('calendar-assistant')
            if skill:
                if (skill.skill_path / 'references').exists():
                    execution_info['resources_used'].append('references/ available')
                if (skill.skill_path / 'assets').exists():
                    execution_info['resources_used'].append('assets/ available')
            
            return execution_info
        
        except Exception as e:
            execution_info['success'] = False
            execution_info['error'] = str(e)
            return execution_info
    
    def step5_execute_ideagen_skill(self, user_query: str, temperature: float):
        """
        STEP 5: Execute IdeaGen skill via subprocess
        
        Args:
            user_query: User's idea generation request
            temperature: Creativity level
            
        Yields:
            Tuple of (chunk, execution_info)
        """
        execution_info = {
            'tool_used': 'generate_ideas',
            'resources_used': [],
            'execution_time': datetime.now().isoformat(),
            'success': True,
            'execution_method': 'subprocess'
        }
        
        try:
            # Parse query to extract parameters
            num_ideas_match = re.search(r'(\d+)\s+ideas?', user_query.lower())
            num_ideas = int(num_ideas_match.group(1)) if num_ideas_match and 1 <= int(num_ideas_match.group(1)) <= 10 else 5
            
            # Extract topic
            topic = re.sub(r'generate|brainstorm|give me|create|come up with|i need', '', user_query, flags=re.IGNORECASE)
            topic = re.sub(r'\d+\s+ideas?\s+(for|about|on)?', '', topic, flags=re.IGNORECASE)
            topic = topic.strip() or user_query
            
            execution_info['parameters'] = {
                'topic': topic,
                'num_ideas': num_ideas,
                'creativity': temperature
            }
            
            # Check what resources are available
            skill = self.skill_loader.get_skill('nvidia-ideagen')
            if skill:
                if (skill.skill_path / 'references').exists():
                    execution_info['resources_used'].append('references/ available')
                if (skill.skill_path / 'assets').exists():
                    execution_info['resources_used'].append('assets/ available')
            
            # Execute via subprocess
            yield "🔄 Executing skill via subprocess...\n\n", execution_info
            
            result = self.skill_loader.execute_skill_subprocess(
                skill_name='nvidia-ideagen',
                command='generate_ideas',
                parameters={
                    'topic': topic,
                    'num_ideas': num_ideas,
                    'creativity': temperature,
                    'api_key': self.api_key
                },
                timeout=60
            )
            
            if not result['success']:
                execution_info['success'] = False
                execution_info['error'] = result.get('error', 'Unknown error')
                yield f"❌ Error: {execution_info['error']}", execution_info
                return
            
            # Parse and yield output
            output = result['output']
            
            if isinstance(output, dict):
                ideas = output.get('ideas', [])
                yield f"✅ **Generated {len(ideas)} Ideas:**\n\n", execution_info
                
                for i, idea in enumerate(ideas, 1):
                    yield f"**Idea {i}:**\n{idea}\n\n", execution_info
            else:
                # Raw text output
                yield str(output), execution_info
        
        except Exception as e:
            execution_info['success'] = False
            execution_info['error'] = str(e)
            yield f"❌ Error executing idea generation skill: {str(e)}", execution_info
    
    def step5_execute_vlm_skill(self, user_query: str, image_path: Optional[str] = None):
        """
        STEP 5: Execute VLM skill via subprocess
        
        Args:
            user_query: User's image analysis request
            image_path: Path to the image to analyze
            
        Yields:
            Tuple of (chunk, execution_info)
        """
        execution_info = {
            'tool_used': 'analyze_image',
            'resources_used': [],
            'execution_time': datetime.now().isoformat(),
            'success': True,
            'execution_method': 'subprocess'
        }
        
        try:
            if not image_path:
                execution_info['success'] = False
                execution_info['error'] = 'No image provided for analysis'
                yield "❌ Error: Please upload an image to analyze", execution_info
                return
            
            # Extract the specific task from the query
            prompt = user_query
            if "analyze" in user_query.lower() or "describe" in user_query.lower():
                prompt = "Describe what you see in this image in detail."
            elif "extract text" in user_query.lower() or "ocr" in user_query.lower():
                prompt = "Extract all text visible in this image."
            elif "identify" in user_query.lower():
                prompt = "Identify all significant objects in this image."
            
            execution_info['parameters'] = {
                'image_path': image_path,
                'prompt': prompt
            }
            
            # Execute via subprocess
            yield "🔄 Analyzing image...\n\n", execution_info
            
            result = self.skill_loader.execute_skill_subprocess(
                skill_name='nvidia-vlm',
                command='analyze_image',
                parameters={
                    'image_path': image_path,
                    'prompt': prompt,
                    'temperature': 0.2
                },
                timeout=60
            )
            
            if not result['success']:
                execution_info['success'] = False
                execution_info['error'] = result.get('error', 'Unknown error')
                yield f"❌ Error: {execution_info['error']}", execution_info
                return
            
            # Parse and yield output
            output = result['output']
            
            # Handle JSON output from subprocess
            if isinstance(output, dict):
                if output.get('success'):
                    analysis_result = output.get('result', '')
                    yield f"✅ **Image Analysis:**\n\n{analysis_result}\n\n", execution_info
                else:
                    execution_info['success'] = False
                    execution_info['error'] = output.get('error', 'Unknown error')
                    yield f"❌ Error: {execution_info['error']}", execution_info
            else:
                # Fallback for plain text output
                yield f"✅ **Image Analysis:**\n\n{output}\n\n", execution_info
        
        except Exception as e:
            execution_info['success'] = False
            execution_info['error'] = str(e)
            yield f"❌ Error executing VLM skill: {str(e)}", execution_info
    
    def step5_execute_image_generation_skill(self, user_query: str):
        """
        STEP 5: Execute Image Generation skill via subprocess
        
        Args:
            user_query: User's image generation request
            
        Yields:
            Tuple of (chunk, execution_info, image_path)
        """
        execution_info = {
            'tool_used': 'generate_image',
            'resources_used': [],
            'execution_time': datetime.now().isoformat(),
            'success': True,
            'execution_method': 'subprocess'
        }
        
        try:
            # Extract prompt from query
            prompt = user_query
            # Remove trigger phrases
            for phrase in ['generate image', 'create image', 'make image', 'draw', 'generate picture', 'create picture']:
                prompt = re.sub(phrase, '', prompt, flags=re.IGNORECASE)
            prompt = re.sub(r'^(of|for|about)\s+', '', prompt.strip(), flags=re.IGNORECASE)
            prompt = prompt.strip() or user_query
            
            # Check if multiple variations requested
            count_match = re.search(r'(\d+)\s+(variations?|versions?|images?)', user_query.lower())
            count = int(count_match.group(1)) if count_match and 2 <= int(count_match.group(1)) <= 10 else 1
            
            execution_info['parameters'] = {
                'prompt': prompt,
                'count': count
            }
            
            # Execute via subprocess
            if count > 1:
                yield f"🎨 Generating {count} variations...\n\n", execution_info, None
                
                result = self.skill_loader.execute_skill_subprocess(
                    skill_name='image-generation',
                    command='generate_multiple_images',
                    parameters={
                        'prompt': prompt,
                        'count': count,
                        'width': 1024,
                        'height': 1024,
                        'steps': 4
                    },
                    timeout=120
                )
            else:
                yield "🎨 Generating image...\n\n", execution_info, None
                
                result = self.skill_loader.execute_skill_subprocess(
                    skill_name='image-generation',
                    command='generate_image',
                    parameters={
                        'prompt': prompt,
                        'width': 1024,
                        'height': 1024,
                        'seed': 0,
                        'steps': 4
                    },
                    timeout=60
                )
            
            if not result['success']:
                execution_info['success'] = False
                execution_info['error'] = result.get('error', 'Unknown error')
                yield f"❌ Error: {execution_info['error']}", execution_info, None
                return
            
            # Parse output
            output = result['output']
            
            if count > 1 and isinstance(output, dict):
                # Check if it's an error response
                if not output.get('success'):
                    execution_info['success'] = False
                    execution_info['error'] = output.get('error', 'Generation failed')
                    yield f"❌ Error: {execution_info['error']}", execution_info, None
                    return
                
                results = output.get('results', [])
                successful_images = [r['image_path'] for r in results if r.get('success')]
                
                yield f"✅ **Generated {len(successful_images)} images!**\n\n", execution_info, successful_images
                
                for i, img_path in enumerate(successful_images, 1):
                    yield f"📸 Image {i}: {Path(img_path).name}\n", execution_info, successful_images
                
            elif isinstance(output, dict) and output.get('success'):
                image_path = output.get('image_path')
                yield f"✅ **Image generated!**\n\n📸 Saved to: {Path(image_path).name}\n", execution_info, [image_path]
            elif isinstance(output, dict) and not output.get('success'):
                # Skill returned error in JSON format
                execution_info['success'] = False
                execution_info['error'] = output.get('error', 'Generation failed')
                yield f"❌ Error: {execution_info['error']}", execution_info, None
            else:
                execution_info['success'] = False
                execution_info['error'] = 'Unexpected output format'
                yield "❌ Error: Unexpected output format", execution_info, None
        
        except Exception as e:
            execution_info['success'] = False
            execution_info['error'] = str(e)
            yield f"❌ Error executing image generation skill: {str(e)}", execution_info, None
    
    def step5_execute_shell_commands_skill(self, user_query: str):
        """
        STEP 5: Execute shell commands skill DIRECTLY (FAST - no subprocess!)
        
        Executes shell commands directly by importing and calling functions,
        bypassing the slow subprocess + JSON overhead.
        
        Args:
            user_query: User's shell command request
            
        Yields:
            Tuple of (chunk, execution_info)
        """
        execution_info = {
            'tool_used': 'shell_commands_direct',
            'execution_time': datetime.now().isoformat(),
            'success': True,
            'execution_method': 'direct_import'  # FAST!
        }
        
        try:
            # Import shell commands module directly for fast execution
            import sys
            from pathlib import Path
            
            # Add shell commands to path
            shell_skill_path = Path(__file__).parent / 'shell_commands_skill' / 'scripts'
            if str(shell_skill_path) not in sys.path:
                sys.path.insert(0, str(shell_skill_path))
            
            # Import the shell commands module
            import shell_commands
            
            yield "🔄 Executing shell commands directly...\n\n", execution_info
            
            # Parse the query to determine which command to run
            query_lower = user_query.lower()
            
            # Route to appropriate shell command function
            # Handle: "identify where is the README.md file"
            if ('identify' in query_lower or 'where' in query_lower or 'locate' in query_lower) and 'readme' in query_lower:
                # Simple location query - just confirm it's in root
                from pathlib import Path
                readme_path = Path('./README.md')
                if readme_path.exists():
                    result = f"📄 Found README.md in the root directory: {readme_path.resolve()}"
                else:
                    result = "❌ README.md not found in root directory"
                yield f"✅ **Location:**\n\n{result}\n", execution_info
                
            # Handle: "grep the README.md file for the section described performance"  
            elif ('grep' in query_lower or 'extract' in query_lower or 'get' in query_lower or 'section' in query_lower) and 'readme' in query_lower and ('performance' in query_lower or 'speed' in query_lower or 'fast' in query_lower or 'architecture' in query_lower or 'implement' in query_lower):
                # Performance/architecture query - read multiple relevant sections
                import re
                
                # Try to read the README file directly for comprehensive info
                try:
                    from pathlib import Path
                    readme_path = Path('./README.md')
                    
                    if readme_path.exists():
                        content = readme_path.read_text(encoding='utf-8')
                        
                        # Extract sections related to performance, speed, architecture
                        relevant_sections = []
                        lines = content.split('\n')
                        
                        # Keywords that indicate relevant sections
                        section_keywords = [
                            'performance', 'speed', 'fast', 'optimization', 'kv-cache', 
                            'context engineering', 'architecture', 'key insight', 'speedup',
                            'latency', 'throughput', 'how it works', 'technical implementation'
                        ]
                        
                        current_section = []
                        in_relevant_section = False
                        section_title = ""
                        
                        for i, line in enumerate(lines):
                            # Check if this is a header
                            if line.startswith('#'):
                                # Save previous section if it was relevant
                                if in_relevant_section and current_section:
                                    relevant_sections.append({
                                        'title': section_title,
                                        'content': '\n'.join(current_section[:100])  # Limit to 100 lines per section
                                    })
                                
                                # Check if new section is relevant
                                line_lower = line.lower()
                                in_relevant_section = any(kw in line_lower for kw in section_keywords)
                                
                                if in_relevant_section:
                                    section_title = line
                                    current_section = [line]
                                else:
                                    current_section = []
                                    
                            elif in_relevant_section:
                                current_section.append(line)
                                
                                # Also capture content with relevant keywords even if not in titled section
                                line_lower = line.lower()
                                if any(kw in line_lower for kw in section_keywords) and len(current_section) < 5:
                                    # Start capturing from here
                                    in_relevant_section = True
                        
                        # Add last section if relevant
                        if in_relevant_section and current_section:
                            relevant_sections.append({
                                'title': section_title or "Performance Details",
                                'content': '\n'.join(current_section[:100])
                            })
                        
                        # Format output
                        if relevant_sections:
                            result = f"📊 **Found {len(relevant_sections)} relevant section(s) in README.md:**\n\n"
                            for idx, section in enumerate(relevant_sections[:5], 1):  # Limit to top 5 sections
                                result += f"\n{'-'*60}\n"
                                result += f"**Section {idx}: {section['title']}**\n\n"
                                result += section['content']
                                result += f"\n{'-'*60}\n"
                        else:
                            # Fallback: grep for specific terms
                            result = shell_commands.grep_in_file(
                                filepath='README.md',
                                search_pattern='performance|speed|optimization|KV-cache|Context Engineering',
                                case_sensitive=False,
                                context_lines=10,
                                show_line_numbers=True
                            )
                    else:
                        result = "❌ README.md not found"
                        execution_info['success'] = False
                        
                except Exception as e:
                    # Fallback to grep
                    result = shell_commands.grep_in_file(
                        filepath='README.md',
                        search_pattern='performance|speed|fast|optimization',
                        case_sensitive=False,
                        context_lines=8,
                        show_line_numbers=True
                    )
                
                yield f"✅ **Performance & Architecture Information:**\n\n{result}\n", execution_info
                
            elif 'find' in query_lower and 'readme' in query_lower:
                # Find README files
                result = shell_commands.find_files(pattern='README.md', search_path='.')
                yield f"✅ **Search Results:**\n\n{result}\n", execution_info
                
            elif 'grep' in query_lower or 'search' in query_lower:
                # Generic grep - extract search pattern
                import re
                pattern_match = re.search(r'"([^"]+)"|\'([^\']+)\'|for\s+(\S+)', query_lower)
                if pattern_match:
                    search_pattern = pattern_match.group(1) or pattern_match.group(2) or pattern_match.group(3)
                    
                    # Determine file to search in
                    if 'readme' in query_lower:
                        result = shell_commands.grep_in_file(
                            filepath='README.md',
                            search_pattern=search_pattern,
                            case_sensitive=False,
                            context_lines=3
                        )
                    else:
                        result = shell_commands.grep_files(
                            search_text=search_pattern,
                            file_pattern='*.md',
                            case_sensitive=False
                        )
                    
                    yield f"✅ **Search Results:**\n\n{result}\n", execution_info
                else:
                    yield "❌ Could not parse search pattern. Please specify what to search for.\n", execution_info
                    execution_info['success'] = False
                    
            elif 'list' in query_lower or 'ls' in query_lower:
                # List directory
                path = '.' if 'current' in query_lower or 'here' in query_lower else None
                result = shell_commands.list_directory(path=path)
                yield f"✅ **Directory Listing:**\n\n{result}\n", execution_info
                
            elif 'cat' in query_lower or 'show' in query_lower or 'display' in query_lower:
                # Show file contents - extract filename
                import re
                file_match = re.search(r'(?:cat|show|display|read)\s+(?:file\s+)?([^\s]+)', query_lower)
                if file_match:
                    filename = file_match.group(1)
                    result = shell_commands.head_file(filepath=filename, num_lines=50)
                    yield f"✅ **File Contents:**\n\n{result}\n", execution_info
                else:
                    yield "❌ Could not parse filename. Please specify which file to display.\n", execution_info
                    execution_info['success'] = False
                    
            elif 'performance' in query_lower or 'speed' in query_lower or 'fast' in query_lower:
                # User asking about performance - grep README for performance section
                result = shell_commands.grep_in_file(
                    filepath='README.md',
                    search_pattern='performance|speed|optimization',
                    case_sensitive=False,
                    context_lines=8,
                    show_line_numbers=True
                )
                yield f"✅ **Performance Information from README:**\n\n{result}\n", execution_info
                
            else:
                # Generic: try to find relevant files or show help
                result = shell_commands.check_safety_status()
                yield f"ℹ️ **Shell Commands Available:**\n\n{result}\n", execution_info
                yield f"\n💡 Try asking: 'find README', 'grep performance in README', 'list files', etc.\n", execution_info
        
        except ImportError as e:
            execution_info['success'] = False
            execution_info['error'] = f"Could not import shell_commands module: {str(e)}"
            yield f"❌ Error: {execution_info['error']}\n", execution_info
            
        except Exception as e:
            execution_info['success'] = False
            execution_info['error'] = str(e)
            yield f"❌ Error executing shell commands: {str(e)}\n", execution_info
    
    def chat_stream(
        self, 
        user_query: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        image_path: Optional[str] = None
    ):
        """
        Process user query with streaming response
        Implements the 5-step Agent Skills process with visible progress
        NOW WITH QUERY DECOMPOSITION for multi-skill queries
        Supports image input for VLM and image output for generation
        
        Args:
            user_query: User's question or request
            temperature: LLM temperature (0-1)
            max_tokens: Maximum tokens to generate
            image_path: Path to uploaded image (for VLM skill)
            
        Yields:
            Tuple of (response_chunk, step_info_dict, ics_content_bytes, generated_images)
            step_info includes: step, skill_name, details
        """
        # Display steps progress header
        progress_header = """**🔄 Agent Skills Process (with Query Decomposition)**
        
Following the 5-step integration from [agentskills.io](https://agentskills.io/integrate-skills#overview):

"""
        yield progress_header, {'step': 'header'}, None, None
        
        # ===== STEP 1 & 2: Already done at startup =====
        step_info = {
            'step': 1,
            'name': 'Discover & Load',
            'status': 'completed',
            'details': f'Found {len(self.skills)} skills: {", ".join([s.name for s in self.skills])}'
        }
        yield f"**✅ Steps 1-2: Discover & Load Metadata** - {step_info['details']}\n\n", step_info, None, None
        
        # ===== NEW: Query Decomposition =====
        step_info = {'step': 'decompose', 'name': 'Decompose', 'status': 'in_progress'}
        yield f"**⏳ Query Decomposition** - Analyzing query complexity...\n", step_info, None, None
        
        decomposition = self.decompose_query(user_query)
        
        is_multi_step = decomposition.get('multi_steps', False)
        execution_plan = decomposition.get('output_steps', [])
        
        if is_multi_step:
            step_info['status'] = 'completed'
            yield f"**✅ Query Decomposition Complete** - Detected complex multi-skill query: {len(execution_plan)} steps\n", step_info, None, None
            for plan_step in execution_plan:
                yield f"   - Step {plan_step['step_nr']}: `{plan_step['skill_name']}` - {plan_step['rationale']}\n", step_info, None, None
            yield "\n", step_info, None, None
        else:
            step_info['status'] = 'completed'
            yield f"**✅ Query Decomposition Complete** - Single-skill query\n\n", step_info, None, None
        
        # ===== Execute each step in the plan =====
        # Track results from all steps
        all_results = []
        ics_content_to_return = None
        generated_images_to_return = []
        
        for plan_step in execution_plan:
            step_nr = plan_step['step_nr']
            skill_name = plan_step['skill_name']
            sub_query = plan_step.get('sub_query', user_query)
            rationale = plan_step['rationale']
            
            # Handle special skill types
            if skill_name == 'none':
                yield f"\n\n**⊘ Cannot fulfill request** - {rationale}\n\n", {'step': 'error'}, None, None
                continue
            
            if skill_name == 'chitchat':
                # Simple chitchat - just acknowledge
                yield f"\n\n{sub_query}\n\n", {'step': 'chitchat'}, None, None
                all_results.append(f"Step {step_nr}: Chitchat handled")
                continue
            
            # Handle final_response: Synthesize all previous results
            if skill_name == 'final_response':
                yield f"\n{'='*60}\n", {'step': 'separator'}, None, None
                yield f"**📋 Executing Step {step_nr}/{len(execution_plan)}: Final Response Synthesis**\n", {'step': step_nr}, None, None
                yield f"*{rationale}*\n\n", {'step': step_nr}, None, None
                
                # Generate comprehensive response using LLM with all accumulated results
                yield f"**🤖 Generating comprehensive response...**\n\n", {'step': 'synthesis'}, None, None
                
                # Build context from all previous steps
                context_summary = f"Original user query: {user_query}\n\n"
                context_summary += "Results from previous steps:\n"
                for idx, result in enumerate(all_results, 1):
                    context_summary += f"{idx}. {result}\n"
                
                # Read the plan file to get detailed step outputs
                if self.current_plan_id:
                    plan_data = self.plan_manager.get_plan(self.current_plan_id)
                    if plan_data and 'steps' in plan_data:
                        context_summary += "\n\nDetailed step outputs:\n"
                        for step in plan_data['steps']:
                            if step.get('result'):
                                context_summary += f"\nStep {step['step_nr']} ({step['skill_name']}):\n{step['result']}\n"
                
                # Call LLM to synthesize final response
                synthesis_prompt = f"""Based on the following information, provide a comprehensive and well-structured response to the user's question.

{context_summary}

User's question: {sub_query}

Provide a detailed, informative response that consolidates all the information above. Focus on answering the user's original question comprehensively."""

                try:
                    completion = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant that synthesizes information to provide comprehensive answers."},
                            {"role": "user", "content": synthesis_prompt}
                        ],
                        temperature=0.5,
                        max_tokens=2048,
                        stream=True
                    )
                    
                    synthesized_response = ""
                    for chunk in completion:
                        if chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            synthesized_response += content
                            yield content, {'step': 'synthesis'}, None, None
                    
                    yield f"\n\n", {'step': 'synthesis'}, None, None
                    all_results.append(f"Step {step_nr}: Final response synthesized")
                    
                    # Update plan with synthesis result
                    if self.current_plan_id:
                        self.plan_manager.update_step_status(
                            self.current_plan_id, 
                            step_nr, 
                            "completed", 
                            f"Synthesized final response ({len(synthesized_response)} chars)"
                        )
                except Exception as e:
                    error_msg = f"❌ Error generating synthesis: {str(e)}\n\n"
                    yield error_msg, {'step': 'error'}, None, None
                    all_results.append(f"Step {step_nr}: Synthesis failed - {str(e)}")
                
                continue
            
            # Show which step we're executing
            yield f"\n{'='*60}\n", {'step': 'separator'}, None, None
            yield f"**📋 Executing Step {step_nr}/{len(execution_plan)}: `{skill_name}`**\n", {'step': step_nr}, None, None
            yield f"*{rationale}*\n\n", {'step': step_nr}, None, None
            
            # ===== STEP 3: Match (for this sub-query) =====
            step_info = {'step': 3, 'name': 'Match', 'status': 'in_progress', 'plan_step': step_nr}
            yield f"**⏳ Step 3: Matching** - `{skill_name}`\n", step_info, None, None
            
            # Direct match from decomposition
            matched_skill = skill_name if skill_name in [s.name for s in self.skills] else None
            
            if not matched_skill:
                yield f"**⊘ Skill Not Found** - `{skill_name}` is not available\n\n", step_info, None, None
                all_results.append(f"Step {step_nr} ({skill_name}): Skill not available")
                
                # Update plan: mark step as failed with reason
                if self.current_plan_id:
                    self.plan_manager.update_step_status(self.current_plan_id, step_nr, "failed", f"Skill '{skill_name}' not found")
                continue
            
            step_info['status'] = 'completed'
            yield f"**✅ Step 3: Matched** - `{matched_skill}`\n\n", step_info, None, None
            
            # ===== STEP 4: Activate =====
            step_info = {'step': 4, 'name': 'Activate', 'status': 'in_progress', 'skill_name': matched_skill, 'plan_step': step_nr}
            yield f"**⏳ Step 4: Activating** - `{matched_skill}`...\n", step_info, None, None
            
            activation_info = self.step4_activate_skill(matched_skill)
            
            if not activation_info['success']:
                yield f"**❌ Activation Failed** - {activation_info.get('error', 'Unknown error')}\n\n", step_info, None, None
                all_results.append(f"Step {step_nr} ({skill_name}): Activation failed")
                
                # Update plan: mark step as failed with error
                if self.current_plan_id:
                    self.plan_manager.update_step_status(self.current_plan_id, step_nr, "failed", f"Activation failed: {activation_info.get('error', 'Unknown')}")
                continue
            
            tools_count = activation_info['tools_discovered']
            step_info['status'] = 'completed'
            yield f"**✅ Step 4: Activated** - {tools_count} tools ready\n\n", step_info, None, None
            
            # ===== STEP 5: Execute =====
            step_info = {'step': 5, 'name': 'Execute', 'status': 'in_progress', 'skill_name': matched_skill, 'plan_step': step_nr}
            exec_method = "directly (fast!)" if matched_skill == "shell-commands" else "via subprocess"
            yield f"**⏳ Step 5: Executing** - Running `{matched_skill}` {exec_method}...\n\n", step_info, None, None
            
            # Update plan: mark step as in_progress
            if self.current_plan_id:
                self.plan_manager.update_step_status(self.current_plan_id, step_nr, "in_progress")
            
            # Execute based on skill type
            if matched_skill == "calendar-assistant":
                exec_info = self.step5_execute_calendar_skill(sub_query)
                
                if exec_info['success']:
                    parsed_data = exec_info.get('parsed_data', {})
                    
                    if parsed_data:
                        result_summary = f"""✅ **Calendar Event Created!**

📅 **Event Details:**
- **Title:** {parsed_data.get('summary', 'Event')}
- **Date:** {parsed_data.get('start_date', 'TBD')}
- **Time:** {parsed_data.get('start_time', 'All day')}
- **Duration:** {parsed_data.get('duration_hours', 1)} hours

📥 **Download the .ics file** using the button on the right →
"""
                    else:
                        result_summary = "✅ **Calendar Event Created!** Download the .ics file on the right →"
                    
                    yield result_summary, step_info, exec_info['ics_content'], None
                    all_results.append(f"Step {step_nr}: Calendar event created")
                    ics_content_to_return = exec_info['ics_content']
                    
                    # Update plan: mark step as completed with condensed crucial info only
                    if self.current_plan_id:
                        # Condense to only crucial information
                        summary = parsed_data.get('summary', 'Untitled Event').strip() or 'Untitled Event'
                        start_date = parsed_data.get('start_date', '').strip()
                        start_time = parsed_data.get('start_time', '').strip()
                        duration = parsed_data.get('duration_hours', 1)
                        
                        # Format: "Title on YYYY-MM-DD at HH:MM (Xh)"
                        if start_date and start_time:
                            result_text = f"{summary} on {start_date} at {start_time} ({duration}h)"
                        elif start_date:
                            result_text = f"{summary} on {start_date} ({duration}h)"
                        else:
                            result_text = f"{summary} scheduled ({duration}h)"
                        
                        self.plan_manager.update_step_status(self.current_plan_id, step_nr, "completed", result_text)
                else:
                    error_msg = f"❌ Error: {exec_info.get('error', 'Unknown error')}"
                    yield error_msg, step_info, None, None
                    all_results.append(f"Step {step_nr}: Failed - {exec_info.get('error', 'Unknown')}")
                    
                    # Update plan: mark step as failed with error message
                    if self.current_plan_id:
                        self.plan_manager.update_step_status(self.current_plan_id, step_nr, "failed", f"Error: {exec_info.get('error', 'Unknown')}")
            
            elif matched_skill == "nvidia-ideagen":
                ideas_text = ""
                for chunk, exec_info in self.step5_execute_ideagen_skill(sub_query, temperature):
                    ideas_text += chunk
                    yield chunk, step_info, None, None
                
                all_results.append(f"Step {step_nr}: Generated ideas")
                
                # Update plan: mark step as completed with ideas summary
                if self.current_plan_id:
                    # Store first 300 chars of generated ideas as result
                    result_summary = f"Generated ideas: {ideas_text[:300]}..." if len(ideas_text) > 300 else f"Generated ideas: {ideas_text}"
                    self.plan_manager.update_step_status(self.current_plan_id, step_nr, "completed", result_summary)
            
            elif matched_skill == "nvidia-vlm":
                vlm_text = ""
                for chunk, exec_info in self.step5_execute_vlm_skill(sub_query, image_path):
                    vlm_text += chunk
                    yield chunk, step_info, None, None
                
                all_results.append(f"Step {step_nr}: Image analysis complete")
                
                # Update plan: mark step as completed with analysis summary and image path
                if self.current_plan_id:
                    # Get absolute path of the uploaded image
                    abs_image_path = str(Path(image_path).resolve()) if image_path else "No image provided"
                    result_summary = f"Image analysis of '{abs_image_path}': {vlm_text[:200]}..." if len(vlm_text) > 200 else f"Image analysis of '{abs_image_path}': {vlm_text}"
                    self.plan_manager.update_step_status(self.current_plan_id, step_nr, "completed", result_summary)
            
            elif matched_skill == "image-generation":
                step_generated_images = []
                execution_error = None
                
                for chunk, exec_info, images in self.step5_execute_image_generation_skill(sub_query):
                    yield chunk, step_info, None, images
                    if images:
                        generated_images_to_return.extend(images)
                        step_generated_images.extend(images)
                    # Track if there was an error
                    if exec_info.get('success') == False:
                        execution_error = exec_info.get('error', 'Unknown error')
                
                # Update plan with absolute paths to generated images (NOT the actual image data)
                if self.current_plan_id:
                    if step_generated_images:
                        # Convert to absolute paths - these are the actual file locations
                        abs_image_paths = [str(Path(img).resolve()) for img in step_generated_images]
                        paths_str = ", ".join(abs_image_paths)
                        result_summary = f"Generated {len(step_generated_images)} image(s) at: {paths_str}"
                        self.plan_manager.update_step_status(self.current_plan_id, step_nr, "completed", result_summary)
                        all_results.append(f"Step {step_nr}: Image(s) generated at {paths_str[:100]}")
                    elif execution_error:
                        # Failed with error
                        result_summary = f"Image generation failed: {execution_error}"
                        self.plan_manager.update_step_status(self.current_plan_id, step_nr, "failed", result_summary)
                        all_results.append(f"Step {step_nr}: Failed - {execution_error}")
                    else:
                        # No images and no clear error (shouldn't happen but handle gracefully)
                        result_summary = f"Image generation attempted for: {sub_query[:200]} (no images returned)"
                        self.plan_manager.update_step_status(self.current_plan_id, step_nr, "completed", result_summary)
                        all_results.append(f"Step {step_nr}: Image generation completed (no files returned)")
            
            elif matched_skill == "shell-commands":
                # Execute shell commands directly (FAST - no subprocess JSON overhead!)
                shell_result = ""
                for chunk, exec_info in self.step5_execute_shell_commands_skill(sub_query):
                    shell_result += chunk
                    yield chunk, step_info, None, None
                
                all_results.append(f"Step {step_nr}: Shell command executed")
                
                # Update plan: mark step as completed with shell output summary
                if self.current_plan_id:
                    # Store first 200 chars of shell output as result
                    result_summary = f"Shell output: {shell_result[:200]}..." if len(shell_result) > 200 else f"Shell output: {shell_result}"
                    self.plan_manager.update_step_status(self.current_plan_id, step_nr, "completed", result_summary)
            
            step_info['status'] = 'completed'
            yield f"\n", step_info, None, None
        
        # ===== Final Summary (if multi-step) =====
        if is_multi_step and len(all_results) > 1:
            yield f"\n\n{'='*60}\n", {'step': 'summary'}, None, None
            yield f"**✅ Multi-Step Execution Complete**\n\n", {'step': 'summary'}, None, None
            yield f"Completed {len(all_results)} steps:\n", {'step': 'summary'}, None, None
            for result in all_results:
                yield f"- {result}\n", {'step': 'summary'}, None, None
        
        # Return any ICS content from calendar steps or generated images
        if ics_content_to_return or generated_images_to_return:
            yield "", {'step': 'complete'}, ics_content_to_return, generated_images_to_return if generated_images_to_return else None


class GradioUI:
    """Gradio UI for Agent Skills Chatbot"""
    
    def __init__(self, chatbot: AgentSkillsChatbot):
        self.chatbot = chatbot
    
    def save_ics_file(self, ics_content: bytes, summary: str = "event") -> str:
        """Save ICS content to a temporary file"""
        # Clean summary for filename
        safe_name = "".join(c for c in summary if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
        safe_name = safe_name or "event"
        
        filename = f"event_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
        
        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.ics')
        temp_file.write(ics_content)
        temp_file.close()
        
        return temp_file.name
    
    def process_message(
        self, 
        user_message: str, 
        history: List[dict],
        temperature: float,
        input_image = None
    ):
        """
        Process user message and stream response with 5-step progress
        
        Now displays each step of the Agent Skills process as it executes
        Supports image input for VLM and image output for generation
        """
        if not user_message or not user_message.strip():
            yield history, None, "", None
            return
        
        # Add user message to history in messages format (required by Gradio 6.5.1)
        history = history or []
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": ""})
        
        # Stream response with step-by-step progress
        response = ""
        ics_content_bytes = None
        generated_images = []
        activated_skill = None
        
        # Get image path if provided
        image_path = input_image if input_image else None
        
        for chunk, step_info, ics_bytes, gen_images in self.chatbot.chat_stream(
            user_message, 
            temperature=temperature,
            image_path=image_path
        ):
            response += chunk
            
            # Track which skill was activated
            if step_info and 'skill_name' in step_info and not activated_skill:
                activated_skill = step_info['skill_name']
            
            # Update chat with current response
            history[-1]["content"] = response
            
            # Store ICS content if returned
            if ics_bytes:
                ics_content_bytes = ics_bytes
            
            # Store generated images if returned
            if gen_images:
                generated_images = gen_images
            
            # Yield current state
            yield history, None, "", (generated_images if generated_images else None)
        
        # If we have ICS content, save it
        if ics_content_bytes:
            # Decode ICS content for preview
            ics_preview = ics_content_bytes.decode('utf-8')
            
            # Extract summary for filename
            summary_match = re.search(r'SUMMARY:(.*?)(?:\r?\n)', ics_preview)
            summary = summary_match.group(1) if summary_match else "event"
            
            # Save to temp file
            file_path = self.save_ics_file(ics_content_bytes, summary)
            
            # Return with file and preview
            yield history, file_path, ics_preview, (generated_images if generated_images else None)
            return
        
        # Final yield
        yield history, None, "", (generated_images if generated_images else None)
    
    def clear_history(self):
        """Clear chat history"""
        return []
    
    def build_interface(self) -> gr.Blocks:
        """Build Gradio interface"""
        
        with gr.Blocks(title="Agent Skills Chatbot - Enhanced") as interface:
            
            gr.Markdown(
                """
                # 🤖 Agent Skills Chatbot
                
                Intelligent assistant with multi-skill execution powered by **skill_loader.py**
                
                ---
                """
            )
            
            # Chat interface
            with gr.Row():
                with gr.Column(scale=3):
                    chatbot = gr.Chatbot(
                        label="Chat",
                        height=500,
                        show_label=True,
                    )
                    
                    with gr.Row():
                        user_input = gr.Textbox(
                            label="Your message",
                            placeholder="Ask me to generate ideas, book an event, analyze an image, or generate images...",
                            scale=4,
                            lines=2
                        )
                        submit_btn = gr.Button("Send", variant="primary", scale=1)
                    
                    # Image input for VLM skill
                    with gr.Row():
                        input_image = gr.Image(
                            label="📸 Upload Image (for image analysis)",
                            type="filepath",
                            height=200
                        )
                
                with gr.Column(scale=1):
                    # Calendar file download
                    gr.Markdown("### 📅 Calendar Event")
                    ics_download = gr.File(
                        label="📥 Download .ics File",
                        visible=True,
                        interactive=False
                    )
                    gr.Markdown("""
                    **How to use:**
                    1. Download the .ics file
                    2. Double-click to open
                    3. Import to your calendar
                    """)
                    
                    # Generated images gallery
                    gr.Markdown("### 🎨 Generated Images")
                    output_gallery = gr.Gallery(
                        label="Generated Images",
                        show_label=False,
                        columns=2,
                        rows=2,
                        height=400,
                        object_fit="contain"
                    )
                    
                    # Examples - Focus on complex multi-skill queries
                    gr.Examples(
                        examples=[
                            # Multi-skill: Calendar + Ideas
                            "Book myself for 1 hour tomorrow at 2pm for creative work, then generate 5 innovative AI project ideas",
                            "Schedule a brainstorming session Friday at 3pm and give me 7 startup ideas to discuss during the meeting",
                            "Create a planning session next Monday at 10am for 2 hours and brainstorm ideas about sustainable technology",
                            "I wanna understand how this chatbot is so fast, could you give me some insights?",
                            # Multi-skill: Calendar + Image Generation
                            "Schedule an art review meeting tomorrow at 4pm and generate an image of a modern minimalist workspace",
                            "Book a design sprint next Wednesday at 9am and create an image of a futuristic smartwatch interface",
                            
                            # Multi-skill: Ideas + Image Generation
                            "Generate 4 ideas for eco-friendly product packaging and then create an image visualizing the best concept",
                            "Brainstorm 5 concepts for a mobile meditation app and generate an image of the app's home screen",
                            "Give me 6 ideas for urban park designs and create an image showing a bird's eye view of a green park",
                            
                            # Multi-skill: Calendar + Ideas + Image Generation (3 skills!)
                            "Schedule a product design workshop tomorrow at 1pm, brainstorm 5 wearable tech ideas, and generate an image of a smart ring device",
                            
                            # Multi-skill: Image Analysis + Ideas (requires image upload)
                            "Analyze this image and then generate 5 creative ideas inspired by what you see in the image",
                            
                            # Multi-skill: Image Analysis + Image Generation (requires image upload)
                            "Analyze this image and describe the style, then generate a new image in a similar artistic style",
                            
                            # Complex multi-skill scenarios
                            "Book a creative session next Thursday at 2pm for 3 hours, generate 8 ideas for interactive art installations, and create an image of a holographic art piece",
                            "Schedule a product brainstorm Friday morning at 10am, come up with 6 ideas for smart home devices, and generate an image of a voice-controlled home hub",
                        ],
                        inputs=user_input,
                        label="💡 Complex Multi-Skill Examples (2-3 skills per query!)"
                    )
            
            # Settings
            with gr.Accordion("⚙️ Settings", open=False):
                temperature = gr.Slider(
                    minimum=0.0,
                    maximum=1.0,
                    value=0.7,
                    step=0.1,
                    label="Temperature (creativity)",
                    info="Higher = more creative"
                )
            
            with gr.Row():
                clear_btn = gr.Button("🗑️ Clear Chat")
            
            # Hidden preview textbox
            ics_preview = gr.Textbox(visible=False)
            
            # Event handlers
            submit_btn.click(
                fn=self.process_message,
                inputs=[user_input, chatbot, temperature, input_image],
                outputs=[chatbot, ics_download, ics_preview, output_gallery]
            ).then(
                fn=lambda: "",
                outputs=[user_input]
            )
            
            user_input.submit(
                fn=self.process_message,
                inputs=[user_input, chatbot, temperature, input_image],
                outputs=[chatbot, ics_download, ics_preview, output_gallery]
            ).then(
                fn=lambda: "",
                outputs=[user_input]
            )
            
            clear_btn.click(
                fn=self.clear_history,
                outputs=[chatbot]
            )
            
            gr.Markdown(
                """
                ---
                
                ### 🔧 Technical Details:
                
                **Architecture**: Implements the [Agent Skills Specification](https://agentskills.io/integrate-skills#overview)
                
                - **Query Decomposition**: LLM-powered analysis to break complex queries into atomic steps
                - **5-Step Process**: Discover → Load → Match → Activate → Execute
                - **Multi-Skill Execution**: Sequential execution of multiple skills for complex queries
                - **Skill Loader**: `skill_loader.py` with `@skill_tool` auto-discovery
                - **LLM**: NVIDIA Llama 3.1 Nemotron Nano 8B
                - **Skills Format**: `config.yaml` + `SKILL.md` + `scripts/` + `references/` + `assets/`
                - **Tool Integration**: LangChain StructuredTool compatible
                
                ---
                
                💡 **Features**:
                - ✅ **Query decomposition** for complex multi-skill requests (NEW!)
                - ✅ **Multi-modal support** - image input & output (NEW!)
                - ✅ **Image generation** using NVIDIA Flux.1 Schnell (NEW!)
                - ✅ **Image analysis** using NVIDIA Nemotron VLM (NEW!)
                - ✅ **Step-by-step visualization** of skill execution process
                - ✅ **Auto skill discovery** from directory structure
                - ✅ **Tool auto-discovery** with `@skill_tool` decorator
                - ✅ **Access control aware** via config.yaml
                - ✅ **Resource access** (read_reference, read_asset)
                - ✅ **Streaming responses** with real-time progress
                
                📚 **Reference**: [agentskills.io/integrate-skills](https://agentskills.io/integrate-skills#overview)
                """
            )
        
        return interface


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("Agent Skills Chatbot - Enhanced with SkillLoader")
    print("="*80 + "\n")
    
    # Check for API key
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        print("❌ Error: NVIDIA_API_KEY environment variable not set")
        print("\nPlease set it using:")
        print("  PowerShell: $env:NVIDIA_API_KEY='your-key-here'")
        print("  CMD:        set NVIDIA_API_KEY=your-key-here")
        print("  Linux/Mac:  export NVIDIA_API_KEY='your-key-here'")
        print("\nGet your key at: https://build.nvidia.com/")
        sys.exit(1)
    
    # Get project directory
    project_dir = Path(__file__).parent
    
    print(f"📂 Project directory: {project_dir}")
    
    try:
        # Initialize chatbot with SkillLoader
        chatbot = AgentSkillsChatbot(
            skills_base_path=str(project_dir),
            api_key=api_key
        )
        
        # Display discovered skills summary
        print("\n📋 Skills Summary:")
        for skill in chatbot.skills:
            print(f"\n  🎯 {skill.name}")
            print(f"     Type: {skill.skill_type}")
            print(f"     Version: {skill.skill_md_metadata.get('version', 'unknown')}")
            print(f"     Description: {skill.description[:100]}...")
        
        # Discover tools for each skill
        print("\n🔧 Discovered Tools:")
        for skill in chatbot.skills:
            tools = chatbot.skill_loader.discover_tools(skill.name)
            if tools:
                print(f"\n  📦 {skill.name}: {len(tools)} tool(s)")
                for tool in tools[:3]:  # Show first 3
                    print(f"     - {tool._tool_name}")
        
        print("\n" + "="*80)
        print("✅ Initialization complete! Launching Gradio interface...")
        print("="*80 + "\n")
        
        # Build and launch UI
        ui = GradioUI(chatbot)
        interface = ui.build_interface()
        
        # Launch
        interface.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False
        )
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
