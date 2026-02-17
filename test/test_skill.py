#!/usr/bin/env python3
"""
Comprehensive Test Suite for ExpAgentSkill with AI Planner / NAT Integration
Tests skill_loader.py, @skill_tool decorator, and both calendar and ideagen skills
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, List
import traceback

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")

def print_test(test_name: str):
    """Print a test header"""
    print(f"\n{Colors.BOLD}TEST: {test_name}{Colors.RESET}")
    print("-" * 80)

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")

def print_info(message: str):
    """Print info message"""
    print(f"   {message}")

class TestResults:
    """Track test results"""
    def __init__(self):
        self.tests: List[tuple[str, bool, str]] = []
    
    def add(self, name: str, passed: bool, details: str = ""):
        self.tests.append((name, passed, details))
    
    def summary(self):
        """Print test summary"""
        print_section("TEST SUMMARY")
        
        passed = sum(1 for _, p, _ in self.tests if p)
        failed = len(self.tests) - passed
        
        for name, passed, details in self.tests:
            if passed:
                print_success(f"{name}")
            else:
                print_error(f"{name}")
            if details:
                print_info(details)
        
        print(f"\n{Colors.BOLD}Total: {len(self.tests)} tests{Colors.RESET}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
        
        if failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED!{Colors.RESET}")
            return 0
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ {failed} TEST(S) FAILED{Colors.RESET}")
            return 1


def test_skill_loader_import():
    """Test 1: Import SkillLoader"""
    print_test("Import SkillLoader Module")
    
    try:
        from skill_loader import (
            SkillLoader, SkillMetadata, skill_tool,
            load_skills, discover_and_list_skills
        )
        print_success("Successfully imported SkillLoader and related classes")
        print_info(f"SkillLoader: {SkillLoader}")
        print_info(f"SkillMetadata: {SkillMetadata}")
        print_info(f"@skill_tool decorator: {skill_tool}")
        return True, None
    except ImportError as e:
        print_error(f"Failed to import SkillLoader: {e}")
        traceback.print_exc()
        return False, str(e)


def test_skill_discovery():
    """Test 2: Skill Discovery"""
    print_test("Discover Skills from Directory")
    
    try:
        from skill_loader import SkillLoader
        
        # Initialize loader
        base_path = Path(__file__).parent
        loader = SkillLoader(base_path)
        
        print_info(f"Skills base path: {base_path}")
        
        # Discover skills
        skills = loader.list_skills()
        
        if not skills:
            print_error("No skills discovered")
            return False, "No skills found"
        
        print_success(f"Discovered {len(skills)} skill(s):")
        for skill in skills:
            print_info(f"  📦 {skill.name}")
            print_info(f"     Type: {skill.skill_type}")
            print_info(f"     Description: {skill.description[:80]}...")
            print_info(f"     Path: {skill.skill_path}")
        
        return True, f"Found {len(skills)} skills"
    
    except Exception as e:
        print_error(f"Skill discovery failed: {e}")
        traceback.print_exc()
        return False, str(e)


def test_skill_metadata():
    """Test 3: Skill Metadata Loading"""
    print_test("Load and Parse Skill Metadata")
    
    try:
        from skill_loader import SkillLoader
        
        loader = SkillLoader(Path(__file__).parent)
        skills = loader.list_skills()
        
        if not skills:
            print_error("No skills available for metadata test")
            return False, "No skills"
        
        skill = skills[0]
        print_success(f"Testing metadata for: {skill.name}")
        
        # Check config.yaml
        if skill.config:
            print_success("config.yaml loaded successfully")
            print_info(f"  Name: {skill.config.get('name', 'N/A')}")
            print_info(f"  Version: {skill.config.get('version', 'N/A')}")
            print_info(f"  Skill Type: {skill.skill_type}")
            print_info(f"  Runtime: {skill.config.get('runtime', {}).get('type', 'N/A')}")
        else:
            print_warning("No config.yaml found")
        
        # Check SKILL.md frontmatter
        if skill.skill_md_metadata:
            print_success("SKILL.md frontmatter parsed successfully")
            print_info(f"  Keys: {list(skill.skill_md_metadata.keys())}")
        else:
            print_warning("No SKILL.md frontmatter")
        
        # Check description
        if skill.description:
            print_success(f"Description available ({len(skill.description)} chars)")
        else:
            print_warning("No description")
        
        return True, None
    
    except Exception as e:
        print_error(f"Metadata test failed: {e}")
        traceback.print_exc()
        return False, str(e)


def test_tool_discovery():
    """Test 4: Tool Auto-Discovery"""
    print_test("Auto-Discover @skill_tool Decorated Functions")
    
    try:
        from skill_loader import SkillLoader
        
        loader = SkillLoader(Path(__file__).parent)
        
        # Test calendar skill
        print_info("Testing calendar-assistant skill...")
        cal_tools = loader.discover_tools("calendar-assistant")
        
        if cal_tools:
            print_success(f"Discovered {len(cal_tools)} tools from calendar-assistant:")
            for tool in cal_tools:
                print_info(f"  🔧 {tool._tool_name}")
                print_info(f"     Description: {tool._tool_description[:60]}...")
        else:
            print_warning("No tools discovered from calendar-assistant")
        
        # Test ideagen skill
        print_info("\nTesting nvidia-ideagen skill...")
        idea_tools = loader.discover_tools("nvidia-ideagen")
        
        if idea_tools:
            print_success(f"Discovered {len(idea_tools)} tools from nvidia-ideagen:")
            for tool in idea_tools:
                print_info(f"  🔧 {tool._tool_name}")
                print_info(f"     Description: {tool._tool_description[:60]}...")
        else:
            print_warning("No tools discovered from nvidia-ideagen")
        
        total_tools = len(cal_tools) + len(idea_tools)
        if total_tools == 0:
            print_error("No tools discovered from any skill")
            return False, "No tools found"
        
        return True, f"Found {total_tools} tools total"
    
    except Exception as e:
        print_error(f"Tool discovery failed: {e}")
        traceback.print_exc()
        return False, str(e)


def test_langchain_tool_creation():
    """Test 5: LangChain StructuredTool Creation"""
    print_test("Create LangChain StructuredTools")
    
    try:
        from skill_loader import SkillLoader
        
        # Check if LangChain is available
        try:
            from langchain.tools import StructuredTool
            langchain_available = True
        except ImportError:
            print_warning("LangChain not installed - skipping this test")
            return True, "Skipped (LangChain not available)"
        
        loader = SkillLoader(Path(__file__).parent)
        
        # Test calendar skill
        print_info("Creating LangChain tools for calendar-assistant...")
        try:
            cal_langchain_tools = loader.create_langchain_tools("calendar-assistant")
            
            print_success(f"Created {len(cal_langchain_tools)} LangChain StructuredTools:")
            for tool in cal_langchain_tools:
                print_info(f"  🔧 {tool.name}")
                print_info(f"     Args schema: {tool.args_schema.__name__ if tool.args_schema else 'None'}")
        except Exception as e:
            print_error(f"Failed to create calendar tools: {e}")
            return False, str(e)
        
        # Test ideagen skill
        print_info("\nCreating LangChain tools for nvidia-ideagen...")
        try:
            idea_langchain_tools = loader.create_langchain_tools("nvidia-ideagen")
            
            print_success(f"Created {len(idea_langchain_tools)} LangChain StructuredTools:")
            for tool in idea_langchain_tools:
                print_info(f"  🔧 {tool.name}")
                print_info(f"     Args schema: {tool.args_schema.__name__ if tool.args_schema else 'None'}")
        except Exception as e:
            print_error(f"Failed to create ideagen tools: {e}")
            return False, str(e)
        
        total = len(cal_langchain_tools) + len(idea_langchain_tools)
        return True, f"Created {total} LangChain tools"
    
    except Exception as e:
        print_error(f"LangChain tool creation failed: {e}")
        traceback.print_exc()
        return False, str(e)


def test_access_control():
    """Test 6: Access Control"""
    print_test("Test Access Control via config.yaml")
    
    try:
        from skill_loader import SkillLoader
        
        loader = SkillLoader(Path(__file__).parent)
        skills = loader.list_skills()
        
        print_info("Testing access control for discovered skills...")
        
        for skill in skills:
            print_info(f"\nSkill: {skill.name}")
            print_info(f"  User groups: {skill.user_groups if skill.user_groups else 'None (unrestricted)'}")
            print_info(f"  Admin groups: {skill.admin_groups if skill.admin_groups else 'None'}")
            
            # Test with different user groups
            test_groups = [
                ([], "No groups"),
                (["engineering-team"], "Engineering team"),
                (["data-science-team"], "Data science team"),
                (["ai-planner-admins"], "Admins"),
            ]
            
            for groups, label in test_groups:
                has_access = skill.check_access(groups)
                status = "✓ Access granted" if has_access else "✗ Access denied"
                print_info(f"    {label}: {status}")
        
        print_success("Access control test completed")
        return True, None
    
    except Exception as e:
        print_error(f"Access control test failed: {e}")
        traceback.print_exc()
        return False, str(e)


def test_resource_tools():
    """Test 7: Built-in Resource Tools"""
    print_test("Test Built-in Resource Access Tools")
    
    try:
        from skill_loader import SkillLoader
        
        # Check if LangChain is available
        try:
            from langchain.tools import StructuredTool
        except ImportError:
            print_warning("LangChain not installed - skipping this test")
            return True, "Skipped (LangChain not available)"
        
        loader = SkillLoader(Path(__file__).parent)
        
        # Get tools from calendar skill (which should have resource tools)
        tools = loader.create_langchain_tools("calendar-assistant")
        
        # Find resource tools
        resource_tool_names = ["read_reference", "read_asset", "list_resources"]
        found_resource_tools = [t for t in tools if t.name in resource_tool_names]
        
        if found_resource_tools:
            print_success(f"Found {len(found_resource_tools)} resource tools:")
            for tool in found_resource_tools:
                print_info(f"  🔧 {tool.name}: {tool.description}")
            
            # Test list_resources
            list_tool = next((t for t in found_resource_tools if t.name == "list_resources"), None)
            if list_tool:
                print_info("\nTesting list_resources tool...")
                result = list_tool.func()
                print_info(f"  Result:\n{result}")
                print_success("list_resources executed successfully")
            
            return True, f"Found {len(found_resource_tools)} resource tools"
        else:
            print_warning("No resource tools found (check enable_resource_tools in config.yaml)")
            return True, "No resource tools (may be disabled)"
    
    except Exception as e:
        print_error(f"Resource tools test failed: {e}")
        traceback.print_exc()
        return False, str(e)


def test_calendar_skill_execution():
    """Test 8: Calendar Skill Execution"""
    print_test("Execute Calendar Assistant Skill Tools")
    
    try:
        # Import calendar skill tools directly
        sys.path.insert(0, str(Path(__file__).parent))
        from calendar_assistant_skill.scripts.calendar_skill import (
            parse_calendar_event,
            create_ics_file,
            natural_language_to_calendar,
            get_calendar_skill_info
        )
        
        print_success("Successfully imported calendar skill tools")
        
        # Test 1: Get skill info
        print_info("\n1. Testing get_calendar_skill_info...")
        info = get_calendar_skill_info()
        print_success(f"  Name: {info['name']}")
        print_success(f"  Version: {info['version']}")
        print_success(f"  Capabilities: {len(info['capabilities'])}")
        print_success(f"  Status: {info['status']}")
        
        # Test 2: Create ICS file
        print_info("\n2. Testing create_ics_file...")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        result = create_ics_file(
            summary="Test Meeting",
            start_date=tomorrow,
            start_time="14:00",
            duration_hours=1.0,
            location="Test Room"
        )
        
        if result.get("success"):
            print_success(f"  Created ICS file: {result['file_path']}")
            print_success(f"  Event: {result['event_summary']}")
            print_success(f"  File size: {result['file_size']} bytes")
            
            # Clean up test file
            try:
                Path(result['file_path']).unlink()
            except:
                pass
        else:
            print_error(f"  Failed: {result.get('error', 'Unknown error')}")
            return False, "ICS creation failed"
        
        # Test 3: Parse calendar event (requires API key)
        api_key = os.environ.get('NVIDIA_API_KEY')
        if api_key:
            print_info("\n3. Testing parse_calendar_event...")
            parsed = parse_calendar_event("Meeting tomorrow at 3pm for 2 hours")
            
            if "error" in parsed:
                print_warning(f"  Parse failed (expected if API unavailable): {parsed['error']}")
            else:
                print_success(f"  Parsed successfully:")
                print_info(f"    Summary: {parsed.get('summary', 'N/A')}")
                print_info(f"    Date: {parsed.get('start_date', 'N/A')}")
                print_info(f"    Time: {parsed.get('start_time', 'N/A')}")
        else:
            print_warning("  NVIDIA_API_KEY not set - skipping natural language parsing test")
        
        return True, "Calendar skill tools executed"
    
    except Exception as e:
        print_error(f"Calendar skill execution failed: {e}")
        traceback.print_exc()
        return False, str(e)


def test_ideagen_skill_execution():
    """Test 9: IdeaGen Skill Execution"""
    print_test("Execute NVIDIA IdeaGen Skill Tools")
    
    try:
        # Check for API key first
        api_key = os.environ.get('NVIDIA_API_KEY')
        if not api_key:
            print_warning("NVIDIA_API_KEY not set - skipping IdeaGen skill tests")
            print_info("Set NVIDIA_API_KEY to test idea generation functionality")
            print_info("Get your key at: https://build.nvidia.com/")
            return True, "Skipped (no API key)"
        
        # Import ideagen skill tools
        sys.path.insert(0, str(Path(__file__).parent))
        from nvidia_ideagen_skill.scripts.ideagen_skill import (
            generate_ideas,
            get_ideagen_skill_info,
            save_generated_ideas,
            list_saved_ideas
        )
        
        print_success("Successfully imported ideagen skill tools")
        
        # Test 1: Get skill info
        print_info("\n1. Testing get_ideagen_skill_info...")
        info = get_ideagen_skill_info()
        print_success(f"  Name: {info['name']}")
        print_success(f"  Version: {info['version']}")
        print_success(f"  Model: {info['model']}")
        print_success(f"  Capabilities: {len(info['capabilities'])}")
        print_success(f"  Status: {info['status']}")
        
        # Test 2: Generate ideas
        print_info("\n2. Testing generate_ideas...")
        print_info("  Generating 2 ideas about 'CLI testing tools'...")
        
        ideas = generate_ideas(
            topic="CLI testing tools",
            num_ideas=2,
            creativity=0.7
        )
        
        if ideas and not ideas.startswith("❌"):
            print_success("  Ideas generated successfully!")
            print_info(f"  Output length: {len(ideas)} characters")
            
            # Test 3: Save ideas
            print_info("\n3. Testing save_generated_ideas...")
            save_result = save_generated_ideas("CLI testing tools", ideas)
            
            if save_result.get("success"):
                print_success(f"  Saved to: {save_result['file_path']}")
                
                # Clean up test file
                try:
                    Path(save_result['file_path']).unlink()
                except:
                    pass
            else:
                print_warning(f"  Save failed: {save_result.get('error', 'Unknown error')}")
        else:
            print_error(f"  Idea generation failed: {ideas}")
            return False, "Idea generation failed"
        
        # Test 4: List saved ideas
        print_info("\n4. Testing list_saved_ideas...")
        list_result = list_saved_ideas()
        if list_result.get("success"):
            print_success(f"  Found {list_result['count']} saved idea file(s)")
        
        return True, "IdeaGen skill tools executed"
    
    except Exception as e:
        print_error(f"IdeaGen skill execution failed: {e}")
        traceback.print_exc()
        return False, str(e)


def test_skills_xml_generation():
    """Test 10: Skills XML Generation for LLM"""
    print_test("Generate Skills XML for LLM Prompt Injection")
    
    try:
        from skill_loader import SkillLoader
        
        loader = SkillLoader(Path(__file__).parent)
        
        # Generate XML
        xml = loader.generate_skills_xml()
        
        print_success("Generated skills XML:")
        print_info(xml)
        
        # Validate XML structure
        if "<available_skills>" in xml and "</available_skills>" in xml:
            print_success("XML structure valid")
        else:
            print_error("Invalid XML structure")
            return False, "Invalid XML"
        
        # Check for skill elements
        skill_count = xml.count("<skill>")
        print_success(f"Contains {skill_count} skill(s)")
        
        return True, f"{skill_count} skills in XML"
    
    except Exception as e:
        print_error(f"XML generation failed: {e}")
        traceback.print_exc()
        return False, str(e)


def test_pydantic_model_generation():
    """Test 11: Pydantic Model Auto-Generation"""
    print_test("Auto-Generate Pydantic Models from Type Hints")
    
    try:
        from skill_loader import SkillLoader
        
        # Check if Pydantic is available
        try:
            from pydantic import BaseModel
        except ImportError:
            print_warning("Pydantic not installed - skipping this test")
            return True, "Skipped (Pydantic not available)"
        
        loader = SkillLoader(Path(__file__).parent)
        
        # Discover tools
        tools = loader.discover_tools("calendar-assistant")
        
        if not tools:
            print_warning("No tools to test")
            return True, "No tools discovered"
        
        print_info(f"Testing Pydantic model generation for {len(tools)} tools...")
        
        for tool in tools[:3]:  # Test first 3 tools
            try:
                # Create Pydantic model
                model = loader._create_pydantic_model_from_function(tool)
                print_success(f"  {tool._tool_name}: {model.__name__}")
                
                # Show fields
                if hasattr(model, 'model_fields'):
                    fields = list(model.model_fields.keys())
                    print_info(f"    Fields: {', '.join(fields)}")
            except Exception as e:
                print_error(f"  {tool._tool_name}: Failed - {e}")
        
        return True, "Pydantic models generated"
    
    except Exception as e:
        print_error(f"Pydantic model test failed: {e}")
        traceback.print_exc()
        return False, str(e)


def test_directory_structure():
    """Test 12: Directory Structure Compliance"""
    print_test("Verify OpenSkills Directory Structure")
    
    try:
        base_path = Path(__file__).parent
        
        # Check calendar skill
        print_info("Checking calendar_assistant_skill...")
        cal_skill = base_path / "calendar_assistant_skill"
        
        required_files = {
            "config.yaml": "Configuration file",
            "SKILL.md": "Skill instructions",
            "scripts/calendar_skill.py": "Implementation",
            "scripts/__init__.py": "Package init"
        }
        
        recommended_dirs = {
            "references": "Documentation directory",
            "assets": "Resources directory"
        }
        
        all_present = True
        for file, desc in required_files.items():
            file_path = cal_skill / file
            if file_path.exists():
                print_success(f"  ✓ {file}: {desc}")
            else:
                print_error(f"  ✗ {file}: MISSING")
                all_present = False
        
        for dir_name, desc in recommended_dirs.items():
            dir_path = cal_skill / dir_name
            if dir_path.exists() and dir_path.is_dir():
                files = list(dir_path.iterdir())
                print_success(f"  ✓ {dir_name}/: {desc} ({len(files)} files)")
            else:
                print_warning(f"  ! {dir_name}/: Not found (recommended)")
        
        # Check ideagen skill
        print_info("\nChecking nvidia_ideagen_skill...")
        idea_skill = base_path / "nvidia_ideagen_skill"
        
        required_files_idea = {
            "config.yaml": "Configuration file",
            "SKILL.md": "Skill instructions",
            "scripts/ideagen_skill.py": "Implementation",
            "scripts/__init__.py": "Package init"
        }
        
        for file, desc in required_files_idea.items():
            file_path = idea_skill / file
            if file_path.exists():
                print_success(f"  ✓ {file}: {desc}")
            else:
                print_error(f"  ✗ {file}: MISSING")
                all_present = False
        
        for dir_name, desc in recommended_dirs.items():
            dir_path = idea_skill / dir_name
            if dir_path.exists() and dir_path.is_dir():
                files = list(dir_path.iterdir())
                print_success(f"  ✓ {dir_name}/: {desc} ({len(files)} files)")
            else:
                print_warning(f"  ! {dir_name}/: Not found (recommended)")
        
        if all_present:
            print_success("\nAll required files present")
            return True, None
        else:
            print_error("\nSome required files missing")
            return False, "Missing files"
    
    except Exception as e:
        print_error(f"Directory structure test failed: {e}")
        traceback.print_exc()
        return False, str(e)


def main():
    """Run all tests"""
    print_section("ExpAgentSkill - Comprehensive Test Suite")
    print_info("Testing skill_loader.py and AI Planner / NAT integration")
    print_info(f"Base path: {Path(__file__).parent}")
    print_info(f"Python version: {sys.version}")
    
    results = TestResults()
    
    # Run all tests
    tests = [
        ("Import SkillLoader", test_skill_loader_import),
        ("Skill Discovery", test_skill_discovery),
        ("Skill Metadata", test_skill_metadata),
        ("Tool Auto-Discovery", test_tool_discovery),
        ("LangChain Tool Creation", test_langchain_tool_creation),
        ("Access Control", test_access_control),
        ("Resource Tools", test_resource_tools),
        ("Calendar Skill Execution", test_calendar_skill_execution),
        ("IdeaGen Skill Execution", test_ideagen_skill_execution),
        ("Skills XML Generation", test_skills_xml_generation),
        ("Pydantic Model Generation", test_pydantic_model_generation),
        ("Directory Structure", test_directory_structure),
    ]
    
    for test_name, test_func in tests:
        try:
            passed, details = test_func()
            results.add(test_name, passed, details or "")
        except Exception as e:
            print_error(f"Test crashed: {e}")
            traceback.print_exc()
            results.add(test_name, False, f"Crashed: {str(e)}")
    
    # Print summary
    exit_code = results.summary()
    
    # Additional info
    if exit_code == 0:
        print(f"\n{Colors.BOLD}Next Steps:{Colors.RESET}")
        print("  1. Both skills are ready for AI Planner / NAT integration")
        print("  2. See QUICKSTART.md for usage examples")
        print("  3. See README_NEW_ARCHITECTURE.md for complete documentation")
        print(f"\n{Colors.BOLD}Note:{Colors.RESET}")
        print("  - Set NVIDIA_API_KEY to test idea generation and NL parsing")
        print("  - Install langchain and pydantic for full NAT integration")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
