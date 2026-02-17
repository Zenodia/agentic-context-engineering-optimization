"""
NVIDIA Idea Generation Skill Implementation
Agent Skills API Compliant with NAT Integration

This is the implementation code that gets called after the agent
reads the SKILL.md instructions and decides to use this skill.

Includes @skill_tool decorated functions for NAT auto-discovery.
"""

import os
import sys
from openai import OpenAI
from typing import Generator, Dict, List, Optional, Any
import json
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
import time

# Import skill_tool decorator from skill_loader
try:
    from skill_loader import skill_tool
except ImportError:
    # Fallback: Add parent directory to path
    parent_dir = Path(__file__).parent.parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    try:
        from skill_loader import skill_tool
    except ImportError:
        # If still can't import, define a dummy decorator
        def skill_tool(name=None, description=None, return_direct=False):
            def decorator(func):
                func._is_skill_tool = True
                func._tool_name = name or func.__name__
                func._tool_description = description or func.__doc__ or ""
                func._tool_return_direct = return_direct
                return func
            return decorator


class NvidiaIdeaGenSkill:
    """
    NVIDIA-powered idea generation skill for AI agents
    
    This implementation is activated when an agent:
    1. Discovers the skill via SKILL.md metadata in system prompt
    2. Reads the full SKILL.md instructions
    3. Decides the user needs idea generation
    4. Calls this implementation
    """
    
    def __init__(self, api_key: Optional[str] = None, ideas_dir: Optional[str] = None):
        """
        Initialize the NVIDIA idea generation skill
        
        Args:
            api_key: NVIDIA API key (defaults to NVIDIA_API_KEY env var)
            ideas_dir: Custom directory for saved ideas (defaults to 'ideas/')
        
        Raises:
            ValueError: If NVIDIA_API_KEY is not set
        """
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "NVIDIA_API_KEY must be set as environment variable or passed to constructor. "
                "Get your key at: https://build.nvidia.com/"
            )
        
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.api_key
        )
        self.model = "nvidia/llama-3.1-nemotron-nano-8b-v1"
        
        # Create directory for saved ideas
        self.ideas_dir = Path(ideas_dir) if ideas_dir else Path("ideas")
        self.ideas_dir.mkdir(exist_ok=True)
        
        self.version = "1.0.0"
        self.name = "nvidia-ideagen"
        
        # Skill location for agent discovery
        self.skill_location = Path(__file__).parent.parent / "SKILL.md"
    
    def generate_ideas_stream(
        self, 
        topic: str, 
        num_ideas: int = 5, 
        context: str = "",
        creativity: float = 0.7
    ) -> Generator[str, None, None]:
        """
        Generate ideas with streaming output (recommended for UX)
        
        Args:
            topic: The topic to generate ideas about
            num_ideas: Number of ideas to generate (1-10)
            context: Additional context or constraints
            creativity: Temperature setting (0-1, higher = more creative)
        
        Yields:
            Streamed text chunks
        """
        if not topic or not topic.strip():
            yield "❌ Error: Topic cannot be empty. Please provide a topic to generate ideas about."
            return
        
        if not 1 <= num_ideas <= 10:
            yield f"❌ Error: num_ideas must be between 1 and 10, got {num_ideas}"
            return
        
        # Build prompts with skill awareness
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(topic, num_ideas, context)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            # Stream the response
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=creativity,
                top_p=0.95,
                max_tokens=4096,
                frequency_penalty=0.2,
                presence_penalty=0.1,
                stream=True
            )
            
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        
        except Exception as e:
            yield f"\n\n❌ Error generating ideas: {str(e)}\n\nPlease try again or check your API key."
    
    def generate_ideas(
        self, 
        topic: str, 
        num_ideas: int = 5, 
        context: str = "",
        creativity: float = 0.7
    ) -> str:
        """Generate ideas (non-streaming version)"""
        result = ""
        for chunk in self.generate_ideas_stream(topic, num_ideas, context, creativity):
            result += chunk
        return result
    
    def generate_ideas_batch(
        self,
        topic: str,
        num_ideas: int = 5,
        context: str = "",
        creativity: float = 0.7,
        use_parallel: bool = True,
        max_workers: Optional[int] = None
    ) -> List[str]:
        """
        Generate multiple ideas in parallel using ThreadPoolExecutor (better for I/O-bound API calls)
        
        This method is optimized for batch operations when generating many ideas.
        It uses ThreadPoolExecutor for I/O-bound API calls, which is faster than
        multiprocessing for network requests and works better in subprocess contexts.
        
        Args:
            topic: The topic to generate ideas about
            num_ideas: Number of ideas to generate (1-50)
            context: Additional context or constraints
            creativity: Temperature setting (0-1)
            use_parallel: Whether to use parallel processing (default: True)
            max_workers: Maximum number of worker threads (default: min(4, num_ideas))
        
        Returns:
            List of individual idea strings
        """
        if not topic or not topic.strip():
            return ["❌ Error: Topic cannot be empty. Please provide a topic to generate ideas about."]
        
        if not 1 <= num_ideas <= 50:
            return [f"❌ Error: num_ideas must be between 1 and 50, got {num_ideas}"]
        
        # For small batches (<= 8 ideas), always use single API call (fastest)
        # Threading overhead not worth it for small batches
        if num_ideas <= 8 or not use_parallel:
            ideas_text = self.generate_ideas(topic, num_ideas, context, creativity)
            # Split into individual ideas
            return self._parse_ideas_from_text(ideas_text)
        
        # For larger batches, use threading (better for I/O-bound API calls)
        # However, for small batches (5-10 ideas), it's often faster to make a single API call
        # Only use threading for larger batches (10+ ideas) where the parallelization overhead is worth it
        if num_ideas >= 10:
            # Use fewer workers to avoid overwhelming the API
            if max_workers is None:
                max_workers = min(4, num_ideas)  # Limit to 4 workers max for API calls
            
            # Calculate ideas per worker
            ideas_per_worker = max(1, num_ideas // max_workers)
            remaining_ideas = num_ideas % max_workers
            
            # Create work items - each worker generates multiple ideas
            work_items = []
            for i in range(max_workers):
                worker_ideas = ideas_per_worker
                if i < remaining_ideas:
                    worker_ideas += 1
                if worker_ideas > 0:
                    work_items.append((topic, worker_ideas, context, creativity))
            
            # Process in parallel using threading (better for I/O-bound operations)
            try:
                # Debug: Print threading info (only in non-JSON mode to avoid breaking output)
                if not os.getenv('SKILL_JSON_MODE'):
                    print(f"🔄 Using threading: {len(work_items)} workers, {max_workers} max threads", file=sys.stderr)
                
                start_time = time.time()
                all_ideas = []
                
                # Use ThreadPoolExecutor for I/O-bound API calls
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all tasks
                    future_to_worker = {}
                    for i, work_item in enumerate(work_items):
                        work_topic, work_ideas, work_context, work_creativity = work_item
                        future = executor.submit(
                            self._generate_ideas_worker_thread,
                            work_topic, work_ideas, work_context, work_creativity
                        )
                        future_to_worker[future] = (i, work_ideas)
                    
                    # Collect results as they complete
                    for future in as_completed(future_to_worker):
                        try:
                            worker_ideas_list = future.result()
                            all_ideas.extend(worker_ideas_list)
                        except Exception as e:
                            if not os.getenv('SKILL_JSON_MODE'):
                                print(f"⚠️  Worker failed: {e}", file=sys.stderr)
                            # Continue with other workers
                
                elapsed = time.time() - start_time
                
                # Debug: Print timing (only in non-JSON mode)
                if not os.getenv('SKILL_JSON_MODE'):
                    print(f"⚡ Threading completed in {elapsed:.2f}s with {len(work_items)} parallel workers", file=sys.stderr)
                
                return all_ideas[:num_ideas]  # Ensure we don't exceed requested count
            except Exception as e:
                # Fallback to single process on error
                if not os.getenv('SKILL_JSON_MODE'):
                    print(f"⚠️  Threading failed, falling back to single process: {e}", file=sys.stderr)
                ideas_text = self.generate_ideas(topic, num_ideas, context, creativity)
                return self._parse_ideas_from_text(ideas_text)
        else:
            # This should never be reached due to the check above, but keep for safety
            # For smaller batches (4-9 ideas), use single API call (faster than threading overhead)
            # The API can generate multiple ideas efficiently in one call
            ideas_text = self.generate_ideas(topic, num_ideas, context, creativity)
            return self._parse_ideas_from_text(ideas_text)
    
    def _generate_ideas_worker_thread(
        self,
        topic: str,
        num_ideas: int,
        context: str,
        creativity: float
    ) -> List[str]:
        """
        Thread worker function for generating ideas
        This is a method (not static) so it can access self.client
        """
        try:
            # Create a separate client instance for this thread to avoid thread-safety issues
            # OpenAI client is not fully thread-safe for concurrent writes
            thread_client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=self.api_key
            )
            
            # Build prompts
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(topic, num_ideas, context)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Make API call with thread-specific client
            worker_start = time.time()
            completion = thread_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=creativity,
                top_p=0.95,
                max_tokens=4096,
                frequency_penalty=0.2,
                presence_penalty=0.1,
                stream=False
            )
            worker_elapsed = time.time() - worker_start
            
            ideas_text = completion.choices[0].message.content
            
            # Debug output to stderr (won't break JSON)
            if not os.getenv('SKILL_JSON_MODE'):
                print(f"  🔹 Worker generated {num_ideas} idea(s) in {worker_elapsed:.2f}s", file=sys.stderr)
            
            # Parse and return
            return self._parse_ideas_from_text(ideas_text)
        except Exception as e:
            if not os.getenv('SKILL_JSON_MODE'):
                print(f"  ❌ Worker error: {e}", file=sys.stderr)
            return [f"❌ Error generating ideas: {str(e)}"]
    
    def _parse_ideas_from_text(self, ideas_text: str) -> List[str]:
        """
        Parse ideas text into a list of individual ideas
        
        Args:
            ideas_text: Raw text output from LLM
        
        Returns:
            List of individual idea strings
        """
        if not ideas_text:
            return []
        
        ideas_list = []
        current_idea = ""
        
        # Split by common idea markers
        lines = ideas_text.split('\n')
        for line in lines:
            # Check for idea markers
            if (line.strip().startswith('**Idea') or 
                line.strip().startswith('### ') or
                line.strip().startswith('## ') or
                (line.strip() and line.strip()[0].isdigit() and 
                 ('.' in line[:5] or ')' in line[:5]))):
                if current_idea.strip():
                    ideas_list.append(current_idea.strip())
                current_idea = line + '\n'
            else:
                current_idea += line + '\n'
        
        # Add last idea
        if current_idea.strip():
            ideas_list.append(current_idea.strip())
        
        # If no clear separation found, try splitting by double newlines
        if len(ideas_list) <= 1 and '\n\n' in ideas_text:
            ideas_list = [idea.strip() for idea in ideas_text.split('\n\n') if idea.strip()]
        
        return ideas_list if ideas_list else [ideas_text.strip()]
    
    def brainstorm_concepts(
        self,
        domain: str,
        focus_area: str = "",
        constraints: Optional[List[str]] = None
    ) -> Generator[str, None, None]:
        """Brainstorm conceptual ideas for a domain with constraints"""
        if not domain or not domain.strip():
            yield "❌ Error: Domain cannot be empty."
            return
        
        system_prompt = """You are a creative brainstorming assistant. Generate innovative, 
practical, and well-explained concepts. Structure your response with clear numbering and 
detailed explanations for each concept."""
        
        constraints_text = ""
        if constraints:
            constraints_text = "\n\nConstraints/Requirements:\n" + "\n".join(f"- {c}" for c in constraints)
        
        user_prompt = f"""Generate creative concepts for the following:

Domain: {domain}
{f"Focus Area: {focus_area}" if focus_area else ""}
{constraints_text}

Provide 3-5 innovative concepts with:
1. Concept name
2. Brief description (2-3 sentences)
3. Key benefits or unique aspects
4. Implementation considerations

Format each concept clearly and make them actionable."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.8,
                top_p=0.95,
                max_tokens=4096,
                stream=True
            )
            
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        
        except Exception as e:
            yield f"\n\n❌ Error brainstorming: {str(e)}"
    
    def expand_idea(
        self,
        idea: str,
        expansion_type: str = "detailed"
    ) -> Generator[str, None, None]:
        """Expand an existing idea with more details"""
        if not idea or not idea.strip():
            yield "❌ Error: Idea cannot be empty."
            return
        
        expansion_prompts = {
            "detailed": "Provide a comprehensive breakdown with implementation steps, requirements, and considerations.",
            "technical": "Focus on technical architecture, technologies, and implementation details.",
            "creative": "Explore creative variations, alternative approaches, and innovative extensions.",
            "business": "Analyze business value, market potential, stakeholders, and ROI considerations."
        }
        
        expansion_type_lower = expansion_type.lower()
        if expansion_type_lower not in expansion_prompts:
            yield f"❌ Error: Invalid expansion_type '{expansion_type}'. Must be one of: detailed, technical, creative, business"
            return
        
        system_prompt = f"You are an expert idea expansion assistant. {expansion_prompts[expansion_type_lower]}"
        
        user_prompt = f"""Expand the following idea in depth:

