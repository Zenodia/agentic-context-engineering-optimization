"""
Shell Commands Skill - Safe File System Navigation and Search
Implements safe shell commands with prohibition of dangerous operations (rm, -fr)

Author: Zenodia
License: MIT
"""

import os
import sys
import subprocess
import shlex
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

# Add parent directory to path for skill_tool decorator
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from skill_loader import skill_tool


# ============================================================================
# Safety Configuration
# ============================================================================

# Prohibited commands and flags - NEVER allow these
PROHIBITED_COMMANDS = ['rm', 'rmdir', 'unlink', 'dd', 'mkfs', 'fdisk']
PROHIBITED_FLAGS = ['-rf', '-fr', '-r -f', '-f -r', '--recursive --force', '--force --recursive']

# Environment configuration
SAFE_MODE = os.environ.get('SAFE_MODE', 'true').lower() == 'true'
MAX_FIND_RESULTS = int(os.environ.get('MAX_FIND_RESULTS', '100'))

# Current working directory (session-based)
_current_directory = os.getcwd()


# ============================================================================
# Safety Validation
# ============================================================================

def is_command_safe(command: str) -> tuple[bool, Optional[str]]:
    """
    Validate that a command is safe to execute
    
    Args:
        command: Command string to validate
        
    Returns:
        Tuple of (is_safe, error_message)
    """
    if not SAFE_MODE:
        return True, None
    
    command_lower = command.lower()
    
    # Check for prohibited commands
    for prohibited_cmd in PROHIBITED_COMMANDS:
        if re.search(rf'\b{prohibited_cmd}\b', command_lower):
            return False, f"❌ Command '{prohibited_cmd}' is prohibited for safety. Use safe alternatives."
    
    # Check for prohibited flags
    for prohibited_flag in PROHIBITED_FLAGS:
        if prohibited_flag in command_lower:
            return False, f"❌ Flag combination '{prohibited_flag}' is prohibited for safety."
    
    # Additional pattern checks
    dangerous_patterns = [
        (r'rm\s+', "rm command"),
        (r'-rf\s+', "-rf flags"),
        (r'>\s*/dev/', "device file redirection"),
        (r':\s*\(\s*\)\s*\{', "fork bomb pattern"),
    ]
    
    for pattern, description in dangerous_patterns:
        if re.search(pattern, command_lower):
            return False, f"❌ Dangerous pattern detected: {description}"
    
    return True, None


