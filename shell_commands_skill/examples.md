# Shell Commands Skill - Examples

This document provides practical examples of using the shell commands skill for common tasks.

## Table of Contents
- [Navigation Examples](#navigation-examples)
- [File Finding Examples](#file-finding-examples)
- [File Operations Examples](#file-operations-examples)
- [Content Search Examples](#content-search-examples)
- [Combined Workflows](#combined-workflows)
- [Safety Examples](#safety-examples)

---

## Navigation Examples

### Example 1: Check Current Location
```python
from shell_commands_skill.scripts.shell_commands import print_working_directory

result = print_working_directory()
print(result)
# Output: 📍 Current directory: /home/user/projects
```

### Example 2: List Current Directory
```python
from shell_commands_skill.scripts.shell_commands import list_directory

result = list_directory()
print(result)
# Output:
# 📂 Directory: /home/user/projects
# 
# drwxr-xr-x  5 user user 4.0K Jan 15 10:30 my_project
# drwxr-xr-x  3 user user 4.0K Jan 14 09:20 another_project
# -rw-r--r--  1 user user 1.2K Jan 13 15:45 README.md
```

### Example 3: Navigate to Different Directory
```python
from shell_commands_skill.scripts.shell_commands import change_directory

result = change_directory("/home/user/documents")
print(result)
# Output: ✅ Changed directory to: /home/user/documents
```

### Example 4: List Specific Directory with Hidden Files
```python
from shell_commands_skill.scripts.shell_commands import list_directory

result = list_directory(path="/home/user/my_project", show_hidden=True)
print(result)
# Shows all files including hidden ones (.git, .env, etc.)
```

---

## File Finding Examples

### Example 5: Find All Markdown Files
```python
from shell_commands_skill.scripts.shell_commands import find_files

result = find_files(pattern="*.md")
print(result)
# Output:
# 🔍 Found 15 files matching '*.md':
# 
# /home/user/projects/README.md
# /home/user/projects/docs/guide.md
# /home/user/projects/docs/api.md
# ...
```

### Example 6: Find Python Files in Specific Directory
```python
from shell_commands_skill.scripts.shell_commands import find_files

result = find_files(
    pattern="*.py",
    search_path="/home/user/my_project/src"
)
print(result)
# Output: Lists all .py files in the src directory
```

### Example 7: Find Configuration Files
```python
from shell_commands_skill.scripts.shell_commands import find_files

result = find_files(pattern="*config*", file_type="f")
print(result)
# Finds: config.yaml, .eslintrc.config.js, nginx.conf, etc.
```

### Example 8: Find Test Files
```python
from shell_commands_skill.scripts.shell_commands import find_files

result = find_files(pattern="test_*.py")
print(result)
# Finds: test_user.py, test_api.py, test_utils.py, etc.
```

### Example 9: Find Directories
```python
from shell_commands_skill.scripts.shell_commands import find_files

result = find_files(
    pattern="*test*",
    file_type="d"  # d for directories
)
print(result)
# Output: Lists all directories with 'test' in the name
```

### Example 10: Case-Insensitive Search
```python
from shell_commands_skill.scripts.shell_commands import find_files

result = find_files(
    pattern="readme*",
    case_sensitive=False
)
print(result)
# Finds: README.md, readme.txt, ReadMe.md, etc.
```

### Example 11: Limited Depth Search
```python
from shell_commands_skill.scripts.shell_commands import find_files

result = find_files(
    pattern="*.json",
    max_depth=2  # Only search current dir and immediate subdirs
)
print(result)
# Faster search, limited to 2 levels deep
```

### Example 12: Find by Extension (Convenience Function)
```python
from shell_commands_skill.scripts.shell_commands import find_by_extension

# Find all Python files
python_files = find_by_extension(extension="py")

# Find all JSON files
json_files = find_by_extension(extension="json")

# Find all markdown files in specific directory
md_files = find_by_extension(
    extension="md",
    search_path="/home/user/docs"
)
```

### Example 13: Find with Regex
```python
from shell_commands_skill.scripts.shell_commands import find_files_by_regex

# Find log files with specific pattern
result = find_files_by_regex(regex_pattern="^[a-z]+\.log$")

# Find numbered files
result = find_files_by_regex(regex_pattern="^[0-9]+\.txt$")

# Find files starting with capital letter
result = find_files_by_regex(regex_pattern="^[A-Z].*\.py$")
```

---

## File Operations Examples

### Example 14: Create New File
```python
from shell_commands_skill.scripts.shell_commands import touch_file

result = touch_file(filepath="newfile.txt")
print(result)
# Output: ✅ File(s) created/updated: newfile.txt
```

### Example 15: Create Multiple Files
```python
from shell_commands_skill.scripts.shell_commands import touch_file

result = touch_file(filepath="file1.txt file2.txt file3.txt")
print(result)
# Creates three files at once
```

### Example 16: Copy a File
```python
from shell_commands_skill.scripts.shell_commands import copy_file

result = copy_file(
    source="config.yaml",
    destination="backups/config.yaml"
)
print(result)
# Output: ✅ Successfully copied: config.yaml → backups/config.yaml
```

### Example 17: Copy Directory Recursively
```python
from shell_commands_skill.scripts.shell_commands import copy_file

result = copy_file(
    source="src/",
    destination="backup/src/",
    recursive=True
)
print(result)
# Copies entire directory tree
```

### Example 18: Get File Information
```python
from shell_commands_skill.scripts.shell_commands import get_file_info

result = get_file_info(filepath="README.md")
print(result)
# Output:
# 📄 File info for: /home/user/projects/README.md
# -rw-r--r-- 1 user user 1.2K Jan 15 10:30 README.md
```

---

## Content Search Examples

### Example 19: Search for Text in Files
```python
from shell_commands_skill.scripts.shell_commands import grep_files

result = grep_files(
    search_text="TODO",
    file_pattern="*.py"
)
print(result)
# Output:
# 🔍 Found 12 matches for 'TODO':
# 
# src/main.py:45:    # TODO: Implement error handling
# src/utils.py:89:    # TODO: Add caching
# tests/test_api.py:23:    # TODO: Add more test cases
```

### Example 20: Case-Insensitive Content Search
```python
from shell_commands_skill.scripts.shell_commands import grep_files

result = grep_files(
    search_text="error",
    file_pattern="*.log",
    case_sensitive=False
)
# Finds: error, Error, ERROR, ErRoR, etc.
```

### Example 21: Search in Specific Directory
```python
from shell_commands_skill.scripts.shell_commands import grep_files

result = grep_files(
    search_text="import",
    file_pattern="*.py",
    search_path="/home/user/project/src"
)
# Only searches in the src directory
```

### Example 22: Search Without Line Numbers
```python
from shell_commands_skill.scripts.shell_commands import grep_files

result = grep_files(
    search_text="FIXME",
    file_pattern="*",
    show_line_numbers=False
)
# Shows matching files without line numbers
```

---

## Combined Workflows

### Example 23: Explore New Project
```python
from shell_commands_skill.scripts.shell_commands import (
    change_directory,
    list_directory,
    find_files
)

# Navigate to project
print(change_directory("/home/user/new_project"))

# See what's there
print(list_directory())

# Find all Python files
print(find_files(pattern="*.py"))

# Find all documentation
print(find_files(pattern="*.md"))
```

### Example 24: Find and Analyze Configuration Files
```python
from shell_commands_skill.scripts.shell_commands import (
    find_files,
    get_file_info
)

# Find all config files
configs = find_files(pattern="*config*")

# Get detailed info for each
for line in configs.split('\n'):
    if line.strip() and not line.startswith('🔍'):
        print(get_file_info(line.strip()))
```

### Example 25: Backup Important Files
```python
from shell_commands_skill.scripts.shell_commands import (
    find_files,
    copy_file
)

# Find all YAML config files
yaml_files = find_files(pattern="*.yaml")

# Copy each to backup directory
for line in yaml_files.split('\n'):
    filepath = line.strip()
    if filepath and not filepath.startswith('🔍'):
        filename = filepath.split('/')[-1]
        copy_file(
            source=filepath,
            destination=f"backups/{filename}"
        )
```

### Example 26: Find TODOs Across Project
```python
from shell_commands_skill.scripts.shell_commands import (
    find_files,
    grep_files
)

# Find all source files
source_files = find_files(pattern="*.py")
print(source_files)

# Search for TODO comments
todos = grep_files(
    search_text="TODO",
    file_pattern="*.py",
    show_line_numbers=True
)
print(todos)
```

### Example 27: Project Structure Analysis
```python
from shell_commands_skill.scripts.shell_commands import (
    print_working_directory,
    list_directory,
    find_files,
    find_by_extension
)

# Show current location
print(print_working_directory())

# List root directory
print(list_directory())

# Count different file types
python_count = len(find_by_extension("py").split('\n')) - 3  # Subtract header lines
js_count = len(find_by_extension("js").split('\n')) - 3
json_count = len(find_by_extension("json").split('\n')) - 3
md_count = len(find_by_extension("md").split('\n')) - 3

print(f"\nProject Statistics:")
print(f"Python files: {python_count}")
print(f"JavaScript files: {js_count}")
print(f"JSON files: {json_count}")
print(f"Markdown files: {md_count}")
```

---

## Safety Examples

### Example 28: Blocked Command (rm)
```python
# This will be BLOCKED by the safety system
from shell_commands_skill.scripts.shell_commands import execute_safe_command

result = execute_safe_command("rm file.txt")
print(result)
# Output:
# {
#   'success': False,
#   'output': '',
#   'error': "❌ Command 'rm' is prohibited for safety. Use safe alternatives.",
#   'command': 'rm file.txt'
# }
```

### Example 29: Blocked Flag Combination (-rf)
```python
# This will also be BLOCKED
from shell_commands_skill.scripts.shell_commands import execute_safe_command

result = execute_safe_command("rm -rf temp/")
print(result)
# Output: Error message about prohibited -rf flags
```

### Example 30: Check Safety Status
```python
from shell_commands_skill.scripts.shell_commands import check_safety_status

print(check_safety_status())
# Output:
# 🔒 Safety Status:
# - Safe Mode: ✅ ENABLED
# - Max Find Results: 100
# - Current Directory: /home/user/projects
# 
# Prohibited Commands: rm, rmdir, unlink, dd, mkfs, fdisk
# Prohibited Flags: -rf, -fr, -r -f, -f -r, --recursive --force, ...
# 
# Safe Mode protects against:
# ❌ File deletion (rm, rmdir)
# ❌ Force recursive operations (-rf, -fr)
# ❌ System modifications (dd, mkfs, fdisk)
# ❌ Fork bombs and dangerous patterns
# 
# Allowed Safe Commands:
# ✅ ls (list directory)
# ✅ cd (change directory)
# ✅ pwd (print working directory)
# ✅ cp (copy files)
# ✅ touch (create files)
# ✅ find (search files)
# ✅ grep (search content)
```

### Example 31: Safe Alternative to Deletion
```python
# Instead of deleting, move to trash folder
from shell_commands_skill.scripts.shell_commands import copy_file, touch_file

# Create trash folder if needed
touch_file("trash/.gitkeep")

# Move files to trash instead of deleting
copy_file(
    source="temp_file.txt",
    destination="trash/temp_file.txt"
)
# Now you can manually delete from trash when safe
```

---

## Real-World Use Cases

### Use Case 1: Code Review Preparation
```python
"""Find all Python files that need review"""
from shell_commands_skill.scripts.shell_commands import (
    find_files,
    grep_files
)

# Find all Python files
python_files = find_files(pattern="*.py", search_path="src/")

# Find files with TODO or FIXME
todos = grep_files(search_text="TODO", file_pattern="*.py", search_path="src/")
fixmes = grep_files(search_text="FIXME", file_pattern="*.py", search_path="src/")

print("Files for review:")
print(todos)
print(fixmes)
```

### Use Case 2: Documentation Audit
```python
"""Check documentation coverage"""
from shell_commands_skill.scripts.shell_commands import find_files

# Find all code files
py_files = find_files(pattern="*.py")
py_count = len([l for l in py_files.split('\n') if l.strip() and not l.startswith('🔍')])

# Find all doc files
md_files = find_files(pattern="*.md")
md_count = len([l for l in md_files.split('\n') if l.strip() and not l.startswith('🔍')])

print(f"Code files: {py_count}")
print(f"Documentation files: {md_count}")
print(f"Docs per code file: {md_count/py_count:.2f}")
```

### Use Case 3: Configuration Management
```python
"""Find and backup all configuration files"""
from shell_commands_skill.scripts.shell_commands import (
    find_files,
    copy_file,
    touch_file
)

# Create backup directory
touch_file("config_backups/.gitkeep")

# Find all config files
configs = find_files(pattern="*.{yaml,yml,json,conf,cfg}")

# Backup each one
for line in configs.split('\n'):
    if line.strip() and not line.startswith('🔍'):
        filepath = line.strip()
        filename = filepath.split('/')[-1]
        copy_file(
            source=filepath,
            destination=f"config_backups/{filename}"
        )
        print(f"Backed up: {filename}")
```

### Use Case 4: Find Unused Files
```python
"""Find files not imported or referenced"""
from shell_commands_skill.scripts.shell_commands import (
    find_files,
    grep_files
)

# Get all Python files
all_py = find_files(pattern="*.py")

# Check each file for imports
for line in all_py.split('\n'):
    if line.strip() and not line.startswith('🔍'):
        filename = line.strip().split('/')[-1].replace('.py', '')
        # Search for imports of this file
        imports = grep_files(
            search_text=f"import.*{filename}",
            file_pattern="*.py"
        )
        if "No matches found" in imports:
            print(f"⚠️  Possibly unused: {line.strip()}")
```

---

## Tips and Best Practices

### Tip 1: Use Absolute Paths for Clarity
```python
# Better: Absolute path
find_files(pattern="*.py", search_path="/home/user/project/src")

# vs Relative path (depends on current directory)
find_files(pattern="*.py", search_path="./src")
```

### Tip 2: Limit Search Scope for Performance
```python
# Faster: Specific directory and depth limit
find_files(pattern="*.json", search_path="/home/user/project", max_depth=3)

# vs Slower: Search everything from root
find_files(pattern="*.json", search_path="/")
```

### Tip 3: Combine Tools for Complex Tasks
```python
# First find files
files = find_files(pattern="*.py")

# Then search within those files
for filepath in files.split('\n'):
    if filepath.strip():
        content = grep_files(search_text="class ", file_pattern=filepath)
        print(content)
```

### Tip 4: Always Check Current Directory First
```python
# Know where you are before operating
print(print_working_directory())

# Then proceed with operations
list_directory()
```

### Tip 5: Use Case-Insensitive for Flexible Matching
```python
# Finds README, readme, ReadMe, etc.
find_files(pattern="readme*", case_sensitive=False)
```

---

## Error Handling Examples

### Example: Handle Missing Directory
```python
from shell_commands_skill.scripts.shell_commands import list_directory

result = list_directory(path="/nonexistent/path")
if "Error" in result:
    print("Directory not found, using current directory instead")
    result = list_directory()
print(result)
```

### Example: Handle No Results
```python
from shell_commands_skill.scripts.shell_commands import find_files

result = find_files(pattern="*.xyz")
if "No files found" in result:
    print("No matching files, trying different pattern...")
    result = find_files(pattern="*")
```

### Example: Validate Before Operation
```python
from shell_commands_skill.scripts.shell_commands import (
    get_file_info,
    copy_file
)

# Check if file exists first
info = get_file_info("important.txt")
if "Error" not in info:
    # File exists, safe to copy
    copy_file(source="important.txt", destination="backup/important.txt")
else:
    print("File doesn't exist, skipping backup")
```

---

## Integration Examples

### With LangChain Agent
```python
from langchain.agents import create_react_agent
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from skill_loader import SkillLoader

# Load skill
loader = SkillLoader()
skill = loader.load_skill("shell_commands_skill")
tools = skill.get_tools()

# Create agent
llm = ChatNVIDIA(model="meta/llama-3.1-8b-instruct")
agent = create_react_agent(llm, tools, prompt_template)

# Use agent
response = agent.invoke({"input": "Find all Python files in the project"})
```

### Standalone Script
```python
#!/usr/bin/env python3
import sys
from shell_commands_skill.scripts.shell_commands import find_files

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: script.py <pattern>")
        sys.exit(1)
    
    pattern = sys.argv[1]
    result = find_files(pattern=pattern)
    print(result)
```

---

**For more examples and detailed documentation, see:**
- `SKILL.md` - Complete skill instructions
- `README.md` - User guide
- `config.yaml` - Configuration options