{idea}

Provide a thorough expansion covering:
- Core concept elaboration
- Key components and elements
- Practical considerations
- Potential challenges and solutions
- Next steps or action items

Make it comprehensive and actionable."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.5,
                top_p=0.95,
                max_tokens=4096,
                stream=True
            )
            
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        
        except Exception as e:
            yield f"\n\n❌ Error expanding idea: {str(e)}"
    
    def save_ideas(self, topic: str, content: str) -> str:
        """Save generated ideas to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '_')).strip()
        safe_topic = safe_topic.replace(' ', '_')[:50]
        
        filename = f"ideas_{safe_topic}_{timestamp}.md"
        filepath = self.ideas_dir / filename
        
        markdown_content = f"""# Ideas: {topic}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

{content}

---

*Generated using NVIDIA Nemotron Model via Agent Skills*
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return str(filepath)
    
    def list_saved_ideas(self) -> List[Dict[str, str]]:
        """List all saved ideas"""
        ideas_files = sorted(
            self.ideas_dir.glob("ideas_*.md"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        result = []
        for file in ideas_files:
            result.append({
                "filename": file.name,
                "path": str(file),
                "size": file.stat().st_size,
                "modified": datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return result
    
    def get_skill_info(self) -> Dict[str, any]:
        """Get skill metadata and status information"""
        return {
            "name": self.name,
            "version": self.version,
            "model": self.model,
            "capabilities": [
                "generate_multiple_ideas",
                "brainstorm_with_constraints",
                "expand_ideas_detailed",
                "expand_ideas_technical",
                "expand_ideas_creative",
                "expand_ideas_business",
                "save_idea_library",
                "list_saved_ideas",
                "streaming_output"
            ],
            "status": "initialized",
            "api_available": True,
            "ideas_directory": str(self.ideas_dir.absolute()),
            "saved_ideas_count": len(self.list_saved_ideas()),
            "skill_location": str(self.skill_location.absolute()) if self.skill_location.exists() else "not found"
        }
    
    def _build_system_prompt(self) -> str:
        """
        Build the system prompt with Agent Skills awareness
        
        According to https://agentskills.io/integrate-skills, agents should have
        skill metadata injected into their system prompt for skill discovery.
        """
        # Get available skills metadata
        available_skills_xml = self._get_available_skills_xml()
        
        base_prompt = """You are an expert idea generation assistant inspired by advanced brainstorming methodologies. 
Your role is to generate creative, practical, and well-structured ideas. 

Key principles:
- Be innovative yet feasible
- Provide clear explanations
- Consider multiple perspectives
- Include actionable details
- Structure ideas logically

Format your responses with clear numbering and organization."""
        
        # Inject available skills metadata if running in agent context
        if available_skills_xml:
            return f"""{base_prompt}

{available_skills_xml}"""
        
        return base_prompt
    
    def _build_user_prompt(self, topic: str, num_ideas: int, context: str) -> str:
        """Build the user prompt for idea generation"""
        context_text = f"\n\nAdditional Context:\n{context}" if context else ""
        
        return f"""Generate {num_ideas} innovative ideas for the following topic:

**Topic:** {topic}{context_text}

For each idea, provide:
1. **Title:** A catchy, descriptive name
2. **Description:** 2-3 sentence overview
3. **Key Features:** 3-5 main aspects or components
4. **Potential Impact:** Why this idea matters
5. **Next Steps:** Initial actions to explore or implement

Format each idea clearly with numbering and use markdown formatting for readability."""
    
    def _get_available_skills_xml(self) -> str:
        """
        Generate the <available_skills> XML block for agent context injection
        
        This follows the Agent Skills specification:
        https://agentskills.io/integrate-skills#injecting-into-context
        """
        skill_path = Path(__file__).parent.parent
        skill_md = skill_path / "SKILL.md"
        
        if not skill_md.exists():
            return ""
        
        # Parse SKILL.md frontmatter
        try:
            with open(skill_md, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    import yaml
                    try:
                        frontmatter = yaml.safe_load(parts[1])
                        name = frontmatter.get('name', 'nvidia-ideagen')
                        description = frontmatter.get('description', 'AI-powered idea generation skill')
                        
                        return f"""<available_skills>
  <skill>
    <name>{name}</name>
    <description>{description}</description>
    <location>{skill_md.absolute()}</location>
  </skill>
</available_skills>"""
                    except:
                        pass
        except:
            pass
        
        # Fallback if parsing fails
        return f"""<available_skills>
  <skill>
    <name>nvidia-ideagen</name>
    <description>AI-powered idea generation skill using NVIDIA's Nemotron model for brainstorming, concept development, and creative ideation.</description>
    <location>{skill_md.absolute()}</location>
  </skill>
</available_skills>"""


# ============================================================================
# Note: Removed multiprocessing worker functions
# ThreadPoolExecutor uses instance methods directly, no need for static workers
# ============================================================================


# Skill discovery utility for agents
def discover_skills(skill_directories: List[str]) -> List[Dict[str, str]]:
    """
    Discover Agent Skills in specified directories
    
    According to https://agentskills.io/integrate-skills, agents should:
    1. Scan configured directories for SKILL.md files
    2. Parse only the frontmatter (name and description) at startup
    3. Keep initial context usage low (~50-100 tokens per skill)
    
    Args:
        skill_directories: List of directory paths to scan
    
    Returns:
        List of skill metadata dicts with name, description, and location
    """
    skills = []
    
    for directory in skill_directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            continue
        
        # Find all SKILL.md files
        for skill_md in dir_path.rglob("SKILL.md"):
            try:
                with open(skill_md, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract frontmatter
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        try:
                            import yaml
                            frontmatter = yaml.safe_load(parts[1])
                            
                            skills.append({
                                "name": frontmatter.get('name', 'unknown'),
                                "description": frontmatter.get('description', ''),
                                "location": str(skill_md.absolute()),
                                "path": str(skill_md.parent)
                            })
                        except:
                            pass
            except:
                continue
    
    return skills


def generate_skills_xml(skills: List[Dict[str, str]]) -> str:
    """
    Generate XML for injecting into agent system prompt
    
    Format according to https://agentskills.io/integrate-skills#injecting-into-context
    
    Args:
        skills: List of skill metadata from discover_skills()
    
    Returns:
        XML string formatted for system prompt injection
    """
    if not skills:
        return ""
    
    xml_parts = ["<available_skills>"]
    
    for skill in skills:
        xml_parts.append(f"""  <skill>
    <name>{skill['name']}</name>
    <description>{skill['description']}</description>
    <location>{skill['location']}</location>
  </skill>""")
    
    xml_parts.append("</available_skills>")
    
    return "\n".join(xml_parts)


# ============================================================================
# NAT Auto-Discovery Tool Functions
# These @skill_tool decorated functions are auto-discovered by the skill loader
# ============================================================================

# Global skill instance for tool functions
_global_skill_instance = None

def _get_skill_instance():
    """Get or create the global skill instance"""
    global _global_skill_instance
    if _global_skill_instance is None:
        api_key = os.getenv("NVIDIA_API_KEY")
        try:
            _global_skill_instance = NvidiaIdeaGenSkill(api_key=api_key)
        except ValueError as e:
            # API key not set - return None
            print(f"Warning: {str(e)}")
            return None
    return _global_skill_instance


@skill_tool(
    name="generate_ideas",
    description="Generate creative ideas on a topic. Returns a formatted string with numbered ideas. Automatically optimizes: single API call for <=8 ideas (fastest), ThreadPoolExecutor for 10+ ideas (parallel processing).",
    return_direct=False
)
def generate_ideas(
    topic: str,
    num_ideas: int = 5,
    context: str = "",
    creativity: float = 0.7,
    use_parallel: Optional[bool] = None
) -> str:
    """
    Generate creative ideas on any topic
    
    This function automatically chooses the fastest method:
    - For <= 8 ideas: Single API call (fastest, no overhead)
    - For 10+ ideas: ThreadPoolExecutor parallel processing (faster for large batches)
    
    Args:
        topic: The topic to generate ideas about (required)
        num_ideas: Number of ideas to generate, 1-50 (default: 5)
        context: Additional context or constraints (optional)
        creativity: Creativity level 0.0-1.0, higher is more creative (default: 0.7)
        use_parallel: Optional override (None = auto-detect based on num_ideas)
    
    Returns:
        String with formatted ideas
    
    Examples:
        >>> generate_ideas("sustainable urban transportation", num_ideas=3)  # Single call
        >>> generate_ideas("mobile apps", context="for remote workers", creativity=0.8)  # Single call
        >>> generate_ideas("AI applications", num_ideas=15)  # Auto-uses ThreadPoolExecutor
    """
    skill = _get_skill_instance()
    if skill is None:
        return "❌ Error: NVIDIA_API_KEY not set. Get your key at https://build.nvidia.com/"
    
    # Auto-optimize execution method:
    # - For <= 8 ideas: Always use single API call (fastest, no overhead)
    # - For 10+ ideas: Use ThreadPoolExecutor if use_parallel is True or None
    # - For 9 ideas: Use single call (edge case, threading overhead not worth it)
    
    # Force single API call for small batches regardless of use_parallel parameter
    if num_ideas < 10:
        return skill.generate_ideas(topic, num_ideas, context, creativity)
    
    # For 10+ ideas, check if parallel processing should be used
    if num_ideas >= 10 and (use_parallel is True or use_parallel is None):
        # Use batch processing for large batches (10+ ideas)
        ideas_list = skill.generate_ideas_batch(
            topic, num_ideas, context, creativity, use_parallel=True
        )
        # Combine into formatted string
        return "\n\n".join(f"**Idea {i+1}:**\n{idea}" for i, idea in enumerate(ideas_list))
    else:
        # Single API call - fastest for <= 8 ideas (and forced for 9 ideas to avoid edge case)
        return skill.generate_ideas(topic, num_ideas, context, creativity)


@skill_tool(
    name="brainstorm_concepts",
    description="Brainstorm concepts for a domain with specific focus and constraints. More structured than generate_ideas.",
    return_direct=False
)
def brainstorm_concepts(
    domain: str,
    focus_area: str = "",
    constraints: Optional[List[str]] = None
) -> str:
    """
    Brainstorm domain-specific concepts with constraints
    
    Args:
        domain: Domain or field for brainstorming (e.g., "Healthcare Technology")
        focus_area: Specific area within domain (optional, e.g., "patient monitoring")
        constraints: List of requirements or constraints (optional)
    
    Returns:
        String with structured brainstorming output
    
    Examples:
        >>> brainstorm_concepts("Education Technology", "elementary math")
        >>> brainstorm_concepts("Healthcare", "remote care", ["must work offline", "low cost"])
    """
    skill = _get_skill_instance()
    if skill is None:
        return "❌ Error: NVIDIA_API_KEY not set. Get your key at https://build.nvidia.com/"
    
    result = ""
    for chunk in skill.brainstorm_concepts(domain, focus_area, constraints or []):
        result += chunk
    return result


@skill_tool(
    name="expand_idea_detailed",
    description="Expand an idea with comprehensive details including implementation steps, requirements, and challenges.",
    return_direct=False
)
def expand_idea_detailed(idea: str) -> str:
    """
    Expand an idea with detailed analysis
    
    Args:
        idea: The idea to expand (1-3 sentences describing the core concept)
    
    Returns:
        String with comprehensive expansion including implementation details
    
    Example:
        >>> expand_idea_detailed("A mobile app that gamifies recycling by giving points for scanned items")
    """
    skill = _get_skill_instance()
    if skill is None:
        return "❌ Error: NVIDIA_API_KEY not set. Get your key at https://build.nvidia.com/"
    
    result = ""
    for chunk in skill.expand_idea(idea, expansion_type="detailed"):
        result += chunk
    return result


@skill_tool(
    name="expand_idea_technical",
    description="Expand an idea from a technical perspective with architecture, technologies, and implementation details.",
    return_direct=False
)
def expand_idea_technical(idea: str) -> str:
    """
    Expand an idea with technical analysis
    
    Args:
        idea: The idea to expand with technical details
    
    Returns:
        String with technical architecture, stack, and implementation approach
    
    Example:
        >>> expand_idea_technical("An AI-powered platform for personalized learning paths")
    """
    skill = _get_skill_instance()
    if skill is None:
        return "❌ Error: NVIDIA_API_KEY not set. Get your key at https://build.nvidia.com/"
    
    result = ""
    for chunk in skill.expand_idea(idea, expansion_type="technical"):
        result += chunk
    return result


@skill_tool(
    name="expand_idea_business",
    description="Expand an idea from a business perspective with market analysis, revenue models, and ROI.",
    return_direct=False
)
def expand_idea_business(idea: str) -> str:
    """
    Expand an idea with business analysis
    
    Args:
        idea: The idea to expand with business analysis
    
    Returns:
        String with market opportunity, business model, competitive analysis, and financials
    
    Example:
        >>> expand_idea_business("A subscription service for curated local experiences")
    """
    skill = _get_skill_instance()
    if skill is None:
        return "❌ Error: NVIDIA_API_KEY not set. Get your key at https://build.nvidia.com/"
    
    result = ""
    for chunk in skill.expand_idea(idea, expansion_type="business"):
        result += chunk
    return result


@skill_tool(
    name="expand_idea_creative",
    description="Expand an idea creatively with variations, alternatives, and innovative extensions.",
    return_direct=False
)
def expand_idea_creative(idea: str) -> str:
    """
    Expand an idea with creative variations
    
    Args:
        idea: The idea to expand creatively
    
    Returns:
        String with creative variations, alternative approaches, and innovative extensions
    
    Example:
        >>> expand_idea_creative("A social network for book lovers")
    """
    skill = _get_skill_instance()
    if skill is None:
        return "❌ Error: NVIDIA_API_KEY not set. Get your key at https://build.nvidia.com/"
    
    result = ""
    for chunk in skill.expand_idea(idea, expansion_type="creative"):
        result += chunk
    return result


@skill_tool(
    name="save_generated_ideas",
    description="Save generated ideas to a markdown file in the ideas/ directory.",
    return_direct=False
)
def save_generated_ideas(topic: str, ideas_content: str) -> Dict[str, Any]:
    """
    Save ideas to file for later reference
    
    Args:
        topic: Topic of the ideas (used for filename)
        ideas_content: The ideas text to save
    
    Returns:
        Dictionary with file path and success status
    
    Example:
        >>> ideas = generate_ideas("AI applications", 5)
        >>> save_generated_ideas("AI applications", ideas)
    """
    skill = _get_skill_instance()
    if skill is None:
        return {
            "error": "NVIDIA_API_KEY not set. Get your key at https://build.nvidia.com/",
            "success": False
        }
    
    try:
        filepath = skill.save_ideas(topic, ideas_content)
        return {
            "success": True,
            "file_path": filepath,
            "message": f"✅ Ideas saved to: {filepath}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error saving ideas: {str(e)}"
        }


@skill_tool(
    name="list_saved_ideas",
    description="List all previously saved idea files with metadata.",
    return_direct=False
)
def list_saved_ideas() -> Dict[str, Any]:
    """
    List all saved ideas in the ideas/ directory
    
    Returns:
        Dictionary with list of saved idea files and metadata
    
    Example:
        >>> list_saved_ideas()
    """
    skill = _get_skill_instance()
    if skill is None:
        return {
            "error": "Skill not initialized",
            "ideas": []
        }
    
    try:
        ideas_list = skill.list_saved_ideas()
        return {
            "success": True,
            "count": len(ideas_list),
            "ideas": ideas_list
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error listing ideas: {str(e)}",
            "ideas": []
        }


@skill_tool(
    name="get_ideagen_skill_info",
    description="Get information about the idea generation skill capabilities and status",
    return_direct=False
)
def get_ideagen_skill_info() -> Dict[str, Any]:
    """
    Get metadata about the NVIDIA idea generation skill
    
    Returns:
        Dictionary with skill information including capabilities, model, and configuration
    """
    skill = _get_skill_instance()
    if skill is None:
        return {
            "error": "Skill not initialized - NVIDIA_API_KEY not set",
            "name": "nvidia-ideagen",
            "status": "not_initialized"
        }
    
    return skill.get_skill_info()


# Convenience function
def generate_ideas_quick(topic: str, num_ideas: int = 5, api_key: Optional[str] = None) -> str:
    """Quick function to generate ideas without initializing skill object"""
    skill = NvidiaIdeaGenSkill(api_key=api_key)
    return skill.generate_ideas(topic, num_ideas)


# Main execution - supports both CLI JSON mode and example usage
if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='NVIDIA Idea Generation Skill')
    parser.add_argument('--json', action='store_true',
                       help='JSON mode for subprocess execution')
    parser.add_argument('--example', action='store_true',
                       help='Run example usage')
    
    args = parser.parse_args()
    
    if args.json:
        # JSON CLI mode for subprocess execution
        try:
            # Read JSON input from stdin
            input_data = json.loads(sys.stdin.read())
            command = input_data.get('command', '')
            parameters = input_data.get('parameters', {})
            
            # Initialize skill
            api_key = parameters.get('api_key') or os.getenv('NVIDIA_API_KEY')
            skill = NvidiaIdeaGenSkill(api_key=api_key)
            
            # Execute command
            if command == 'generate_ideas':
                topic = parameters.get('topic', '')
                num_ideas = parameters.get('num_ideas', 5)
                creativity = parameters.get('creativity', 0.7)
                context = parameters.get('context', '')
                # Backward compatibility: support both old and new parameter names
                use_parallel = parameters.get('use_parallel', 
                                            parameters.get('use_multiprocessing', True))
                
                # Set JSON mode flag for subprocess execution
                os.environ['SKILL_JSON_MODE'] = '1'
                
                # Auto-optimize execution method based on num_ideas
                # Single API call is fastest for <= 8 ideas (no threading overhead)
                # ThreadPoolExecutor only beneficial for 10+ ideas
                if num_ideas >= 10 and use_parallel:
                    # Generate ideas in parallel using ThreadPoolExecutor for large batches
                    batch_start = time.time()
                    ideas_list = skill.generate_ideas_batch(
                        topic, num_ideas, context, creativity, 
                        use_parallel=True
                    )
                    batch_time = time.time() - batch_start
                    # Combine into formatted text
                    ideas_text = "\n\n".join(f"**Idea {i+1}:**\n{idea}" for i, idea in enumerate(ideas_list))
                else:
                    # Single API call - fastest for <= 8 ideas
                    # This avoids threading overhead which slows down small batches
                    ideas_text = skill.generate_ideas(topic, num_ideas, context, creativity)
                    # Parse ideas into list
                    ideas_list = skill._parse_ideas_from_text(ideas_text)
                
                output = {
                    'success': True,
                    'ideas': ideas_list,
                    'raw_text': ideas_text,
                    'count': len(ideas_list),
                    'batch_processed': num_ideas >= 10 and use_parallel,
                    'execution_method': 'ThreadPoolExecutor' if (num_ideas >= 10 and use_parallel) else 'sequential'
                }
                
                print(json.dumps(output))
            
            elif command == 'brainstorm_concepts':
                domain = parameters.get('domain', '')
                focus_area = parameters.get('focus_area', '')
                constraints = parameters.get('constraints', [])
                
                result = ""
                for chunk in skill.brainstorm_concepts(domain, focus_area, constraints):
                    result += chunk
                
                output = {
                    'success': True,
                    'result': result
                }
                
                print(json.dumps(output))
            
            elif command == 'expand_idea':
                idea = parameters.get('idea', '')
                expansion_type = parameters.get('expansion_type', 'detailed')
                
                result = ""
                for chunk in skill.expand_idea(idea, expansion_type):
                    result += chunk
                
                output = {
                    'success': True,
                    'expansion': result
                }
                
                print(json.dumps(output))
            
            else:
                output = {
                    'success': False,
                    'error': f"Unknown command: {command}"
                }
                print(json.dumps(output))
                sys.exit(1)
        
        except Exception as e:
            output = {
                'success': False,
                'error': str(e)
            }
            print(json.dumps(output))
            sys.exit(1)
    
    else:
        # Default: Run example usage
        print("\n" + "="*60)
        print("NVIDIA Idea Generation Skill - Agent Skills API Compliant")
        print("="*60 + "\n")
        
        # Demonstrate skill discovery
        print("🔍 Discovering skills...")
        current_dir = Path(__file__).parent.parent
        skills = discover_skills([str(current_dir)])
        
        if skills:
            print(f"✅ Found {len(skills)} skill(s):\n")
            for skill in skills:
                print(f"  - {skill['name']}: {skill['description'][:80]}...")
                print(f"    Location: {skill['location']}\n")
            
            print("📝 Generated XML for agent prompt:")
            print(generate_skills_xml(skills))
            print()
        
        print("="*60 + "\n")
        
        # Check for API key
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            print("❌ Error: NVIDIA_API_KEY environment variable not set")
            print("\nPlease set it using:")
            print("  PowerShell: $env:NVIDIA_API_KEY='your-key-here'")
            print("  CMD:        set NVIDIA_API_KEY=your-key-here")
            print("  Linux/Mac:  export NVIDIA_API_KEY='your-key-here'")
            print("\nGet your key at: https://build.nvidia.com/")
            exit(1)
        
        # Initialize and test skill
        try:
            skill = NvidiaIdeaGenSkill()
            print("✅ Skill initialized successfully\n")
            
            # Show skill info
            info = skill.get_skill_info()
            print("📊 Skill Information:")
            print(json.dumps(info, indent=2))
            print("\n" + "="*60 + "\n")
            
            # Test idea generation
            print("🧪 Testing idea generation...")
            print("Topic: Sustainable urban living")
            print("Number of ideas: 2")
            print("\n" + "-"*60 + "\n")
            
            for chunk in skill.generate_ideas_stream(
                topic="sustainable urban living solutions",
                num_ideas=2,
                creativity=0.7
            ):
                print(chunk, end="", flush=True)
            
            print("\n" + "-"*60 + "\n")
            print("✅ Test completed successfully!")
            print("\n" + "="*60 + "\n")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            exit(1)

