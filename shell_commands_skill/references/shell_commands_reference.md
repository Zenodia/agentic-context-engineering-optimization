# Shell Commands Reference

Complete reference for safe shell commands in the Shell Commands Skill.

## Navigation Commands

### ls - List Directory Contents

**Purpose:** Display files and directories in the current or specified directory.

**Syntax:**
```bash
list_directory(path=None, show_hidden=False)
```

**Examples:**
```python
# List current directory
list_directory()

# List specific directory
list_directory(path="/home/user/projects")

# Include hidden files
list_directory(show_hidden=True)

# List with details (long format is default)
list_directory(path="/etc", show_hidden=True)
```

**Output Format:**
```
drwxr-xr-x  5 user user 4.0K Jan 15 10:30 directory_name
-rw-r--r--  1 user user 1.2K Jan 15 10:30 file_name.txt
```

**Output Columns:**
1. Permissions (drwxr-xr-x)
2. Number of links
3. Owner
4. Group
5. Size (human-readable)
6. Modification date
7. File/directory name

---

### cd - Change Directory

**Purpose:** Change the current working directory.

**Syntax:**
```bash
change_directory(path)
```

**Examples:**
```python
# Absolute path
change_directory("/home/user/projects")

# Relative path
change_directory("src/utils")

# Home directory
change_directory("~")

# Parent directory
change_directory("..")

# Previous directory
change_directory("-")  # Note: May not work in all contexts
```

**Notes:**
- Changes are session-based (persist within the skill session)
- Use absolute paths for clarity
- Directory must exist

---

### pwd - Print Working Directory

**Purpose:** Display the current working directory path.

**Syntax:**
```bash
print_working_directory()
```

**Example:**
```python
# Show current location
current_dir = print_working_directory()
print(current_dir)
# Output: 📍 Current directory: /home/user/projects
```

**Use Cases:**
- Verify current location before operations
- Debug path-related issues
- Show context to users

---

## File Operations

### touch - Create Files

**Purpose:** Create new empty files or update timestamps.

**Syntax:**
```bash
touch_file(filepath)
```

**Examples:**
```python
# Create single file
touch_file("newfile.txt")

# Create multiple files
touch_file("file1.txt file2.txt file3.txt")

# Create file with path
touch_file("src/utils/helper.py")

# Update existing file timestamp
touch_file("existing_file.txt")
```

**Notes:**
- Creates parent directories if they don't exist (with proper permissions)
- Safe operation - won't delete or overwrite content
- Can be used to update modification timestamps

---

### cp - Copy Files

**Purpose:** Copy files or directories to a new location.

**Syntax:**
```bash
copy_file(source, destination, recursive=False)
```

**Examples:**
```python
# Copy single file
copy_file(source="config.yaml", destination="backup/config.yaml")

# Copy with absolute paths
copy_file(
    source="/home/user/file.txt",
    destination="/home/user/backup/file.txt"
)

# Copy directory recursively
copy_file(
    source="src/",
    destination="backup/src/",
    recursive=True
)

# Copy and rename
copy_file(
    source="config.yaml",
    destination="config.yaml.backup"
)
```

**Notes:**
- Preserves file attributes by default
- Recursive flag required for directories
- Creates destination directory if needed
- Source must exist

---

## Search Commands

### find - Find Files

**Purpose:** Search for files by name, extension, or pattern.

**Syntax:**
```bash
find_files(
    pattern,
    search_path=None,
    file_type="f",
    case_sensitive=True,
    max_depth=None
)
```

**Parameters:**
- `pattern`: Search pattern (wildcards or exact name)
- `search_path`: Where to search (default: current directory)
- `file_type`: "f" (files), "d" (directories), "l" (links)
- `case_sensitive`: True/False
- `max_depth`: Maximum directory depth (None = unlimited)

**Examples:**
```python
# Find all Python files
find_files(pattern="*.py")

# Find in specific directory
find_files(pattern="*.json", search_path="/home/user/config")

# Find directories
find_files(pattern="*test*", file_type="d")

# Case-insensitive search
find_files(pattern="readme*", case_sensitive=False)

# Limited depth
find_files(pattern="*.md", max_depth=2)
```

**Common Patterns:**
- `*.py` - All Python files
- `test_*` - Files starting with "test_"
- `*config*` - Files containing "config"
- `README*` - README files with any extension

---

### find (Regex) - Advanced Find

**Purpose:** Find files using regex patterns.

**Syntax:**
```bash
find_files_by_regex(
    regex_pattern,
    search_path=None,
    file_type="f"
)
```

**Examples:**
```python
# Files starting with lowercase and ending in .log
find_files_by_regex(regex_pattern="^[a-z]+\\.log$")

# Numbered text files
find_files_by_regex(regex_pattern="^[0-9]+\\.txt$")

# Test files (multiple patterns)
find_files_by_regex(regex_pattern="(^test_.*\\.py$|.*_test\\.py$)")
```

