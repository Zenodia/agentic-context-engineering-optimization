---
name: shell-commands
version: 1.0.0
description: A safe shell commands skill for file system navigation and file searching. Includes ls, cd, pwd, cp, touch commands and powerful find/grep capabilities with regex support. Prohibits dangerous commands like rm and -fr for safety.
author: Zenodia
license: MIT
tags:
  - shell
  - commands
  - file-system
  - navigation
  - search
  - find
  - grep
  - utilities
  - linux
  - ubuntu
runtime:
  type: python
  version: ">=3.8"
dependencies:
  - PyYAML>=6.0
  - langchain-nvidia-ai-endpoints>=0.1.0
  - langchain-core>=0.1.0
  - colorama>=0.4.0
permissions:
  - file:read
  - file:write
  - system:execute
environment:
  SAFE_MODE:
    description: Enable safe mode to prevent dangerous commands (rm, -fr)
    required: false
    default: "true"
  MAX_FIND_RESULTS:
    description: Maximum number of results to return from find commands
    required: false
    default: "100"
---

# Shell Commands Skill

A safe and powerful shell commands skill that provides essential file system navigation and advanced file searching capabilities. This skill enables AI agents to explore directories, manage files safely, and search for files using regex patterns - all while preventing destructive operations.

## When to Use This Skill

Use this skill whenever users need to:
- Navigate the file system (list directories, change directories, show current path)
- Create files or copy files/directories
- Find files by name, extension, or pattern matching
- Search for specific file types across directories
- Explore project structures
- Locate configuration files or source code
- List files with specific patterns

**Trigger phrases:** "find files", "search for", "list directory", "show current path", "copy file", "create file", "locate all", "what files", "navigate to"

## Core Capabilities

### 1. Safe Navigation Commands
Essential file system navigation with safety guarantees:
- **ls**: List directory contents with detailed information
- **cd**: Change current working directory (session-based)
- **pwd**: Print working directory
- **cp**: Copy files and directories safely
- **touch**: Create new empty files

**Safety Features:**
- ❌ **rm commands are PROHIBITED** - prevents accidental file deletion
- ❌ **-fr flags are BLOCKED** - prevents force removal operations
- ✅ All commands are validated before execution
- ✅ Clear error messages for blocked operations

### 2. Advanced File Finding
Powerful file search capabilities with regex support:
- **find**: Search for files by name, extension, or pattern
- **grep**: Search file contents (when combined with find)
- **locate**: Fast file location using patterns
- Support for wildcard patterns (*.md, *.py, etc.)
- Recursive directory searching
- Type filtering (files only, directories only)

### 3. Pattern Matching
Flexible pattern matching for file discovery:
- Extension-based: `*.md`, `*.py`, `*.json`
- Name patterns: `test_*`, `*config*`, `README*`
- Regex support: `^[a-z]+\.txt$`, `.*\.log$`
- Case-sensitive and case-insensitive options

## Usage Instructions

### For AI Agents

When a user asks about file system operations or file searching, follow these workflows:

#### Navigation Commands

**List Directory Contents:**
```python
from scripts.shell_commands import list_directory

# List current directory
result = list_directory()
print(result)

# List specific directory with details
result = list_directory(path="/home/user/projects", show_hidden=True)
print(result)
```

**Change Directory:**
```python
from scripts.shell_commands import change_directory

# Change to specific directory
result = change_directory(path="/home/user/documents")
print(result)
```

**Print Working Directory:**
```python
from scripts.shell_commands import print_working_directory

# Show current location
result = print_working_directory()
print(result)
```

**Copy Files/Directories:**
```python
from scripts.shell_commands import copy_file

# Copy a file
result = copy_file(source="file.txt", destination="backup/file.txt")
print(result)

# Copy directory recursively
result = copy_file(source="src/", destination="backup/src/", recursive=True)
print(result)
```

**Create New File:**
```python
from scripts.shell_commands import touch_file

# Create empty file
result = touch_file(filepath="newfile.txt")
print(result)

# Create multiple files
result = touch_file(filepath="file1.txt file2.txt file3.txt")
print(result)
```

#### File Finding Commands

**Find Files by Extension:**
```python
from scripts.shell_commands import find_files

# Find all markdown files in current directory and subdirectories
result = find_files(
    pattern="*.md",
    search_path=None,  # Uses current directory
    file_type="f"  # f=file, d=directory
)
print(result)

# Find all Python files in specific directory
result = find_files(
    pattern="*.py",
    search_path="/home/user/projects",
    file_type="f"
)
print(result)
```

