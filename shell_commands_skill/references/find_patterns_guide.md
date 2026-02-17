# Find Patterns Guide

Reference guide for file finding patterns in the Shell Commands Skill.

## Wildcard Patterns

### Basic Wildcards

| Pattern | Matches | Example |
|---------|---------|---------|
| `*` | Any characters | `*.txt` matches all text files |
| `?` | Single character | `file?.txt` matches `file1.txt`, `fileA.txt` |
| `[abc]` | Any character in set | `file[123].txt` matches `file1.txt`, `file2.txt`, `file3.txt` |
| `[a-z]` | Character range | `[a-z]*.py` matches Python files starting with lowercase |
| `[!abc]` | Not in set | `file[!0-9].txt` matches non-numeric file names |

### Common Wildcard Examples

```bash
# Find all markdown files
*.md

# Find all Python files
*.py

# Find all JavaScript and TypeScript files (using find_files_by_regex)
.*\.(js|ts)$

# Find all config files
*config*

# Find test files
test_*.py

# Find numbered files
file[0-9].txt

# Find README files with any extension
README*
```

## Extension-Based Patterns

### Programming Languages

```bash
# Python
*.py

# JavaScript
*.js

# TypeScript
*.ts

# Java
*.java

# C/C++
*.c, *.cpp, *.h

# Go
*.go

# Rust
*.rs

# Ruby
*.rb
```

### Web Development

```bash
# HTML
*.html

# CSS
*.css

# SCSS/SASS
*.scss, *.sass

# Vue
*.vue

# JSX/TSX
*.jsx, *.tsx
```

### Data Files

```bash
# JSON
*.json

# YAML
*.yaml, *.yml

# XML
*.xml

# CSV
*.csv

# SQL
*.sql
```

### Documentation

```bash
# Markdown
*.md

# Text
*.txt

# ReStructuredText
*.rst

# AsciiDoc
*.adoc
```

### Configuration Files

```bash
# Config
*.conf, *.config

# Environment
*.env, .env*

# INI
*.ini

# TOML
*.toml

# Properties
*.properties
```

## Regex Patterns

When using `find_files_by_regex()`, you can use full regex syntax.

### Regex Special Characters

| Character | Meaning | Example |
|-----------|---------|---------|
| `.` | Any character | `a.c` matches `abc`, `a1c` |
| `^` | Start of string | `^test` matches files starting with "test" |
| `$` | End of string | `\.py$` matches files ending with ".py" |
| `*` | Zero or more | `a*` matches "", "a", "aa", "aaa" |
| `+` | One or more | `a+` matches "a", "aa", "aaa" |
| `?` | Zero or one | `a?` matches "", "a" |
| `[]` | Character class | `[abc]` matches "a", "b", or "c" |
| `()` | Group | `(abc)+` matches "abc", "abcabc" |
| `\|` | Or | `(py\|js)$` matches files ending in .py or .js |
| `\` | Escape | `\.` matches literal dot |

### Common Regex Examples

```bash
# Files starting with lowercase letter and ending in .log
^[a-z]+\.log$

# Numbered text files (1-999)
^[0-9]+\.txt$

# Test files (test_*.py or *_test.py)
(^test_.*\.py$|.*_test\.py$)

# Files with dates in name (YYYY-MM-DD format)
.*[0-9]{4}-[0-9]{2}-[0-9]{2}.*

# Configuration files (various extensions)
.*\.(conf|config|cfg|ini)$

# Image files
.*\.(jpg|jpeg|png|gif|svg|webp)$

# Version files (v1.0.0, v2.1.3, etc.)
^v[0-9]+\.[0-9]+\.[0-9]+.*

# Python package files
^__.*__\.py$

# Hidden files (starting with dot)
^\..+

# Uppercase named files
^[A-Z]+\..+$
```

## File Type Filters

### File Types

```bash
# Regular files
file_type="f"

# Directories
file_type="d"

# Symbolic links
file_type="l"
```

### Examples

```bash
# Find all directories named "test"
find_files(pattern="*test*", file_type="d")

# Find all Python files (not directories)
find_files(pattern="*.py", file_type="f")

# Find all symbolic links
find_files(pattern="*", file_type="l")
```

## Search Depth Control

### Max Depth Examples

```bash
# Only current directory (depth 1)
find_files(pattern="*.py", max_depth=1)

# Current directory and immediate subdirectories (depth 2)
find_files(pattern="*.json", max_depth=2)

# Up to 3 levels deep
find_files(pattern="*config*", max_depth=3)

