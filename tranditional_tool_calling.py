"""
Skill Loader for AI Planner / NAT Integration
Implements skill discovery, tool auto-discovery, and resource access tools

Based on the OpenSkills directory structure with AI Planner enhancements:
- SKILL.md: Skill instructions and metadata
- config.yaml: Configuration, access control, and agent settings
- scripts/: Implementation with @skill_tool decorated functions
- references/: Documentation and knowledge base files
- assets/: Templates, data files, and resources
"""

import functools
import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, get_type_hints
import yaml

try:
    from pydantic import BaseModel, create_model, Field
    try:
        # Try newer langchain-core first (v0.2+)
        from langchain_core.tools import StructuredTool
    except ImportError:
        # Fall back to older langchain.tools
        from langchain.tools import StructuredTool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseModel = None
    StructuredTool = None


# ============================================================================
# Decorator for Tool Auto-Discovery
# ============================================================================

def skill_tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    return_direct: bool = False
):
    """
    Decorator to mark functions for auto-discovery as agent tools
    
    Usage:
        @skill_tool(
            name="create_calendar_event",
            description="Create an iCalendar event from structured data"
        )
        def create_event(summary: str, start_date: str, duration_hours: float = 1.0) -> bytes:
            '''Create a calendar event'''
            # Implementation
            pass
    
    Args:
        name: Tool name (defaults to function name)
        description: Tool description (defaults to function docstring)
        return_direct: Whether the tool result should be returned directly to user
    
    The decorator:
    1. Marks the function with metadata for discovery
    2. Preserves the original function signature
    3. Enables automatic Pydantic model generation from type hints
    4. Integrates with LangChain StructuredTool for NAT compatibility
    """
    def decorator(func: Callable) -> Callable:
        # Store metadata on the function
        func._is_skill_tool = True
        func._tool_name = name or func.__name__
        func._tool_description = description or (func.__doc__ or "").strip()
        func._tool_return_direct = return_direct
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # Copy metadata to wrapper
        wrapper._is_skill_tool = True
        wrapper._tool_name = func._tool_name
        wrapper._tool_description = func._tool_description
        wrapper._tool_return_direct = func._tool_return_direct
        
        return wrapper
    
    return decorator


# ============================================================================
# Skill Discovery and Loading
# ============================================================================