**Find Files by Name Pattern:**
```python
# Find all config files
result = find_files(
    pattern="*config*",
    search_path="/etc",
    file_type="f"
)

# Find all test files
result = find_files(
    pattern="test_*.py",
    search_path="/home/user/project",
    file_type="f"
)
```

**Find with Regex:**
```python
# Find files matching regex pattern
result = find_files(
    pattern="^[a-z]+\.log$",
    search_path="/var/log",
    file_type="f",
    use_regex=True
)
```

**Find Directories:**
```python
# Find all directories containing "test"
result = find_files(
    pattern="*test*",
    search_path="/home/user",
    file_type="d"  # Search for directories
)
```

## Example Interactions

### Example 1: Find Markdown Files
**User:** "Find all markdown files in my current directory"

**Agent Action:**
1. Call `find_files(pattern="*.md", file_type="f")`
2. Return list of all .md files with full paths
3. Display count and paths

**Output:**
```
Found 15 markdown files:
/home/user/project/README.md
/home/user/project/docs/guide.md
/home/user/project/docs/api.md
...
```

### Example 2: Navigate and List
**User:** "Go to my documents folder and show me what's there"

**Agent Action:**
1. Call `change_directory(path="/home/user/documents")`
2. Call `list_directory()`
3. Display directory contents

**Output:**
```
Changed to: /home/user/documents
Contents:
drwxr-xr-x  reports/
drwxr-xr-x  personal/
-rw-r--r--  notes.txt
-rw-r--r--  budget.xlsx
```

### Example 3: Find Configuration Files
**User:** "Find all configuration files in my project"

**Agent Action:**
1. Call `find_files(pattern="*config*", file_type="f")`
2. Also call `find_files(pattern="*.conf", file_type="f")`
3. Combine and deduplicate results

**Output:**
```
Found 8 configuration files:
/home/user/project/config.yaml
/home/user/project/.eslintrc.config.js
/home/user/project/nginx.conf
...
```

### Example 4: Copy Project Files
**User:** "Copy all Python files from src/ to backup/"

**Agent Action:**
1. First call `find_files(pattern="*.py", search_path="src/", file_type="f")`
2. Create backup directory if needed
3. Call `copy_file()` for each file or use recursive copy

**Output:**
```
Copying Python files from src/ to backup/...
✅ Copied src/main.py → backup/main.py
✅ Copied src/utils.py → backup/utils.py
✅ Copied src/config.py → backup/config.py
Total: 15 files copied successfully
```

### Example 5: Blocked Dangerous Command
**User:** "Delete all temporary files with rm -rf"

**Agent Action:**
1. Detect "rm" or "-rf" in request
2. Block command execution
3. Explain why it's blocked and suggest alternatives

**Output:**
```
❌ Command blocked for safety!
The 'rm' command and '-rf' flags are prohibited to prevent accidental data loss.

Alternative suggestion:
Instead of deleting, I can help you:
1. Find and list temporary files: find_files(pattern="*.tmp")
2. Move them to a trash folder: copy_file(source="temp/*", destination="trash/")
3. Create a list for manual review

Would you like me to help with one of these alternatives?
```

## Best Practices for Agents

### 1. Always Validate Paths
Before executing commands, check if paths exist and are accessible:
```
"Let me check if that directory exists first..."
[call list_directory or pwd to verify]
```

### 2. Provide Context for Results
When returning file lists, provide useful context:
```
"I found 23 Python files in your project:
- 15 in the src/ directory
- 5 in tests/
- 3 in scripts/

Would you like me to show the full list or filter further?"
```

### 3. Suggest Related Commands
After one operation, suggest related useful commands:
```
"✅ Changed to /home/user/projects
Would you also like me to:
- List the directory contents (ls)
- Find specific files in this directory
- Show subdirectory structure"
```

### 4. Handle Errors Gracefully
If a command fails, provide helpful guidance:
```
"❌ Directory not found: /home/user/nonexistent

Did you mean one of these?
- /home/user/documents
- /home/user/downloads
- /home/user/projects

Or would you like me to create this directory?"
```

### 5. Warn About Dangerous Requests
Always block and explain when users request dangerous operations:
```
"⚠️ I cannot execute 'rm -rf' commands as they can permanently delete files.
This is a safety feature to prevent accidental data loss.

If you need to delete files:
1. Move them to a trash folder first (recoverable)
2. Use your file manager for manual deletion
3. Provide specific file paths (not wildcards) for targeted removal"
```

### 6. Use Relative and Absolute Paths Wisely
Help users understand path context:
```
"You're currently in: /home/user/projects/myapp

Relative path: cd src/
Absolute path: cd /home/user/projects/myapp/src/

Both will work, but relative paths are shorter when working within a project."
```

