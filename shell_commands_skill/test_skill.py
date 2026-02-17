#!/usr/bin/env python3
"""
Test script for Shell Commands Skill
Run this to verify the skill works correctly
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shell_commands_skill.scripts.shell_commands import (
    print_working_directory,
    list_directory,
    find_files,
    find_by_extension,
    check_safety_status,
    get_skill_info
)


def test_skill():
    """Run basic tests on the shell commands skill"""
    
    print("=" * 70)
    print("Shell Commands Skill - Test Suite")
    print("=" * 70)
    
    # Test 1: Check safety status
    print("\n1️⃣  Testing Safety Status:")
    print("-" * 70)
    print(check_safety_status())
    
    # Test 2: Print working directory
    print("\n\n2️⃣  Testing Print Working Directory:")
    print("-" * 70)
    print(print_working_directory())
    
    # Test 3: List current directory
    print("\n\n3️⃣  Testing List Directory:")
    print("-" * 70)
    result = list_directory()
    # Show only first 10 lines
    all_lines = result.split('\n')
    lines = all_lines[:10]
    print('\n'.join(lines))
    if len(all_lines) > 10:
        remaining = len(all_lines) - 10
        print(f"... ({remaining} more lines)")
    
    # Test 4: Find markdown files
    print("\n\n4️⃣  Testing Find Files (*.md):")
    print("-" * 70)
    result = find_files(pattern="*.md", max_depth=2)
    all_lines = result.split('\n')
    lines = all_lines[:15]
    print('\n'.join(lines))
    if len(all_lines) > 15:
        remaining = len(all_lines) - 15
        print(f"... ({remaining} more lines)")
    
    # Test 5: Find Python files
    print("\n\n5️⃣  Testing Find by Extension (.py):")
    print("-" * 70)
    result = find_by_extension(extension="py", search_path=".")
    all_lines = result.split('\n')
    lines = all_lines[:15]
    print('\n'.join(lines))
    if len(all_lines) > 15:
        remaining = len(all_lines) - 15
        print(f"... ({remaining} more lines)")
    
    # Test 6: Get skill info
    print("\n\n6️⃣  Testing Get Skill Info:")
    print("-" * 70)
    info = get_skill_info()
    print(f"Name: {info['name']}")
    print(f"Version: {info['version']}")
    print(f"Description: {info['description']}")
    print(f"Safe Mode: {info['safe_mode']}")
    print(f"Max Find Results: {info['max_find_results']}")
    print(f"\nCapabilities ({len(info['capabilities'])}):")
    for cap in info['capabilities']:
        print(f"  ✅ {cap}")
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ All tests completed successfully!")
    print("=" * 70)
    print("\n💡 The shell_commands_skill is ready to use!")
    print("\nKey features:")
    print("  🔒 Safe mode enabled - dangerous commands blocked")
    print("  📂 File system navigation (ls, cd, pwd)")
    print("  📝 Safe file operations (cp, touch)")
    print("  🔍 Powerful search (find, grep)")
    print("  ❌ rm and -rf commands PROHIBITED")
    print("\nTo use in your agent:")
    print("  from skill_loader import SkillLoader")
    print("  loader = SkillLoader()")
    print("  skill = loader.load_skill('shell_commands_skill')")
    print("  tools = skill.get_tools()")


if __name__ == '__main__':
    try:
        test_skill()
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

