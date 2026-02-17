# Shell Commands Skill

A safe and powerful shell commands skill for file system navigation and file searching with built-in safety features.

## Features

### 🔒 Safety First
- **Prohibits dangerous commands**: `rm`, `rmdir`, `-rf`, `-fr` flags are blocked
- **Command validation**: All commands checked before execution
- **No data loss**: Focus on read-only and safe operations

### 📂 Navigation Commands
- `list_directory` - List directory contents (ls)
- `change_directory` - Change working directory (cd)
- `print_working_directory` - Show current location (pwd)

### 📝 File Operations
- `copy_file` - Safe file/directory copying (cp)
- `touch_file` - Create new files (touch)

### 🔍 Powerful Search
- `find_files` - Find files by pattern with wildcards (*.md, *.py)
- `find_files_by_regex` - Advanced regex pattern matching
- `find_by_extension` - Quick extension-based search
- `grep_files` - Search file contents

### 🛠️ Utilities
- `get_file_info` - Detailed file information
- `check_safety_status` - View current safety configuration

## Quick Start

### Installation

The skill is automatically discovered by the skill loader. Ensure dependencies are installed:

```bash
pip install PyYAML langchain-nvidia-ai-endpoints langchain-core colorama
```

### Usage Examples

**Find all markdown files:**
```python
from shell_commands_skill.scripts.shell_commands import find_files

result = find_files(pattern="*.md")
print(result)
```

**Navigate and list:**
```python
from shell_commands_skill.scripts.shell_commands import change_directory, list_directory

change_directory("/home/user/projects")
result = list_directory()
print(result)
```

**Find files by extension:**
```python
from shell_commands_skill.scripts.shell_commands import find_by_extension

result = find_by_extension(extension="py", search_path="/home/user/project")
print(result)
```

**Search file contents:**
```python
from shell_commands_skill.scripts.shell_commands import grep_files

result = grep_files(search_text="TODO", file_pattern="*.py")
print(result)
```

## Configuration

Set environment variables to customize behavior:

```bash
# Enable/disable safe mode (default: true)
export SAFE_MODE=true

# Maximum search results (default: 100)
export MAX_FIND_RESULTS=100
```

## Safety Features

### Prohibited Operations

❌ **NEVER ALLOWED:**
- `rm` - Remove files
- `rmdir` - Remove directories
- `-rf` / `-fr` - Force recursive flags
- `dd` - Disk operations
- `mkfs` / `fdisk` - Filesystem operations
- Fork bombs and dangerous patterns

✅ **ALWAYS ALLOWED:**
- Read operations (ls, find, grep, cat)
- Safe write operations (touch, cp)
- Navigation (cd, pwd)

### Why These Restrictions?

This skill prioritizes **safety over power**:
- Agent automation can make mistakes
- Typos can have devastating consequences
- No "undo" for deleted files
- Better to be safe than sorry

For file deletion, use:
- Manual file manager operations
- Move to trash folder instead (reversible)
- Explicit manual confirmation

## Example Workflow

```python
# 1. Check current location
print(print_working_directory())
# Output: 📍 Current directory: /home/user

# 2. Navigate to project
print(change_directory("/home/user/my_project"))
# Output: ✅ Changed directory to: /home/user/my_project

# 3. List contents
print(list_directory())
# Output: Shows directory contents with details

# 4. Find all Python files
print(find_files(pattern="*.py"))
# Output: Lists all .py files recursively

# 5. Search for TODO comments
print(grep_files(search_text="TODO", file_pattern="*.py"))
# Output: Shows files and lines containing TODO

# 6. Copy important files
print(copy_file(source="config.yaml", destination="backups/config.yaml"))
# Output: ✅ Successfully copied: config.yaml → backups/config.yaml
```

## Integration with AI Agents

This skill works seamlessly with the skill loader system:

```python
from skill_loader import SkillLoader

# Load skill
loader = SkillLoader()
skill = loader.load_skill("shell_commands_skill")

# Access tools
tools = skill.get_tools()

# Use with ReAct agent
from langchain.agents import create_react_agent
agent = create_react_agent(llm, tools, prompt)
```

## Find Command Examples

### By Extension
```bash
# Find all markdown files
find_files(pattern="*.md")

# Find all Python files
find_files(pattern="*.py")

# Find all JSON files
find_files(pattern="*.json")
```

### By Name Pattern
```bash
# Find test files
find_files(pattern="test_*")

# Find config files
find_files(pattern="*config*")

# Find README files
find_files(pattern="README*")
```

### With Regex
```bash
# Find files starting with lowercase letters and ending in .log
find_files_by_regex(regex_pattern="^[a-z]+\.log$")

# Find numbered files
find_files_by_regex(regex_pattern="^[0-9]+\.txt$")
```

### Specific Directory
```bash
# Find in specific location
find_files(pattern="*.py", search_path="/home/user/project/src")

# Limit depth
find_files(pattern="*.md", max_depth=2)
```

### By Type
```bash
# Find only directories
find_files(pattern="*test*", file_type="d")

# Find only files
find_files(pattern="*", file_type="f")

# Find symbolic links
find_files(pattern="*", file_type="l")
```

## Troubleshooting

### "Permission denied" errors
- Check file permissions: `get_file_info(filepath)`
- Try with absolute paths
- Verify you have read access to the directory

### "Command not allowed" errors
- Review safety status: `check_safety_status()`
- Use safe alternatives provided in error message
- Consider manual operations for dangerous tasks

### No results found
- Check current directory: `print_working_directory()`
- Verify pattern syntax (wildcards vs regex)
- Try case-insensitive search
- Use absolute paths

### Too many results
- Increase MAX_FIND_RESULTS environment variable
- Narrow search pattern
- Specify search_path to limit scope
- Use max_depth parameter

## Advanced Usage

### Batch Operations
```python
# Find all Python files and get info
python_files = find_files(pattern="*.py")
for filepath in python_files.split('\n'):
    if filepath.strip():
        print(get_file_info(filepath))
```

### Combined Search
```python
# Find markdown files containing specific text
md_files = find_files(pattern="*.md", search_path="./docs")
matches = grep_files(search_text="API", file_pattern="*.md", search_path="./docs")
```

### Safe Backup
```python
# Backup all config files
configs = find_files(pattern="*config*")
for config in configs.split('\n'):
    if config.strip():
        copy_file(source=config, destination=f"backups/{config}")
```

## Documentation

- **SKILL.md** - Complete skill instructions for AI agents
- **config.yaml** - Skill configuration and metadata
- **README.md** - This file (user documentation)

## License

MIT License - See LICENSE file for details

## Author

Zenodia

## Version

1.0.0

---

**Remember:** This skill prioritizes **safety and exploration** over destructive operations. For file deletion, use manual tools with explicit confirmation.