class SkillMetadata:
    """Container for skill metadata from config.yaml and SKILL.md"""
    
    def __init__(self, skill_path: Path):
        self.skill_path = skill_path
        self.config = self._load_config()
        self.skill_md_metadata, self.skill_md_content = self._load_skill_md()
        # Set name from config, SKILL.md, or fallback to directory name
        self.name = (
            self.config.get('name') or 
            self.skill_md_metadata.get('name') or 
            skill_path.name
        )
        
    def _load_config(self) -> Dict[str, Any]:
        """Load config.yaml"""
        config_path = self.skill_path / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def _load_skill_md(self) -> tuple[Dict[str, Any], str]:
        """Load and parse SKILL.md frontmatter and content"""
        skill_md_path = self.skill_path / "SKILL.md"
        if not skill_md_path.exists():
            return {}, ""
        
        with open(skill_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    metadata = yaml.safe_load(parts[1]) or {}
                    body = parts[2].strip()
                    return metadata, body
                except yaml.YAMLError:
                    pass
        
        return {}, content
    
    @property
    def description(self) -> str:
        """Get skill description for LLM-based routing"""
        return (
            self.config.get("description") or 
            self.skill_md_metadata.get("description") or 
            ""
        )
    
    @property
    def skill_type(self) -> str:
        """Get skill type: 'generic' or 'custom'"""
        return self.config.get("skill_type", "generic")
    
    @property
    def user_groups(self) -> List[str]:
        """Get allowed user groups (empty = no restrictions)"""
        return self.config.get("user_group", [])
    
    @property
    def admin_groups(self) -> List[str]:
        """Get admin groups"""
        return self.config.get("admin_group", [])
    
    def check_access(self, user_groups: List[str]) -> bool:
        """
        Check if user has access to this skill
        
        Args:
            user_groups: List of groups the user belongs to
        
        Returns:
            True if user has access, False otherwise
        """
        # No restrictions = everyone has access
        if not self.user_groups and not self.admin_groups:
            return True
        
        # Check if user is in allowed groups
        user_group_set = set(user_groups)
        allowed_groups = set(self.user_groups + self.admin_groups)
        
        return bool(user_group_set & allowed_groups)


class OldWays:
    """
    Load and manage skills following OpenSkills + AI Planner architecture
    
    Features:
    - Skill discovery from directory structure
    - Tool auto-discovery with @skill_tool decorator
    - Access control via config.yaml
    - Resource access tools (read_reference, read_asset, list_resources)
    - Pydantic model generation from type hints
    - LangChain StructuredTool integration for NAT
    """
    
    def __init__(self, skills_base_path: Path, exclude_skills: Optional[List[str]] = None):
        """
        Initialize the skill loader
        
        Args:
            skills_base_path: Base path containing skill directories
            exclude_skills: Optional list of skill names to exclude from discovery
                           (e.g., ['nvidia_vlm_skill', 'image_generation_skill'])
        """
        self.skills_base_path = Path(skills_base_path)
        self.exclude_skills = set(exclude_skills if exclude_skills is not None else [])
        self.skills: Dict[str, SkillMetadata] = {}
        self.discover_skills()
    
    def discover_skills(self) -> List[SkillMetadata]:
        """
        Discover all skills in the base path (excluding skills in exclude_skills)
        
        Returns:
            List of discovered skill metadata
        """
        self.skills = {}
        
        if not self.skills_base_path.exists():
            return []
        
        # Find all directories with SKILL.md
        for skill_dir in self.skills_base_path.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                metadata = SkillMetadata(skill_dir)
                # Skip excluded skills - check both skill name and directory name
                skill_name = metadata.name
                dir_name = skill_dir.name
                if skill_name not in self.exclude_skills and dir_name not in self.exclude_skills:
                    self.skills[metadata.name] = metadata
        
        return list(self.skills.values())
    
    def get_skill(self, skill_name: str) -> Optional[SkillMetadata]:
        """Get skill metadata by name"""
        return self.skills.get(skill_name)
    
    def list_skills(
        self, 
        user_groups: Optional[List[str]] = None
    ) -> List[SkillMetadata]:
        """
        List all available skills (with optional access control)
        
        Args:
            user_groups: User's group memberships for access control
        
        Returns:
            List of accessible skills
        """
        if user_groups is None:
            return list(self.skills.values())
        
        return [
            skill for skill in self.skills.values()
            if skill.check_access(user_groups)
        ]
    
    def generate_skills_xml(
        self, 
        user_groups: Optional[List[str]] = None
    ) -> str:
        """
        Generate XML for skill selection (for LLM prompt injection)
        
        This is used by the skill selector to match user queries against
        skill descriptions for routing.
        
        Args:
            user_groups: User's group memberships for access control
        
        Returns:
            XML string with available skills
        """
        skills = self.list_skills(user_groups)
        
        if not skills:
            return "<available_skills></available_skills>"
        
        xml_parts = ["<available_skills>"]
        for skill in sorted(skills, key=lambda s: s.name):
            xml_parts.append(f"""  <skill>
    <name>{skill.name}</name>
    <description>{skill.description}</description>
    <location>{skill.skill_path}</location>
  </skill>""")
        xml_parts.append("</available_skills>")
        
        return "\n".join(xml_parts)
    
    def discover_tools(self, skill_name: str) -> List[Callable]:
        """
        Auto-discover @skill_tool decorated functions from a skill's scripts/
        
        Args:
            skill_name: Name of the skill to discover tools from
        
        Returns:
            List of discovered tool functions
        """
        skill = self.get_skill(skill_name)
        if not skill:
            return []
        
        # Check if auto-discovery is enabled
        if not skill.config.get("generic_settings", {}).get("auto_discover_tools", True):
            return []
        
        scripts_dir = skill.skill_path / "scripts"
        if not scripts_dir.exists():
            return []
        
        tools = []
        
        # Scan all Python files in scripts/
        for py_file in scripts_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            # Import the module
            module_name = f"skill_{skill_name}_{py_file.stem}"
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                # Find all @skill_tool decorated functions
                for name, obj in inspect.getmembers(module, inspect.isfunction):
                    if hasattr(obj, '_is_skill_tool') and obj._is_skill_tool:
                        tools.append(obj)
        
        return tools
    
    def create_langchain_tools(
        self, 
        skill_name: str,
        skill_instance: Optional[Any] = None
    ) -> List:
        """
        Create LangChain StructuredTool objects from discovered tools
        
        This generates Pydantic models from function type hints and creates
        StructuredTool instances compatible with NAT agents.
        
        Args:
            skill_name: Name of the skill
            skill_instance: Optional skill instance for method binding
        
        Returns:
            List of LangChain StructuredTool objects
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "langchain and pydantic are required for tool creation. "
                "Install with: pip install langchain pydantic"
            )
        
        discovered_tools = self.discover_tools(skill_name)
        langchain_tools = []
        
        for tool_func in discovered_tools:
            # Generate Pydantic model from type hints
            args_schema = self._create_pydantic_model_from_function(tool_func)
            
            # Bind method to instance if provided
            if skill_instance and not inspect.isfunction(tool_func):
                tool_func = getattr(skill_instance, tool_func.__name__, tool_func)
            
            # Create StructuredTool
            langchain_tool = StructuredTool(
                name=tool_func._tool_name,
                description=tool_func._tool_description,
                func=tool_func,
                args_schema=args_schema,
                return_direct=tool_func._tool_return_direct
            )
            
            langchain_tools.append(langchain_tool)
        
        # Add built-in resource access tools if enabled
        skill = self.get_skill(skill_name)
        if skill and skill.config.get("generic_settings", {}).get("enable_resource_tools", True):
            langchain_tools.extend(self._create_resource_tools(skill))
        
        return langchain_tools
    
    def _create_pydantic_model_from_function(self, func: Callable) -> Type[BaseModel]:
        """
        Generate a Pydantic model from function type hints
        
        Args:
            func: Function with type hints
        
        Returns:
            Pydantic BaseModel class for input validation
        """
        type_hints = get_type_hints(func)
        sig = inspect.signature(func)
        
        # Build field definitions
        fields = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            param_type = type_hints.get(param_name, Any)
            default = param.default if param.default != inspect.Parameter.empty else ...
            
            # Extract description from docstring if available
            description = f"Parameter: {param_name}"
            
            fields[param_name] = (param_type, Field(default=default, description=description))
        
        # Create dynamic Pydantic model
        model_name = f"{func.__name__.title()}Input"
        return create_model(model_name, **fields)
    
    def _create_resource_tools(self, skill: SkillMetadata) -> List:
        """
        Create built-in resource access tools for a skill
        
        Tools:
        - read_reference: Read documentation from references/
        - read_asset: Read data files from assets/
        - list_resources: List available references and assets
        
        Args:
            skill: Skill metadata
        
        Returns:
            List of resource access StructuredTool objects
        """
        if not LANGCHAIN_AVAILABLE:
            return []
        
        skill_path = skill.skill_path
        
        # read_reference tool
        def read_reference(filename: str) -> str:
            """Read a reference document from the references/ directory"""
            ref_path = skill_path / "references" / filename
            if not ref_path.exists():
                return f"Reference file not found: {filename}"
            try:
                return ref_path.read_text(encoding='utf-8')
            except Exception as e:
                return f"Error reading reference: {str(e)}"
        
        # read_asset tool
        def read_asset(filename: str) -> str:
            """Read an asset file from the assets/ directory"""
            asset_path = skill_path / "assets" / filename
            if not asset_path.exists():
                return f"Asset file not found: {filename}"
            try:
                # For text files
                if asset_path.suffix in ['.txt', '.md', '.json', '.yaml', '.yml', '.csv']:
                    return asset_path.read_text(encoding='utf-8')
                else:
                    return f"Asset file (binary): {filename}, size: {asset_path.stat().st_size} bytes"
            except Exception as e:
                return f"Error reading asset: {str(e)}"
        
        # list_resources tool
        def list_resources() -> str:
            """List all available references and assets"""
            result = []
            
            # List references
            ref_dir = skill_path / "references"
            if ref_dir.exists():
                refs = [f.name for f in ref_dir.iterdir() if f.is_file()]
                if refs:
                    result.append("References:")
                    result.extend(f"  - {ref}" for ref in sorted(refs))
            
            # List assets
            asset_dir = skill_path / "assets"
            if asset_dir.exists():
                assets = [f.name for f in asset_dir.iterdir() if f.is_file()]
                if assets:
                    result.append("\nAssets:")
                    result.extend(f"  - {asset}" for asset in sorted(assets))
            
            return "\n".join(result) if result else "No resources available"
        
        # Create StructuredTools
        tools = []
        
        # read_reference tool
        ReadReferenceInput = create_model(
            "ReadReferenceInput",
            filename=(str, Field(description="Name of the reference file to read"))
        )
        tools.append(StructuredTool(
            name="read_reference",
            description="Read a reference document from the skill's references/ directory",
            func=read_reference,
            args_schema=ReadReferenceInput
        ))
        
        # read_asset tool
        ReadAssetInput = create_model(
            "ReadAssetInput",
            filename=(str, Field(description="Name of the asset file to read"))
        )
        tools.append(StructuredTool(
            name="read_asset",
            description="Read an asset file from the skill's assets/ directory",
            func=read_asset,
            args_schema=ReadAssetInput
        ))
        
        # list_resources tool
        ListResourcesInput = create_model("ListResourcesInput")
        tools.append(StructuredTool(
            name="list_resources",
            description="List all available reference documents and asset files",
            func=list_resources,
            args_schema=ListResourcesInput
        ))
        
        return tools


# ============================================================================
# Convenience Functions
# ============================================================================

def load_skills(skills_base_path: str | Path) -> OldWays:
    """
    Convenience function to create a OldWays
    
    Args:
        skills_base_path: Path to directory containing skill folders
    
    Returns:
        Initialized OldWays instance
    """
    return OldWays(Path(skills_base_path))


def discover_and_list_skills(
    skills_base_path: str | Path,
    user_groups: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Discover skills and return as list of dictionaries
    
    Args:
        skills_base_path: Path to skills directory
        user_groups: Optional user groups for access control
    
    Returns:
        List of skill info dictionaries
    """
    loader = OldWays(Path(skills_base_path))
    skills = loader.list_skills(user_groups)
    print("discovered skills: ", skills)
    return [
        {
            "name": skill.name,
            "description": skill.description,
            "skill_type": skill.skill_type,
            "path": str(skill.skill_path),
            "has_access_control": bool(skill.user_groups or skill.admin_groups)
        }
        for skill in skills
    ]


# ============================================================================
# Testing LangChain Tool Integration
# ============================================================================

def test_langchain_tool_loading(skills_base_path: Optional[str | Path] = None):
    """
    Test loading OldWays skills as LangChain StructuredTool objects
    
    This demonstrates how to:
    1. Initialize OldWays loader
    2. Discover skills and tools
    3. Create LangChain StructuredTool objects
    4. Test tool invocation
    
    Args:
        skills_base_path: Path to skills directory (defaults to current directory)
    
    Returns:
        Dict with test results and created tools
    """
    if not LANGCHAIN_AVAILABLE:
        print("❌ LangChain not available. Install with: pip install langchain pydantic")
        return {"success": False, "error": "LangChain not installed"}
    
    # Initialize loader
    base_path = Path(skills_base_path) if skills_base_path else Path(__file__).parent
    loader = OldWays(base_path)
    
    print("\n" + "="*70)
    print("Testing LangChain Tool Loading from OldWays")
    print("="*70 + "\n")
    
    # Discover skills
    skills = loader.list_skills()
    print(f"📦 Discovered {len(skills)} skills")
    
    if not skills:
        print("⚠️  No skills found. Make sure your skills directory contains SKILL.md files.")
        return {"success": False, "error": "No skills found", "tools": []}
    
    # Test each skill's tool loading
    all_tools = []
    results = {}
    
    for skill in skills:
        print(f"\n🔍 Testing skill: {skill.name}")
        print(f"   Description: {skill.description}")
        
        try:
            # Create LangChain tools
            langchain_tools = loader.create_langchain_tools(skill.name)
            
            print(f"   ✅ Created {len(langchain_tools)} LangChain tools:")
            for tool in langchain_tools:
                print(f"      - {tool.name}: {tool.description[:60]}...")
                all_tools.append(tool)
            
            # Test tool invocation with dummy data (if tools exist)
            if langchain_tools:
                # Test the first non-resource tool
                test_tool = None
                for tool in langchain_tools:
                    if not tool.name.startswith("read_") and tool.name != "list_resources":
                        test_tool = tool
                        break
                
                if test_tool:
                    print(f"\n   🧪 Testing tool invocation: {test_tool.name}")
                    try:
                        # Get tool schema
                        schema = test_tool.args_schema.schema() if hasattr(test_tool, 'args_schema') else {}
                        print(f"      Schema: {schema}")
                        
                        # Note: Actual invocation requires proper input parameters
                        print(f"      ℹ️  Tool is ready for invocation (requires proper inputs)")
                        
                    except Exception as e:
                        print(f"      ⚠️  Test invocation info: {str(e)}")
            
            results[skill.name] = {
                "success": True,
                "tools_count": len(langchain_tools),
                "tools": [t.name for t in langchain_tools]
            }
            
        except Exception as e:
            print(f"   ❌ Error creating tools: {str(e)}")
            results[skill.name] = {
                "success": False,
                "error": str(e)
            }
    
    # Summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    print(f"Total skills tested: {len(skills)}")
    print(f"Total tools created: {len(all_tools)}")
    print(f"Successful: {sum(1 for r in results.values() if r.get('success', False))}")
    print(f"Failed: {sum(1 for r in results.values() if not r.get('success', False))}")
    
    # Tool type breakdown
    if all_tools:
        print(f"\nTool Types:")
        resource_tools = [t for t in all_tools if t.name in ['read_reference', 'read_asset', 'list_resources']]
        custom_tools = [t for t in all_tools if t not in resource_tools]
        print(f"  - Resource access tools: {len(resource_tools)}")
        print(f"  - Custom skill tools: {len(custom_tools)}")
    
    print("\n" + "="*70 + "\n")
    
    return {
        "success": True,
        "skills": results,
        "tools": all_tools,
        "total_tools": len(all_tools)
    }


def create_test_agent(skills_base_path: str | Path, llm=None):
    """
    Create a LangChain agent with tools from OldWays
    
    This function demonstrates how to integrate OldWays tools into a
    LangChain agent for actual use.
    
    Args:
        skills_base_path: Path to skills directory
        llm: LangChain LLM instance (optional, for demonstration)
    
    Returns:
        Dictionary with agent components (agent_executor, tools, loader)
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain required. Install with: pip install langchain pydantic")
    
    # Initialize loader
    loader = OldWays(Path(skills_base_path))
    
    # Collect all tools from all skills
    all_tools = []
    skills = loader.list_skills()
    
    for skill in skills:
        try:
            tools = loader.create_langchain_tools(skill.name)
            all_tools.extend(tools)
        except Exception as e:
            print(f"Warning: Could not load tools for {skill.name}: {e}")
    
    if not all_tools:
        print("Warning: No tools were loaded")
    
    # If LLM is provided, create an agent
    agent_executor = None
    if llm:
        try:
            try:
                from langchain.agents import create_tool_calling_agent, AgentExecutor
            except ImportError:
                from langchain_core.agents import create_tool_calling_agent, AgentExecutor
            from langchain_core.prompts import ChatPromptTemplate
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant with access to specialized skills and tools."),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ])
            
            agent = create_tool_calling_agent(llm, all_tools, prompt)
            agent_executor = AgentExecutor(agent=agent, tools=all_tools, verbose=True)
            
            print(f"✅ Created agent with {len(all_tools)} tools")
            
        except ImportError as e:
            print(f"Note: Agent creation requires additional packages: {e}")
    
    return {
        "loader": loader,
        "tools": all_tools,
        "agent_executor": agent_executor,
        "skills": skills
    }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example: Load skills and discover tools
    loader = OldWays(Path(__file__).parent)
    
    print("\n" + "="*60)
    print("Skill Loader - AI Planner / NAT Integration")
    print("="*60 + "\n")
    
    # List discovered skills
    skills = loader.list_skills()
    print(f"✅ Discovered {len(skills)} skills:\n")
    for skill in skills:
        print(f"  📦 {skill.name}")
        print(f"     Description: {skill.description[:80]}...")
        print(f"     Type: {skill.skill_type}")
        print(f"     Path: {skill.skill_path}\n")
    
    # Generate skills XML for LLM
    print("📝 Skills XML for LLM prompt injection:\n")
    print(loader.generate_skills_xml())
    print()
    
    # Discover tools from a skill
    if skills:
        skill_name = skills[0].name
        print(f"🔍 Discovering tools from '{skill_name}'...\n")
        tools = loader.discover_tools(skill_name)
        print(f"✅ Found {len(tools)} tools:\n")
        for tool in tools:
            print(f"  🔧 {tool._tool_name}")
            print(f"     {tool._tool_description}\n")
    
    print("="*60 + "\n")
    
    # Run LangChain tool loading tests
    print("\n" + "="*60)
    print("Running LangChain Integration Tests")
    print("="*60 + "\n")
    
    test_results = test_langchain_tool_loading()
    
    # Optionally demonstrate agent creation
    # Uncomment if you have an LLM configured:
    # from langchain_openai import ChatOpenAI
    # llm = ChatOpenAI(model="gpt-4", temperature=0)
    # agent_components = create_test_agent(Path(__file__).parent, llm)
    # result = agent_components["agent_executor"].invoke({"input": "What can you help me with?"})
    # print(result)