**Regex Special Characters:**
- `.` - Any character
- `^` - Start of string
- `$` - End of string
- `*` - Zero or more
- `+` - One or more
- `[]` - Character class
- `|` - Or

---

### find_by_extension - Quick Extension Search

**Purpose:** Convenient helper for finding files by extension.

**Syntax:**
```bash
find_by_extension(extension, search_path=None)
```

**Examples:**
```python
# Find Python files
find_by_extension(extension="py")

# Find markdown files
find_by_extension(extension="md")

# Find JSON files in specific directory
find_by_extension(
    extension="json",
    search_path="/home/user/config"
)

# Extension with or without dot works
find_by_extension(extension=".yaml")  # Same as "yaml"
```

---

### grep - Search File Contents

**Purpose:** Search for text patterns within files.

**Syntax:**
```bash
grep_files(
    search_text,
    file_pattern="*",
    search_path=None,
    case_sensitive=True,
    show_line_numbers=True
)
```

**Examples:**
```python
# Find TODO comments in Python files
grep_files(search_text="TODO", file_pattern="*.py")

# Case-insensitive search
grep_files(
    search_text="error",
    file_pattern="*.log",
    case_sensitive=False
)

# Search in specific directory
grep_files(
    search_text="import",
    file_pattern="*.py",
    search_path="/home/user/project/src"
)

# Without line numbers
grep_files(
    search_text="FIXME",
    file_pattern="*",
    show_line_numbers=False
)
```

**Common Searches:**
- `TODO` - Find TODO comments
- `FIXME` - Find FIXME notes
- `import` - Find import statements
- `class ` - Find class definitions
- `def ` - Find function definitions
- `error` - Find error messages

---

## Utility Commands

### get_file_info - File Information

**Purpose:** Get detailed information about a file or directory.

**Syntax:**
```bash
get_file_info(filepath)
```

**Examples:**
```python
# Get file info
get_file_info("config.yaml")

# Get directory info
get_file_info("/home/user/projects")

# With relative path
get_file_info("./src/main.py")
```

**Output:**
```
📄 File info for: /home/user/config.yaml
-rw-r--r-- 1 user user 1.2K Jan 15 10:30 config.yaml
```

---

### check_safety_status - Safety Configuration

**Purpose:** View current safety settings and restrictions.

**Syntax:**
```bash
check_safety_status()
```

**Example:**
```python
# Check safety configuration
status = check_safety_status()
print(status)
```

**Output:**
```
🔒 Safety Status:
- Safe Mode: ✅ ENABLED
- Max Find Results: 100
- Current Directory: /home/user/projects

Prohibited Commands: rm, rmdir, unlink, dd, mkfs, fdisk
Prohibited Flags: -rf, -fr, -r -f, -f -r

Safe Mode protects against:
❌ File deletion (rm, rmdir)
❌ Force recursive operations (-rf, -fr)
❌ System modifications (dd, mkfs, fdisk)

Allowed Safe Commands:
✅ ls, cd, pwd, cp, touch, find, grep
```

---

## Safety Features

### Prohibited Commands

The following commands are **BLOCKED** for safety:

#### 🚫 Deletion Commands
- `rm` - Remove files
- `rmdir` - Remove directories
- `unlink` - Delete file links

#### 🚫 Dangerous Flags
- `-rf` / `-fr` - Force recursive deletion
- `-r -f` / `-f -r` - Separate force + recursive
- `--recursive --force` - Long form flags

#### 🚫 System Commands
- `dd` - Disk operations (can wipe drives)
- `mkfs` - Format filesystem
- `fdisk` - Partition disks
- Fork bombs and dangerous patterns

### Why These Restrictions?

**Reasons for blocking dangerous commands:**

1. **No Undo** - Deleted files can't be recovered
2. **Agent Errors** - AI agents can make mistakes
3. **Typos** - Easy to make catastrophic typos
4. **Automation Risk** - Automated operations are more dangerous
5. **Prompt Injection** - Malicious prompts could cause damage

### Safe Alternatives

Instead of dangerous commands, use these alternatives:

| Dangerous | Safe Alternative |
|-----------|------------------|
| `rm file.txt` | Move to trash: `copy_file("file.txt", "trash/file.txt")` |
| `rm -rf dir/` | Copy elsewhere, then manual deletion |
| `dd if=/dev/zero` | ❌ No safe alternative - use manual tools |

---

## Command Patterns

### Navigation Pattern

```python
# 1. Check where you are
print(print_working_directory())

# 2. List contents
print(list_directory())

# 3. Navigate to target
print(change_directory("/path/to/target"))

# 4. Verify
print(print_working_directory())
```

### Search Pattern

```python
# 1. Find files by pattern
files = find_files(pattern="*.py")

# 2. Search within those files
for line in files.split('\n'):
    if line.strip() and not line.startswith('🔍'):
        result = grep_files(
            search_text="TODO",
            file_pattern=line.strip()
        )
        print(result)
```

### Backup Pattern

