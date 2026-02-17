#!/usr/bin/env python3
"""
Test script for text viewing tools (cat, grep, sed, head, tail)

This script demonstrates the new text file viewing and manipulation capabilities.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shell_commands_skill.scripts.shell_commands import (
    cat_file,
    head_file,
    tail_file,
    grep_in_file,
    sed_replace,
    count_lines,
    touch_file,
    change_directory
)


def create_test_file():
    """Create a test file with sample content"""
    print("=" * 60)
    print("Creating test file...")
    print("=" * 60)
    
    # Create test file
    result = touch_file("test_sample.txt")
    print(result)
    
    # Write content to test file
    test_content = """Line 1: This is the first line
Line 2: TODO: Add more features
Line 3: This contains the word ERROR
Line 4: Normal line here
Line 5: Another TODO item
Line 6: FIXME: Bug in this section
Line 7: Regular content
Line 8: More content here
Line 9: Final TODO comment
Line 10: Last line of the file"""
    
    with open("test_sample.txt", "w") as f:
        f.write(test_content)
    
    print("✅ Test file created: test_sample.txt\n")


def test_cat_file():
    """Test cat_file function"""
    print("=" * 60)
    print("TEST 1: cat_file - Display entire file")
    print("=" * 60)
    
    result = cat_file("test_sample.txt")
    print(result)
    print()
    
    print("=" * 60)
    print("TEST 2: cat_file with line numbers")
    print("=" * 60)
    
    result = cat_file("test_sample.txt", show_line_numbers=True)
    print(result)
    print()
    
    print("=" * 60)
    print("TEST 3: cat_file with line range (lines 3-7)")
    print("=" * 60)
    
    result = cat_file("test_sample.txt", start_line=3, end_line=7)
    print(result)
    print()


def test_head_tail():
    """Test head_file and tail_file functions"""
    print("=" * 60)
    print("TEST 4: head_file - First 5 lines")
    print("=" * 60)
    
    result = head_file("test_sample.txt", num_lines=5)
    print(result)
    print()
    
    print("=" * 60)
    print("TEST 5: tail_file - Last 3 lines")
    print("=" * 60)
    
    result = tail_file("test_sample.txt", num_lines=3)
    print(result)
    print()


def test_grep_in_file():
    """Test grep_in_file function"""
    print("=" * 60)
    print("TEST 6: grep_in_file - Search for 'TODO'")
    print("=" * 60)
    
    result = grep_in_file("test_sample.txt", "TODO")
    print(result)
    print()
    
    print("=" * 60)
    print("TEST 7: grep_in_file - Case-insensitive search for 'error'")
    print("=" * 60)
    
    result = grep_in_file("test_sample.txt", "error", case_sensitive=False)
    print(result)
    print()
    
    print("=" * 60)
    print("TEST 8: grep_in_file - Search with context lines")
    print("=" * 60)
    
    result = grep_in_file("test_sample.txt", "FIXME", context_lines=2)
    print(result)
    print()
    
    print("=" * 60)
    print("TEST 9: grep_in_file - Regex search for lines starting with 'Line [5-9]'")
    print("=" * 60)
    
    result = grep_in_file("test_sample.txt", "^Line [5-9]", regex=True)
    print(result)
    print()


def test_sed_replace():
    """Test sed_replace function"""
    print("=" * 60)
    print("TEST 10: sed_replace - Preview replacing 'TODO' with 'DONE'")
    print("=" * 60)
    
    result = sed_replace("test_sample.txt", "TODO", "DONE", preview_only=True)
    print(result)
    print()
    
    print("=" * 60)
    print("TEST 11: sed_replace - Save to new file")
    print("=" * 60)
    
    result = sed_replace(
        "test_sample.txt",
        "TODO",
        "COMPLETED",
        output_file="test_sample_modified.txt",
        preview_only=False
    )
    print(result)
    
    # Show the modified file
    if "Successfully" in result:
        print("\nContents of modified file:")
        print(cat_file("test_sample_modified.txt"))
    print()


def test_count_lines():
    """Test count_lines function"""
    print("=" * 60)
    print("TEST 12: count_lines - Get file statistics")
    print("=" * 60)
    
    result = count_lines("test_sample.txt")
    print(result)
    print()


def cleanup():
    """Clean up test files"""
    print("=" * 60)
    print("Cleaning up test files...")
    print("=" * 60)
    
    import os
    try:
        if os.path.exists("test_sample.txt"):
            os.remove("test_sample.txt")
            print("✅ Removed test_sample.txt")
        if os.path.exists("test_sample_modified.txt"):
            os.remove("test_sample_modified.txt")
            print("✅ Removed test_sample_modified.txt")
    except Exception as e:
        print(f"⚠️  Error during cleanup: {e}")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("TEXT FILE VIEWING TOOLS - TEST SUITE")
    print("=" * 60)
    print()
    
    try:
        # Create test file
        create_test_file()
        
        # Run tests
        test_cat_file()
        test_head_tail()
        test_grep_in_file()
        test_sed_replace()
        test_count_lines()
        
        print("=" * 60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        cleanup()


if __name__ == "__main__":
    main()