# Unlimited depth (default)
find_files(pattern="*.md")
```

## Case Sensitivity

### Case-Sensitive (Default)

```python
# Only matches exact case
find_files(pattern="README.md", case_sensitive=True)
# Finds: README.md
# Ignores: readme.md, ReadMe.md, README.MD
```

### Case-Insensitive

```python
# Matches any case combination
find_files(pattern="readme*", case_sensitive=False)
# Finds: README.md, readme.txt, ReadMe.md, README.MD, readme.rst
```

## Complex Search Patterns

### Finding Specific Project Files

```python
# Find all Python source files (excluding tests)
find_files(pattern="*.py")  # Get all
# Then filter out test files in your code

# Find all test files
find_files(pattern="test_*.py")
find_files(pattern="*_test.py")

# Find all configuration files
find_files(pattern="*config*")
find_files(pattern="*.{yaml,yml,json,conf}")  # regex mode
```

### Finding by Directory Name

```python
# Find all files in "tests" directories
find_files(pattern="*", search_path="./tests")

# Find all Python files in "src" directory
find_files(pattern="*.py", search_path="./src")

# Find all docs
find_files(pattern="*", search_path="./docs")
```

### Finding Hidden Files

```python
# Find all hidden files (starting with .)
find_files(pattern=".*", max_depth=1)

# Find .git directories
find_files(pattern=".git", file_type="d")

# Find .env files
find_files(pattern=".env*")
```

## Performance Tips

### 1. Use Specific Paths
```python
# Better: Specific directory
find_files(pattern="*.py", search_path="/home/user/project/src")

# Slower: Search from root
find_files(pattern="*.py", search_path="/")
```

### 2. Limit Search Depth
```python
# Faster: Limited depth
find_files(pattern="*.json", max_depth=3)

# Slower: Unlimited depth
find_files(pattern="*.json")
```

### 3. Use Specific Patterns
```python
# Better: Specific extension
find_files(pattern="*.py")

# Slower: Too broad
find_files(pattern="*")
```

### 4. Filter by File Type
```python
# Faster: Only files
find_files(pattern="test*", file_type="f")

# Slower: Everything
find_files(pattern="test*")
```

## Common Use Cases

### 1. Code Review
```python
# Find all source files
python_files = find_files(pattern="*.py")
js_files = find_files(pattern="*.js")
```

### 2. Configuration Audit
```python
# Find all config files
yaml_configs = find_files(pattern="*.yaml")
json_configs = find_files(pattern="*.json")
env_files = find_files(pattern=".env*")
```

### 3. Documentation Search
```python
# Find all documentation
md_files = find_files(pattern="*.md")
txt_files = find_files(pattern="*.txt")
```

### 4. Test Discovery
```python
# Find all test files
test_files = find_files(pattern="test_*.py")
spec_files = find_files(pattern="*.spec.js")
```

### 5. Log Analysis
```python
# Find all log files
log_files = find_files(pattern="*.log")
```

### 6. Backup Preparation
```python
# Find important files to backup
important_files = find_files(pattern="*{config,secret,key}*")
```

## Pattern Troubleshooting

### Problem: No Results Found

**Check:**
1. Current directory: `print_working_directory()`
2. Pattern syntax: wildcards vs regex
3. Case sensitivity: try `case_sensitive=False`
4. File type: ensure files exist, not just directories
5. Search path: use absolute path

**Example:**
```python
# If this returns nothing
find_files(pattern="readme.md")

# Try case-insensitive
find_files(pattern="readme.md", case_sensitive=False)

# Or wildcard
find_files(pattern="README*", case_sensitive=False)
```

### Problem: Too Many Results

**Solutions:**
1. Narrow the pattern
2. Specify search_path
3. Add max_depth
4. Filter by file_type
5. Increase MAX_FIND_RESULTS env var

**Example:**
```python
# Too many results
find_files(pattern="*.py")

# Narrow it down
find_files(pattern="*.py", search_path="./src", max_depth=2)
```

### Problem: Wrong Pattern Type

**Remember:**
- Use `find_files()` for wildcards: `*.py`, `test_*`
- Use `find_files_by_regex()` for regex: `^test_.*\.py$`

## Escape Special Characters

When searching for files with special characters in names:

```python
# Literal dot
find_files(pattern="file.txt")  # Works for wildcards

# Literal brackets
find_files(pattern="file\[1\].txt")  # Escape in regex mode
```

## Summary

### Quick Reference

| Task | Pattern | Function |
|------|---------|----------|
| All Python files | `*.py` | `find_files()` |
| Files starting with "test" | `test_*` | `find_files()` |
| Files containing "config" | `*config*` | `find_files()` |
| Regex pattern | `^[a-z]+\.log$` | `find_files_by_regex()` |
| Case-insensitive | `readme*` | `find_files(..., case_sensitive=False)` |
| Limited depth | `*.json` | `find_files(..., max_depth=2)` |
| Only directories | `*test*` | `find_files(..., file_type='d')` |
| Specific directory | `*.py` | `find_files(..., search_path='/path')` |

---

**Best Practice:** Start with simple wildcards, use regex only when needed for complex patterns.