def execute_safe_command(command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute a shell command with safety checks
    
    Args:
        command: Command to execute
        cwd: Working directory (defaults to current session directory)
        
    Returns:
        Dictionary with execution results
    """
    # Validate command safety
    is_safe, error_msg = is_command_safe(command)
    if not is_safe:
        return {
            'success': False,
            'output': '',
            'error': error_msg,
            'command': command
        }
    
    # Use session directory if not specified
    if cwd is None:
        cwd = _current_directory
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30  # 30 second timeout
        )
        
        return {
            'success': result.returncode == 0,
            'output': result.stdout.strip(),
            'error': result.stderr.strip() if result.returncode != 0 else None,
            'command': command,
            'return_code': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': '',
            'error': '❌ Command timed out after 30 seconds',
            'command': command
        }
    except Exception as e:
        return {
            'success': False,
            'output': '',
            'error': f'❌ Error executing command: {str(e)}',
            'command': command
        }


# ============================================================================
# Navigation Commands
# ============================================================================

@skill_tool(
    name="list_directory",
    description="List contents of a directory. Similar to 'ls' command. Shows files and directories with details."
)
def list_directory(path: Optional[str] = None, show_hidden: bool = False) -> str:
    """
    List directory contents with file details
    
    Args:
        path: Directory path to list (default: current directory)
        show_hidden: Include hidden files (starting with .)
        
    Returns:
        Formatted directory listing
    """
    global _current_directory
    
    target_path = path if path else _current_directory
    
    # Expand user home directory
    target_path = os.path.expanduser(target_path)
    
    # Check if path exists
    if not os.path.exists(target_path):
        return f"❌ Error: Directory not found: {target_path}"
    
    if not os.path.isdir(target_path):
        return f"❌ Error: Not a directory: {target_path}"
    
    # Build ls command - use shlex.quote for proper escaping
    ls_flags = '-lh' if not show_hidden else '-lha'
    command = f'ls {ls_flags} {shlex.quote(target_path)}'
    
    result = execute_safe_command(command)
    
    if result['success']:
        output = f"📂 Directory: {target_path}\n\n{result['output']}"
        return output
    else:
        return f"❌ Error listing directory: {result['error']}"


@skill_tool(
    name="change_directory",
    description="Change the current working directory. Similar to 'cd' command. Updates session directory for subsequent commands."
)
def change_directory(path: str) -> str:
    """
    Change current working directory
    
    Args:
        path: Directory path to change to
        
    Returns:
        Confirmation message or error
    """
    global _current_directory
    
    # Expand user home directory and resolve path
    target_path = os.path.expanduser(path)
    target_path = os.path.abspath(target_path)
    
    # Check if directory exists
    if not os.path.exists(target_path):
        return f"❌ Error: Directory not found: {target_path}"
    
    if not os.path.isdir(target_path):
        return f"❌ Error: Not a directory: {target_path}"
    
    # Update session directory
    _current_directory = target_path
    
    return f"✅ Changed directory to: {target_path}"


@skill_tool(
    name="print_working_directory",
    description="Print the current working directory path. Similar to 'pwd' command. Shows the current session location."
)
def print_working_directory() -> str:
    """
    Get current working directory
    
    Returns:
        Current directory path
    """
    global _current_directory
    return f"📍 Current directory: {_current_directory}"


# ============================================================================
# File Operations
# ============================================================================

@skill_tool(
    name="copy_file",
    description="Copy files or directories. Similar to 'cp' command. Supports recursive copying of directories."
)
def copy_file(source: str, destination: str, recursive: bool = False) -> str:
    """
    Copy file or directory to destination
    
    Args:
        source: Source file or directory path
        destination: Destination path
        recursive: Enable recursive copy for directories
        
    Returns:
        Success message or error
    """
    global _current_directory
    
    # Expand and resolve paths
    source_path = os.path.expanduser(source)
    dest_path = os.path.expanduser(destination)
    
    # Make absolute paths if relative
    if not os.path.isabs(source_path):
        source_path = os.path.join(_current_directory, source_path)
    if not os.path.isabs(dest_path):
        dest_path = os.path.join(_current_directory, dest_path)
    
    # Check if source exists
    if not os.path.exists(source_path):
        return f"❌ Error: Source not found: {source_path}"
    
    # Build cp command - use shlex.quote for proper escaping
    cp_flags = '-r' if recursive else ''
    command = f'cp {cp_flags} {shlex.quote(source_path)} {shlex.quote(dest_path)}'
    
    result = execute_safe_command(command)
    
    if result['success']:
        return f"✅ Successfully copied: {source_path} → {dest_path}"
    else:
        return f"❌ Error copying: {result['error']}"


@skill_tool(
    name="touch_file",
    description="Create a new empty file or update timestamp. Similar to 'touch' command. Can create multiple files at once."
)
def touch_file(filepath: str) -> str:
    """
    Create new empty file(s) or update timestamp
    
    Args:
        filepath: Path to file(s) to create (space-separated for multiple)
        
    Returns:
        Success message or error
    """
    global _current_directory
    
    # Expand user home directory
    filepath = os.path.expanduser(filepath)
    
    # Build touch command - use shlex.quote for proper escaping
    command = f'touch {shlex.quote(filepath)}'
    
    result = execute_safe_command(command, cwd=_current_directory)
    
    if result['success']:
        return f"✅ File(s) created/updated: {filepath}"
    else:
        return f"❌ Error creating file: {result['error']}"


# ============================================================================
# File Finding and Searching
# ============================================================================

@skill_tool(
    name="find_files",
    description="Find files by name, extension, or pattern. Supports wildcards (*.md) and regex. Can search recursively through directories."
)
def find_files(
    pattern: str,
    search_path: Optional[str] = None,
    file_type: str = "f",
    case_sensitive: bool = True,
    max_depth: Optional[int] = None
) -> str:
    """
    Find files matching a pattern using the find command
    
    Args:
        pattern: Search pattern (wildcards like *.md or regex)
        search_path: Directory to search in (default: current directory)
        file_type: Type filter - 'f' for files, 'd' for directories, 'l' for links
        case_sensitive: Case-sensitive matching (default: True)
        max_depth: Maximum directory depth to search
        
    Returns:
        List of matching file paths or error message
    """
    global _current_directory
    
    # Determine search path
    if search_path is None:
        search_path = _current_directory
    else:
        search_path = os.path.expanduser(search_path)
        if not os.path.isabs(search_path):
            search_path = os.path.join(_current_directory, search_path)
    
    # Check if search path exists
    if not os.path.exists(search_path):
        return f"❌ Error: Search path not found: {search_path}"
    
    # Build find command - use shlex.quote for proper escaping
    find_cmd_parts = ['find', shlex.quote(search_path)]
    
    # Add max depth if specified
    if max_depth is not None:
        find_cmd_parts.append(f'-maxdepth {max_depth}')
    
    # Add type filter
    if file_type in ['f', 'd', 'l']:
        find_cmd_parts.append(f'-type {file_type}')
    
    # Add name pattern (case-sensitive or insensitive)
    if case_sensitive:
        find_cmd_parts.append(f'-name {shlex.quote(pattern)}')
    else:
        find_cmd_parts.append(f'-iname {shlex.quote(pattern)}')
    
    command = ' '.join(find_cmd_parts)
    
    result = execute_safe_command(command)
    
    if result['success']:
        if not result['output']:
            return f"🔍 No files found matching pattern: {pattern}"
        
        # Parse results
        files = result['output'].split('\n')
        files = [f for f in files if f.strip()]  # Remove empty lines
        
        # Limit results
        if len(files) > MAX_FIND_RESULTS:
            files = files[:MAX_FIND_RESULTS]
            truncated_msg = f"\n\n⚠️  Results truncated to {MAX_FIND_RESULTS} items (set MAX_FIND_RESULTS to increase)"
        else:
            truncated_msg = ""
        
        # Format output
        file_type_name = {'f': 'files', 'd': 'directories', 'l': 'links'}.get(file_type, 'items')
        output = f"🔍 Found {len(files)} {file_type_name} matching '{pattern}':\n\n"
        output += '\n'.join(files)
        output += truncated_msg
        
        return output
    else:
        return f"❌ Error searching for files: {result['error']}"


@skill_tool(
    name="find_files_by_regex",
    description="Find files using regex pattern matching. More powerful than wildcards, supports complex patterns like '^[a-z]+\\.log$'"
)
def find_files_by_regex(
    regex_pattern: str,
    search_path: Optional[str] = None,
    file_type: str = "f"
) -> str:
    """
    Find files using regex pattern matching
    
    Args:
        regex_pattern: Regular expression pattern (e.g., '^test_.*\\.py$')
        search_path: Directory to search in (default: current directory)
        file_type: Type filter - 'f' for files, 'd' for directories
        
    Returns:
        List of matching file paths or error message
    """
    global _current_directory
    
    # Determine search path
    if search_path is None:
        search_path = _current_directory
    else:
        search_path = os.path.expanduser(search_path)
        if not os.path.isabs(search_path):
            search_path = os.path.join(_current_directory, search_path)
    
    # Check if search path exists
    if not os.path.exists(search_path):
        return f"❌ Error: Search path not found: {search_path}"
    
    # Build find command with regex - use shlex.quote for proper escaping
    find_cmd_parts = ['find', shlex.quote(search_path)]
    
    # Add type filter
    if file_type in ['f', 'd', 'l']:
        find_cmd_parts.append(f'-type {file_type}')
    
    # Add regex pattern
    find_cmd_parts.append(f'-regex {shlex.quote(regex_pattern)}')
    
    command = ' '.join(find_cmd_parts)
    
    result = execute_safe_command(command)
    
    if result['success']:
        if not result['output']:
            return f"🔍 No files found matching regex: {regex_pattern}"
        
        # Parse results
        files = result['output'].split('\n')
        files = [f for f in files if f.strip()]
        
        # Limit results
        if len(files) > MAX_FIND_RESULTS:
            files = files[:MAX_FIND_RESULTS]
            truncated_msg = f"\n\n⚠️  Results truncated to {MAX_FIND_RESULTS} items"
        else:
            truncated_msg = ""
        
        # Format output
        file_type_name = {'f': 'files', 'd': 'directories', 'l': 'links'}.get(file_type, 'items')
        output = f"🔍 Found {len(files)} {file_type_name} matching regex '{regex_pattern}':\n\n"
        output += '\n'.join(files)
        output += truncated_msg
        
        return output
    else:
        return f"❌ Error searching with regex: {result['error']}"


@skill_tool(
    name="find_by_extension",
    description="Convenient helper to find all files with a specific extension. E.g., find all .md, .py, .json files."
)
def find_by_extension(
    extension: str,
    search_path: Optional[str] = None
) -> str:
    """
    Find all files with a specific extension
    
    Args:
        extension: File extension (with or without dot, e.g., 'md' or '.md')
        search_path: Directory to search in (default: current directory)
        
    Returns:
        List of matching files
    """
    # Normalize extension
    if not extension.startswith('.'):
        extension = f'.{extension}'
    
    # Use find_files with wildcard pattern
    pattern = f'*{extension}'
    return find_files(pattern=pattern, search_path=search_path, file_type='f')


@skill_tool(
    name="grep_files",
    description="Search for text patterns within files. Useful for finding files containing specific content."
)
def grep_files(
    search_text: str,
    file_pattern: str = "*",
    search_path: Optional[str] = None,
    case_sensitive: bool = True,
    show_line_numbers: bool = True
) -> str:
    """
    Search for text within files using grep
    
    Args:
        search_text: Text pattern to search for
        file_pattern: File pattern to search in (e.g., '*.py')
        search_path: Directory to search in (default: current directory)
        case_sensitive: Case-sensitive search (default: True)
        show_line_numbers: Show line numbers in results (default: True)
        
    Returns:
        Matching lines with file paths
    """
    global _current_directory
    
    # Determine search path
    if search_path is None:
        search_path = _current_directory
    else:
        search_path = os.path.expanduser(search_path)
        if not os.path.isabs(search_path):
            search_path = os.path.join(_current_directory, search_path)
    
    # Build grep command
    grep_flags = ['-r']  # Recursive
    if not case_sensitive:
        grep_flags.append('-i')
    if show_line_numbers:
        grep_flags.append('-n')
    
    grep_flags_str = ' '.join(grep_flags)
    # Use shlex.quote for proper escaping
    command = f'grep {grep_flags_str} {shlex.quote(search_text)} {shlex.quote(search_path)} --include={shlex.quote(file_pattern)}'
    
    result = execute_safe_command(command)
    
    if result['success']:
        if not result['output']:
            return f"🔍 No matches found for '{search_text}' in {file_pattern}"
        
        lines = result['output'].split('\n')
        if len(lines) > MAX_FIND_RESULTS:
            lines = lines[:MAX_FIND_RESULTS]
            truncated_msg = f"\n\n⚠️  Results truncated to {MAX_FIND_RESULTS} lines"
        else:
            truncated_msg = ""
        
        output = f"🔍 Found {len(lines)} matches for '{search_text}':\n\n"
        output += '\n'.join(lines)
        output += truncated_msg
        
        return output
    else:
        # grep returns exit code 1 when no matches found
        if result['return_code'] == 1:
            return f"🔍 No matches found for '{search_text}' in {file_pattern}"
        return f"❌ Error searching: {result['error']}"


# ============================================================================
# Text File Viewing and Manipulation
# ============================================================================

@skill_tool(
    name="cat_file",
    description="Display contents of a text file. Similar to 'cat' command. Can show line numbers and limit output."
)
def cat_file(
    filepath: str,
    show_line_numbers: bool = False,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None
) -> str:
    """
    Display file contents with optional line numbers and range
    
    Args:
        filepath: Path to file to display
        show_line_numbers: Show line numbers (default: False)
        start_line: Starting line number (1-indexed, default: None for all)
        end_line: Ending line number (inclusive, default: None for all)
        
    Returns:
        File contents or error message
    """
    global _current_directory
    
    # Resolve path
    target_path = os.path.expanduser(filepath)
    if not os.path.isabs(target_path):
        target_path = os.path.join(_current_directory, target_path)
    
    # Check if file exists
    if not os.path.exists(target_path):
        return f"❌ Error: File not found: {target_path}"
    
    if not os.path.isfile(target_path):
        return f"❌ Error: Not a file: {target_path}"
    
    # Build command - use shlex.quote for proper escaping
    if start_line is not None or end_line is not None:
        # Use sed to extract line range
        if start_line is None:
            start_line = 1
        if end_line is None:
            end_line = '$'  # Last line in sed
        
        command = f'sed -n {shlex.quote(f"{start_line},{end_line}p")} {shlex.quote(target_path)}'
    elif show_line_numbers:
        command = f'cat -n {shlex.quote(target_path)}'
    else:
        command = f'cat {shlex.quote(target_path)}'
    
    result = execute_safe_command(command)
    
    if result['success']:
        if not result['output']:
            return f"📄 File is empty: {target_path}"
        
        # Check output size
        lines = result['output'].split('\n')
        if len(lines) > 1000:
            truncated_msg = f"\n\n⚠️  Large file ({len(lines)} lines). Consider using head_file, tail_file, or line range."
        else:
            truncated_msg = ""
        
        output = f"📄 Contents of: {target_path}\n\n{result['output']}{truncated_msg}"
        return output
    else:
        return f"❌ Error reading file: {result['error']}"


@skill_tool(
    name="head_file",
    description="Display the first N lines of a file. Similar to 'head' command. Useful for previewing large files."
)
def head_file(filepath: str, num_lines: int = 10) -> str:
    """
    Show first N lines of a file
    
    Args:
        filepath: Path to file
        num_lines: Number of lines to show (default: 10)
        
    Returns:
        First N lines of file or error message
    """
    global _current_directory
    
    # Resolve path
    target_path = os.path.expanduser(filepath)
    if not os.path.isabs(target_path):
        target_path = os.path.join(_current_directory, target_path)
    
    # Check if file exists
    if not os.path.exists(target_path):
        return f"❌ Error: File not found: {target_path}"
    
    if not os.path.isfile(target_path):
        return f"❌ Error: Not a file: {target_path}"
    
    # Build head command - use shlex.quote for proper escaping
    command = f'head -n {num_lines} {shlex.quote(target_path)}'
    
    result = execute_safe_command(command)
    
    if result['success']:
        if not result['output']:
            return f"📄 File is empty: {target_path}"
        
        output = f"📄 First {num_lines} lines of: {target_path}\n\n{result['output']}"
        return output
    else:
        return f"❌ Error reading file: {result['error']}"


@skill_tool(
    name="tail_file",
    description="Display the last N lines of a file. Similar to 'tail' command. Useful for viewing log files."
)
def tail_file(filepath: str, num_lines: int = 10) -> str:
    """
    Show last N lines of a file
    
    Args:
        filepath: Path to file
        num_lines: Number of lines to show (default: 10)
        
    Returns:
        Last N lines of file or error message
    """
    global _current_directory
    
    # Resolve path
    target_path = os.path.expanduser(filepath)
    if not os.path.isabs(target_path):
        target_path = os.path.join(_current_directory, target_path)
    
    # Check if file exists
    if not os.path.exists(target_path):
        return f"❌ Error: File not found: {target_path}"
    
    if not os.path.isfile(target_path):
        return f"❌ Error: Not a file: {target_path}"
    
    # Build tail command - use shlex.quote for proper escaping
    command = f'tail -n {num_lines} {shlex.quote(target_path)}'
    
    result = execute_safe_command(command)
    
    if result['success']:
        if not result['output']:
            return f"📄 File is empty: {target_path}"
        
        output = f"📄 Last {num_lines} lines of: {target_path}\n\n{result['output']}"
        return output
    else:
        return f"❌ Error reading file: {result['error']}"


@skill_tool(
    name="grep_in_file",
    description="Search for text pattern in a specific file. More targeted than grep_files. Shows matching lines with context."
)
def grep_in_file(
    filepath: str,
    search_pattern: str,
    case_sensitive: bool = True,
    show_line_numbers: bool = True,
    context_lines: int = 0,
    regex: bool = False
) -> str:
    """
    Search for pattern in a specific file
    
    Args:
        filepath: Path to file to search in
        search_pattern: Text pattern to search for
        case_sensitive: Case-sensitive search (default: True)
        show_line_numbers: Show line numbers (default: True)
        context_lines: Show N lines before and after match (default: 0)
        regex: Treat pattern as regex (default: False, uses fixed string)
        
    Returns:
        Matching lines with optional context
    """
    global _current_directory
    
    # Resolve path
    target_path = os.path.expanduser(filepath)
    if not os.path.isabs(target_path):
        target_path = os.path.join(_current_directory, target_path)
    
    # Check if file exists
    if not os.path.exists(target_path):
        return f"❌ Error: File not found: {target_path}"
    
    if not os.path.isfile(target_path):
        return f"❌ Error: Not a file: {target_path}"
    
    # Build grep command
    grep_flags = []
    
    if not case_sensitive:
        grep_flags.append('-i')
    if show_line_numbers:
        grep_flags.append('-n')
    if context_lines > 0:
        grep_flags.append(f'-C {context_lines}')
    if not regex:
        grep_flags.append('-F')  # Fixed string (not regex)
    
    grep_flags_str = ' '.join(grep_flags)
    # Use shlex.quote for proper escaping of pattern and path
    command = f'grep {grep_flags_str} {shlex.quote(search_pattern)} {shlex.quote(target_path)}'
    
    result = execute_safe_command(command)
    
    if result['success']:
        if not result['output']:
            return f"🔍 No matches found for '{search_pattern}' in {filepath}"
        
        lines = result['output'].split('\n')
        output = f"🔍 Found {len(lines)} matches for '{search_pattern}' in {filepath}:\n\n{result['output']}"
        return output
    else:
        # grep returns exit code 1 when no matches found
        if result.get('return_code') == 1:
            return f"🔍 No matches found for '{search_pattern}' in {filepath}"
        return f"❌ Error searching file: {result['error']}"


@skill_tool(
    name="sed_replace",
    description="Replace text in file using sed. Can preview changes or save to new file. Supports regex patterns."
)
def sed_replace(
    filepath: str,
    search_pattern: str,
    replacement: str,
    output_file: Optional[str] = None,
    preview_only: bool = True,
    regex: bool = True,
    global_replace: bool = True
) -> str:
    """
    Replace text patterns in file using sed
    
    Args:
        filepath: Path to file to modify
        search_pattern: Pattern to search for
        replacement: Replacement text
        output_file: Save to different file (default: None, modifies in preview)
        preview_only: Only show preview, don't modify (default: True for safety)
        regex: Treat pattern as regex (default: True)
        global_replace: Replace all occurrences per line (default: True)
        
    Returns:
        Modified content or preview
    """
    global _current_directory
    
    # Resolve path
    target_path = os.path.expanduser(filepath)
    if not os.path.isabs(target_path):
        target_path = os.path.join(_current_directory, target_path)
    
    # Check if file exists
    if not os.path.exists(target_path):
        return f"❌ Error: File not found: {target_path}"
    
    if not os.path.isfile(target_path):
        return f"❌ Error: Not a file: {target_path}"
    
    # Build sed command - correct format: s/pattern/replacement/flags
    # Escape special characters in pattern and replacement for sed
    # Use shlex.quote for file paths
    flags = 'g' if global_replace else ''
    # Escape forward slashes in pattern and replacement for sed
    escaped_pattern = search_pattern.replace('/', r'\/')
    escaped_replacement = replacement.replace('/', r'\/')
    sed_expression = f"s/{escaped_pattern}/{escaped_replacement}/{flags}"
    
    if preview_only:
        # Just display the result, don't modify file
        command = f"sed {shlex.quote(sed_expression)} {shlex.quote(target_path)}"
    else:
        if output_file:
            # Save to different file
            output_path = os.path.expanduser(output_file)
            if not os.path.isabs(output_path):
                output_path = os.path.join(_current_directory, output_path)
            command = f"sed {shlex.quote(sed_expression)} {shlex.quote(target_path)} > {shlex.quote(output_path)}"
        else:
            return "❌ Error: In-place modification requires output_file parameter or keep preview_only=True"
    
    result = execute_safe_command(command)
    
    if result['success']:
        if preview_only:
            output = f"🔄 Preview of replacements in {filepath}:\n"
            output += f"   Pattern: '{search_pattern}' → '{replacement}'\n\n"
            output += result['output']
            output += "\n\n💡 Set preview_only=False and specify output_file to save changes"
            return output
        else:
            return f"✅ Successfully applied replacements and saved to: {output_file}"
    else:
        return f"❌ Error applying sed: {result['error']}"


@skill_tool(
    name="count_lines",
    description="Count lines, words, and characters in a file. Similar to 'wc' command."
)
def count_lines(filepath: str) -> str:
    """
    Count lines, words, and characters in a file
    
    Args:
        filepath: Path to file
        
    Returns:
        Line, word, and character counts
    """
    global _current_directory
    
    # Resolve path
    target_path = os.path.expanduser(filepath)
    if not os.path.isabs(target_path):
        target_path = os.path.join(_current_directory, target_path)
    
    # Check if file exists
    if not os.path.exists(target_path):
        return f"❌ Error: File not found: {target_path}"
    
    if not os.path.isfile(target_path):
        return f"❌ Error: Not a file: {target_path}"
    
    # Build wc command - use shlex.quote for proper escaping
    command = f'wc {shlex.quote(target_path)}'
    
    result = execute_safe_command(command)
    
    if result['success']:
        # Parse wc output: lines words chars filename
        parts = result['output'].split()
        if len(parts) >= 3:
            lines, words, chars = parts[0], parts[1], parts[2]
            output = f"📊 Statistics for {filepath}:\n"
            output += f"   Lines: {lines}\n"
            output += f"   Words: {words}\n"
            output += f"   Characters: {chars}"
            return output
        return f"📊 {result['output']}"
    else:
        return f"❌ Error counting: {result['error']}"


# ============================================================================
# Utility Functions
# ============================================================================

@skill_tool(
    name="get_file_info",
    description="Get detailed information about a file or directory (size, permissions, modification time)."
)
def get_file_info(filepath: str) -> str:
    """
    Get detailed file or directory information
    
    Args:
        filepath: Path to file or directory
        
    Returns:
        Detailed file information
    """
    global _current_directory
    
    # Resolve path
    target_path = os.path.expanduser(filepath)
    if not os.path.isabs(target_path):
        target_path = os.path.join(_current_directory, target_path)
    
    # Check if exists
    if not os.path.exists(target_path):
        return f"❌ Error: File not found: {target_path}"
    
    # Use ls -lh for detailed info - use shlex.quote for proper escaping
    command = f'ls -lh {shlex.quote(target_path)}'
    result = execute_safe_command(command)
    
    if result['success']:
        return f"📄 File info for: {target_path}\n\n{result['output']}"
    else:
        return f"❌ Error getting file info: {result['error']}"


@skill_tool(
    name="check_safety_status",
    description="Check the current safety mode status and configuration."
)
def check_safety_status() -> str:
    """
    Get current safety configuration status
    
    Returns:
        Safety status information
    """
    status = f"""
🔒 Safety Status:
- Safe Mode: {'✅ ENABLED' if SAFE_MODE else '⚠️  DISABLED'}
- Max Find Results: {MAX_FIND_RESULTS}
- Current Directory: {_current_directory}

Prohibited Commands: {', '.join(PROHIBITED_COMMANDS)}
Prohibited Flags: {', '.join(PROHIBITED_FLAGS)}

Safe Mode protects against:
❌ File deletion (rm, rmdir)
❌ Force recursive operations (-rf, -fr)
❌ System modifications (dd, mkfs, fdisk)
❌ Fork bombs and dangerous patterns

Allowed Safe Commands:
✅ ls (list directory)
✅ cd (change directory)
✅ pwd (print working directory)
✅ cp (copy files)
✅ touch (create files)
✅ find (search files)
✅ grep (search content)
✅ cat (view file contents)
✅ head (view first lines)
✅ tail (view last lines)
✅ sed (text replacement - preview mode)
✅ wc (count lines/words)
"""
    return status.strip()


# ============================================================================
# Skill Information
# ============================================================================

def get_skill_info() -> Dict[str, Any]:
    """
    Get skill metadata and capabilities
    
    Returns:
        Dictionary with skill information
    """
    return {
        'name': 'shell_commands',
        'version': '1.1.0',
        'description': 'Safe file system navigation, search, and text file viewing',
        'capabilities': [
            'list_directory',
            'change_directory',
            'print_working_directory',
            'copy_file',
            'touch_file',
            'find_files',
            'find_files_by_regex',
            'find_by_extension',
            'grep_files',
            'get_file_info',
            'check_safety_status',
            'cat_file',
            'head_file',
            'tail_file',
            'grep_in_file',
            'sed_replace',
            'count_lines'
        ],
        'safe_mode': SAFE_MODE,
        'max_find_results': MAX_FIND_RESULTS,
        'prohibited_commands': PROHIBITED_COMMANDS,
        'prohibited_flags': PROHIBITED_FLAGS
    }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Shell Commands Skill')
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
            
            # Route command to appropriate function
            result = None
            
            if command == 'list_directory':
                path = parameters.get('path')
                show_hidden = parameters.get('show_hidden', False)
                result = list_directory(path=path, show_hidden=show_hidden)
            
            elif command == 'change_directory':
                path = parameters.get('path', '')
                result = change_directory(path=path)
            
            elif command == 'print_working_directory':
                result = print_working_directory()
            
            elif command == 'copy_file':
                source = parameters.get('source', '')
                destination = parameters.get('destination', '')
                recursive = parameters.get('recursive', False)
                result = copy_file(source=source, destination=destination, recursive=recursive)
            
            elif command == 'touch_file':
                filepath = parameters.get('filepath', '')
                result = touch_file(filepath=filepath)
            
            elif command == 'find_files':
                pattern = parameters.get('pattern', '*')
                search_path = parameters.get('search_path')
                file_type = parameters.get('file_type', 'f')
                case_sensitive = parameters.get('case_sensitive', True)
                max_depth = parameters.get('max_depth')
                result = find_files(
                    pattern=pattern,
                    search_path=search_path,
                    file_type=file_type,
                    case_sensitive=case_sensitive,
                    max_depth=max_depth
                )
            
            elif command == 'find_files_by_regex':
                regex_pattern = parameters.get('regex_pattern', '')
                search_path = parameters.get('search_path')
                file_type = parameters.get('file_type', 'f')
                result = find_files_by_regex(
                    regex_pattern=regex_pattern,
                    search_path=search_path,
                    file_type=file_type
                )
            
            elif command == 'find_by_extension':
                extension = parameters.get('extension', '')
                search_path = parameters.get('search_path')
                result = find_by_extension(extension=extension, search_path=search_path)
            
            elif command == 'grep_files':
                search_text = parameters.get('search_text', '')
                file_pattern = parameters.get('file_pattern', '*')
                search_path = parameters.get('search_path')
                case_sensitive = parameters.get('case_sensitive', True)
                show_line_numbers = parameters.get('show_line_numbers', True)
                result = grep_files(
                    search_text=search_text,
                    file_pattern=file_pattern,
                    search_path=search_path,
                    case_sensitive=case_sensitive,
                    show_line_numbers=show_line_numbers
                )
            
            elif command == 'get_file_info':
                filepath = parameters.get('filepath', '')
                result = get_file_info(filepath=filepath)
            
            elif command == 'check_safety_status':
                result = check_safety_status()
            
            elif command == 'cat_file':
                filepath = parameters.get('filepath', '')
                show_line_numbers = parameters.get('show_line_numbers', False)
                start_line = parameters.get('start_line')
                end_line = parameters.get('end_line')
                result = cat_file(
                    filepath=filepath,
                    show_line_numbers=show_line_numbers,
                    start_line=start_line,
                    end_line=end_line
                )
            
            elif command == 'head_file':
                filepath = parameters.get('filepath', '')
                num_lines = parameters.get('num_lines', 10)
                result = head_file(filepath=filepath, num_lines=num_lines)
            
            elif command == 'tail_file':
                filepath = parameters.get('filepath', '')
                num_lines = parameters.get('num_lines', 10)
                result = tail_file(filepath=filepath, num_lines=num_lines)
            
            elif command == 'grep_in_file':
                filepath = parameters.get('filepath', '')
                search_pattern = parameters.get('search_pattern', '')
                case_sensitive = parameters.get('case_sensitive', True)
                show_line_numbers = parameters.get('show_line_numbers', True)
                context_lines = parameters.get('context_lines', 0)
                regex = parameters.get('regex', False)
                result = grep_in_file(
                    filepath=filepath,
                    search_pattern=search_pattern,
                    case_sensitive=case_sensitive,
                    show_line_numbers=show_line_numbers,
                    context_lines=context_lines,
                    regex=regex
                )
            
            elif command == 'sed_replace':
                filepath = parameters.get('filepath', '')
                search_pattern = parameters.get('search_pattern', '')
                replacement = parameters.get('replacement', '')
                output_file = parameters.get('output_file')
                preview_only = parameters.get('preview_only', True)
                regex = parameters.get('regex', True)
                global_replace = parameters.get('global_replace', True)
                result = sed_replace(
                    filepath=filepath,
                    search_pattern=search_pattern,
                    replacement=replacement,
                    output_file=output_file,
                    preview_only=preview_only,
                    regex=regex,
                    global_replace=global_replace
                )
            
            elif command == 'count_lines':
                filepath = parameters.get('filepath', '')
                result = count_lines(filepath=filepath)
            
            else:
                output = {
                    'success': False,
                    'error': f"Unknown command: {command}. Available commands: {', '.join(get_skill_info()['capabilities'])}"
                }
                print(json.dumps(output))
                sys.exit(1)
            
            # Prepare output
            output = {
                'success': True,
                'result': result,
                'command': command,
                'output_size': len(str(result))
            }
            
            print(json.dumps(output))
        
        except json.JSONDecodeError as e:
            output = {
                'success': False,
                'error': f"Invalid JSON input: {str(e)}"
            }
            print(json.dumps(output))
            sys.exit(1)
        
        except Exception as e:
            output = {
                'success': False,
                'error': f"Execution error: {str(e)}",
                'traceback': str(e)
            }
            print(json.dumps(output))
            sys.exit(1)
    
    else:
        # Default: Display skill information
        print("🛠️  Shell Commands Skill - Safe File System Operations")
        print("=" * 60)
        print(check_safety_status())
        print("\n" + "=" * 60)
        print("\n✅ Skill loaded successfully!")
        print("\nAvailable commands:")
        info = get_skill_info()
        for capability in info['capabilities']:
            print(f"  - {capability}")