```python
# 1. Find files to backup
important_files = find_files(pattern="*config*")

# 2. Copy to backup directory
for filepath in important_files.split('\n'):
    if filepath.strip() and not filepath.startswith('🔍'):
        filename = filepath.split('/')[-1]
        copy_file(
            source=filepath,
            destination=f"backups/{filename}"
        )
```

### Project Analysis Pattern

```python
# 1. Navigate to project
change_directory("/home/user/project")

# 2. Get overview
print(list_directory())

# 3. Count file types
python_files = find_by_extension("py")
js_files = find_by_extension("js")
md_files = find_by_extension("md")

# 4. Find TODOs
todos = grep_files(search_text="TODO", file_pattern="*.py")
```

---

## Best Practices

### 1. Always Know Where You Are
```python
# Start with pwd
print(print_working_directory())
```

### 2. Use Absolute Paths When Possible
```python
# Better
find_files(pattern="*.py", search_path="/home/user/project")

# vs Relative (depends on current directory)
find_files(pattern="*.py", search_path="./project")
```

### 3. Verify Before Operations
```python
# Check if file exists first
info = get_file_info("important.txt")
if "Error" not in info:
    copy_file(source="important.txt", destination="backup/")
```

### 4. Limit Search Scope
```python
# Faster: Specific and limited
find_files(pattern="*.json", search_path="/etc", max_depth=2)

# Slower: Too broad
find_files(pattern="*", search_path="/")
```

### 5. Handle Errors Gracefully
```python
result = list_directory(path="/maybe/invalid")
if "Error" in result:
    print("Directory not found, using current directory")
    result = list_directory()
```

### 6. Use Case-Insensitive for Flexibility
```python
# More flexible
find_files(pattern="readme*", case_sensitive=False)
# Finds: README.md, readme.txt, ReadMe.md
```

---

## Performance Tips

### Fast Operations
- Specific patterns: `*.py` instead of `*`
- Limited depth: `max_depth=3`
- Specific paths: `/home/user/project` instead of `/`
- File type filters: `file_type='f'`

### Slow Operations
- Broad patterns: `*` (everything)
- Unlimited depth: `max_depth=None`
- Root search: `search_path='/'`
- No filters: Search everything

### Example Comparison
```python
# Fast ⚡
find_files(
    pattern="*.py",
    search_path="/home/user/project/src",
    max_depth=3,
    file_type="f"
)

# Slow 🐌
find_files(
    pattern="*",
    search_path="/",
    max_depth=None
)
```

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Directory not found" | Invalid path | Use `pwd` to verify location |
| "Permission denied" | No read access | Check permissions with `get_file_info` |
| "Command not allowed" | Dangerous command | Use safe alternatives |
| "No files found" | Pattern mismatch | Try case-insensitive or different pattern |
| "Too many results" | Too broad pattern | Narrow search or increase MAX_FIND_RESULTS |

### Error Handling Pattern
```python
def safe_operation(path):
    # Validate first
    info = get_file_info(path)
    if "Error" in info:
        return f"Invalid path: {path}"
    
    # Proceed with operation
    return copy_file(source=path, destination="backup/")
```

---

## Environment Variables

### SAFE_MODE
- **Default:** `true`
- **Purpose:** Enable/disable safety restrictions
- **Values:** `true` or `false`

```bash
export SAFE_MODE=true  # Enable (recommended)
export SAFE_MODE=false # Disable (dangerous!)
```

### MAX_FIND_RESULTS
- **Default:** `100`
- **Purpose:** Limit number of search results
- **Values:** Any positive integer

```bash
export MAX_FIND_RESULTS=100   # Default
export MAX_FIND_RESULTS=500   # More results
export MAX_FIND_RESULTS=50    # Fewer results
```

---

## Integration Examples

### Standalone Script
```python
#!/usr/bin/env python3
from shell_commands_skill.scripts.shell_commands import find_files

result = find_files(pattern="*.py")
print(result)
```

### With LangChain
```python
from skill_loader import SkillLoader

loader = SkillLoader()
skill = loader.load_skill("shell_commands_skill")
tools = skill.get_tools()

# Use with agent
agent = create_react_agent(llm, tools, prompt)
```

### In Gradio App
```python
import gradio as gr
from shell_commands_skill.scripts.shell_commands import find_files

def search_handler(pattern):
    return find_files(pattern=pattern)

interface = gr.Interface(
    fn=search_handler,
    inputs="text",
    outputs="text"
)
```

---

## Quick Reference Card

```
Navigation:
  ls        list_directory(path)
  cd        change_directory(path)
  pwd       print_working_directory()

File Ops:
  touch     touch_file(filepath)
  cp        copy_file(source, dest)

Search:
  find      find_files(pattern, search_path)
  grep      grep_files(search_text, file_pattern)

Info:
  stat      get_file_info(filepath)
  safety    check_safety_status()

Prohibited:
  ❌ rm, rmdir, -rf, -fr, dd, mkfs, fdisk

File Types:
  "f" = files
  "d" = directories
  "l" = symbolic links
```

---

**Remember:** This skill prioritizes **SAFETY** over power. For destructive operations, use manual tools with explicit confirmation.