## Safety Features

### Prohibited Commands
The following commands and flags are **BLOCKED** for safety:

❌ **rm** - Remove/delete files or directories
❌ **rm -r** - Recursive removal
❌ **rm -f** - Force removal (ignore nonexistent files)
❌ **rm -rf** - Force recursive removal (EXTREMELY DANGEROUS)
❌ **-fr** - Any flag combination including force and recursive

### Safe Alternative Commands
Instead of dangerous operations, this skill provides:

✅ **cp** - Copy files (preserves originals)
✅ **touch** - Create new files (doesn't overwrite)
✅ **find** - Locate files (read-only operation)
✅ **ls** - List contents (read-only operation)
✅ **pwd** - Show location (read-only operation)

### Command Validation
All commands go through validation:
1. **Pattern matching**: Check for prohibited strings
2. **Flag checking**: Verify flags are safe
3. **Path validation**: Ensure paths are accessible
4. **Execution limits**: Prevent infinite loops or hangs

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "Permission denied" | Insufficient permissions | Use sudo (if allowed) or check file permissions |
| "Directory not found" | Invalid path | Use `pwd` to check current location, verify path exists |
| "Command not allowed" | Dangerous command blocked | Use safe alternatives provided by the skill |
| "Too many results" | Find returned > MAX_FIND_RESULTS | Narrow search pattern or increase limit |
| "Invalid pattern" | Malformed regex or wildcard | Check pattern syntax, escape special characters |

### Fallback Strategy
If a command fails:
1. Check current working directory with `pwd`
2. Verify the path exists with `ls`
3. Try with absolute path instead of relative
4. Check for typos in path or pattern
5. Suggest corrections based on similar existing paths

## Technical Details

### Command Execution
- All commands run in safe subprocess environment
- Current directory is tracked per session
- Output is captured and formatted
- Timeouts prevent hanging commands
- Error codes are returned with explanations

### Find Command Patterns
The `find` command supports various pattern types:

**Wildcard Patterns:**
- `*.md` - All markdown files
- `test_*` - Files starting with "test_"
- `*config*` - Files containing "config"

**Regex Patterns (use_regex=True):**
- `^README\.md$` - Exact match
- `.*\.log$` - All log files
- `^[0-9]+\.txt$` - Numbered text files

**File Types:**
- `f` - Regular files
- `d` - Directories
- `l` - Symbolic links

### Output Format
All commands return structured output:
```json
{
  "success": true,
  "output": "command output here",
  "error": null,
  "command": "ls -la",
  "execution_time": "0.05s"
}
```

## Integration Patterns

### With Other Skills
This skill can be combined with other skills:

**With File Analysis:**
```python
# Find all Python files
files = find_files(pattern="*.py")
# Then analyze each file with code analysis skill
for file in files:
    analyze_code(file)
```

**With Project Management:**
```python
# Find all project files
project_files = find_files(pattern="*", search_path="./project")
# Generate project structure report
create_project_report(project_files)
```

**With Backup Systems:**
```python
# Find important files
important = find_files(pattern="*.{py,md,yaml}", use_regex=True)
# Copy to backup location
for file in important:
    copy_file(source=file, destination="backups/")
```

## Configuration Options

### Environment Variables

**SAFE_MODE** (default: "true")
- When enabled, blocks all dangerous commands
- Set to "false" only in controlled environments
- Recommended to keep enabled for agent use

**MAX_FIND_RESULTS** (default: "100")
- Limits number of results from find commands
- Prevents overwhelming output
- Increase for comprehensive searches

### Skill Parameters

**list_directory()**
- `path`: Directory to list (default: current)
- `show_hidden`: Include hidden files (default: False)
- `long_format`: Detailed listing (default: True)

**find_files()**
- `pattern`: Search pattern (required)
- `search_path`: Where to search (default: current directory)
- `file_type`: Type filter - "f", "d", or "l" (default: "f")
- `use_regex`: Use regex matching (default: False)
- `case_sensitive`: Case-sensitive matching (default: True)
- `max_depth`: Maximum directory depth (default: None)

**copy_file()**
- `source`: Source file/directory (required)
- `destination`: Destination path (required)
- `recursive`: Copy directories recursively (default: False)
- `preserve`: Preserve file attributes (default: True)

## Advanced Features

### Recursive Searching
Search through entire directory trees:
```python
# Find all JSON files recursively
find_files(
    pattern="*.json",
    search_path="/home/user/project",
    file_type="f"
    # No max_depth = unlimited recursion
)
```

### Depth-Limited Searching
Limit search depth for performance:
```python
# Find only in current directory and immediate subdirectories
find_files(
    pattern="*.py",
    max_depth=2
)
```

### Case-Insensitive Searching
Find files regardless of case:
```python
# Find README files (README.md, readme.txt, ReadMe.md, etc.)
find_files(
    pattern="readme*",
    case_sensitive=False
)
```

### Multiple Pattern Matching
Search for multiple file types:
```python
# Find documentation files
patterns = ["*.md", "*.txt", "*.rst"]
all_docs = []
for pattern in patterns:
    results = find_files(pattern=pattern)
    all_docs.extend(results)
```

### Combined Find and Grep
Find files then search their contents:
```python
# Find all Python files containing "TODO"
python_files = find_files(pattern="*.py")
for file in python_files:
    # Use system grep to search content
    result = execute_safe_command(f"grep -n 'TODO' {file}")
    if result.success:
        print(f"Found TODO in {file}:\n{result.output}")
```

## Troubleshooting

### Issue: Find returns no results
**Solutions:**
1. Check current directory with `pwd`
2. Verify pattern syntax (wildcards vs regex)
3. Try with absolute path instead of relative
4. Check if files actually exist: `ls -la`
5. Try case-insensitive search

### Issue: Permission denied errors
**Solutions:**
1. Check file/directory permissions: `ls -la`
2. Verify you have read access to the directory
3. Try searching in a different directory
4. Use absolute paths to avoid path resolution issues

### Issue: Command blocked by safety features
**Solutions:**
1. Review the safe alternatives suggested
2. Check if you're trying to use `rm` or `-rf`
3. Use `cp` to backup before any modifications
4. Manually perform deletion through file manager if necessary

### Issue: Too many results returned
**Solutions:**
1. Narrow the search pattern
2. Use more specific directory path
3. Add file type filter
4. Set `max_depth` parameter
5. Increase MAX_FIND_RESULTS environment variable

## Performance Considerations

### Efficient Searching
- Use specific search paths instead of searching from root (`/`)
- Limit depth with `max_depth` for faster results
- Use specific patterns instead of wildcards when possible
- Cache results for repeated searches

### Large Directory Trees
For projects with many files:
- Start with narrow searches and expand if needed
- Use file type filters to reduce result set
- Consider searching specific subdirectories
- Monitor MAX_FIND_RESULTS to avoid overwhelming output

## Security Notes

### Why rm is Prohibited
The `rm` command, especially with `-rf` flags, is one of the most dangerous commands in Unix/Linux:
- `rm -rf /` can delete the entire system
- `rm -rf *` can delete all files in current directory
- No "undo" or recovery for deleted files
- Easy to make typos with devastating results
- Agent automation makes accidents more likely

### Safe Practices
This skill enforces safe practices:
✅ Copy instead of move (preserves originals)
✅ Read-only operations (ls, find, pwd)
✅ Explicit confirmation for destructive operations
✅ Path validation before execution
✅ Command whitelist (not blacklist)

## Future Enhancements

Planned features for future versions:
- **xargs integration**: Process find results with other commands
- **stat command**: Detailed file information
- **du command**: Disk usage analysis
- **tree command**: Directory tree visualization
- **grep integration**: Content searching within files
- **ack/ag support**: Advanced code searching
- **Custom command templates**: User-defined safe command combinations
- **Batch operations**: Process multiple files efficiently
- **Undo functionality**: Reverse recent operations (via backups)

---

**Important Safety Notice:**

This skill is designed with safety as the top priority. The prohibition of `rm` and `-rf` commands is intentional and non-negotiable. These restrictions protect against:
- Accidental data loss
- Agent errors or hallucinations causing file deletion
- Malicious prompt injections
- Copy-paste errors
- Automation mistakes

Always use file managers or manual intervention for file deletion operations. This skill focuses on **safe exploration and organization**, not destruction.

---

## Quick Reference

### Navigation
- `list_directory(path)` - List directory contents
- `change_directory(path)` - Change current directory
- `print_working_directory()` - Show current location

### File Operations
- `touch_file(filepath)` - Create empty file
- `copy_file(source, destination, recursive)` - Copy files/directories

### Searching
- `find_files(pattern, search_path, file_type)` - Find files by pattern
- `find_files(pattern, use_regex=True)` - Find with regex

### Common Patterns
- `*.md` - All markdown files
- `test_*` - Files starting with "test_"
- `*config*` - Files containing "config"
- `*.{py,js}` - Python and JavaScript files (regex mode)

**Remember:** Safety first, exploration second, destruction never!


