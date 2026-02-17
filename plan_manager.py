"""
Plan Manager for Query Decomposition Plans
Uses anchor-based format for easy grep/bash searching similar to agent_memory.py
"""

import os
import re
import json
import uuid
import subprocess
import shlex
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from colorama import Fore, init

init(autoreset=True)


class PlanManager:
    """
    Manages stepwise plans from query decomposition.
    Uses grep-friendly anchor format for easy searching and updates.
    """
    
    def __init__(self, plan_file: str = "stepwised_plan.txt", plans_dir: str = None):
        """
        Initialize the plan manager.
        
        Args:
            plan_file: Name of the plan file (default: stepwised_plan.txt)
            plans_dir: Directory to store plans (default: current directory)
        """
        if plans_dir is None:
            plans_dir = Path.cwd()
        else:
            plans_dir = Path(plans_dir)
        
        plans_dir.mkdir(parents=True, exist_ok=True)
        self.plan_file = plans_dir / plan_file
        self.plans_count = 0
        
        # Create file with header if it doesn't exist
        if not self.plan_file.exists():
            self._initialize_file()
        else:
            self._load_plan_count()
        
        print(Fore.GREEN + f"✓ Plan Manager initialized", Fore.RESET)
        print(Fore.CYAN + f"  Plan file: {self.plan_file}", Fore.RESET)
    
    def _initialize_file(self):
        """Initialize the plan file with header using shell commands."""
        file_path = str(self.plan_file)
        timestamp = datetime.now().isoformat()
        
        # Use cat with heredoc to write header (shell command)
        header = f"""================================================================================
                    QUERY DECOMPOSITION PLANS
================================================================================

@FILE_CREATED:{timestamp}@
@LAST_UPDATED:{timestamp}@
@TOTAL_PLANS:0@

This file stores query decomposition plans in a grep-friendly anchor format.
Each plan can be easily searched, modified, or have steps added/updated.

================================================================================

"""
        # Use shell command to write file
        try:
            subprocess.run(
                ['bash', '-c', f'cat > {shlex.quote(file_path)} << \'EOF\'\n{header}EOF'],
                check=True,
                capture_output=True
            )
            self.plans_count = 0
            print(Fore.GREEN + f"✓ Created new plan file: {self.plan_file}", Fore.RESET)
        except subprocess.CalledProcessError as e:
            # Fallback to Python if shell fails
            with open(self.plan_file, 'w', encoding='utf-8') as f:
                f.write(header)
            self.plans_count = 0
            print(Fore.GREEN + f"✓ Created new plan file: {self.plan_file}", Fore.RESET)
    
    def _load_plan_count(self):
        """Load the current plan count from file using grep."""
        try:
            file_path = str(self.plan_file)
            
            # Use grep to extract TOTAL_PLANS
            result = subprocess.run(
                ['grep', '-o', '@TOTAL_PLANS:[0-9]\+@', file_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0 and result.stdout.strip():
                match = re.search(r'@TOTAL_PLANS:(\d+)@', result.stdout)
                if match:
                    self.plans_count = int(match.group(1))
                else:
                    # Fallback: count plan markers using grep
                    count_result = subprocess.run(
                        ['grep', '-c', '<<<PLAN:', file_path],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    if count_result.returncode == 0:
                        self.plans_count = int(count_result.stdout.strip() or 0)
                    else:
                        self.plans_count = 0
            else:
                # Count plan markers using grep
                count_result = subprocess.run(
                    ['grep', '-c', '<<<PLAN:', file_path],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if count_result.returncode == 0:
                    self.plans_count = int(count_result.stdout.strip() or 0)
                else:
                    self.plans_count = 0
        except Exception as e:
            print(Fore.YELLOW + f"Warning: Could not load plan count: {e}", Fore.RESET)
            self.plans_count = 0
    
    def _update_metadata_fast(self):
        """Update metadata using sed (fast - sub-millisecond)."""
        try:
            file_path = str(self.plan_file)
            timestamp = datetime.now().isoformat()
            
            # Use sed to update LAST_UPDATED in-place
            subprocess.run(
                ['sed', '-i', f's/@LAST_UPDATED:[^@]*@/@LAST_UPDATED:{timestamp}@/', file_path],
                check=False,
                capture_output=True
            )
        except Exception:
            # Fallback to Python method
            self._update_metadata()
    
    def _update_metadata(self):
        """Update the metadata in the file header using sed."""
        try:
            file_path = str(self.plan_file)
            timestamp = datetime.now().isoformat()
            
            # Use sed to update both metadata fields in-place
            # Update LAST_UPDATED
            subprocess.run(
                ['sed', '-i', f's/@LAST_UPDATED:[^@]*@/@LAST_UPDATED:{timestamp}@/', file_path],
                check=False,
                capture_output=True
            )
            
            # Update TOTAL_PLANS
            subprocess.run(
                ['sed', '-i', f's/@TOTAL_PLANS:[0-9]\\+@/@TOTAL_PLANS:{self.plans_count}@/', file_path],
                check=False,
                capture_output=True
            )
        except Exception as e:
            print(Fore.RED + f"Error updating metadata: {e}", Fore.RESET)
    
    def write_plan(
        self,
        user_query: str,
        decomposition_result: Dict[str, Any],
        context: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Write a new plan to the file.
        
        Args:
            user_query: The original user query
            decomposition_result: The decomposition result from query_decomposition_call
            context: Optional context (chapter_name, sub_topic, etc.)
        
        Returns:
            plan_id: Unique identifier for this plan
        """
        self.plans_count += 1
        plan_id = str(uuid.uuid4())
        plan_num = f"{self.plans_count:06d}"
        timestamp = datetime.now().isoformat()
        
        multi_steps = decomposition_result.get("multi_steps", False)
        output_steps = decomposition_result.get("output_steps", [])
        
        # Build the plan entry
        plan_entry = f"\n<<<PLAN:{plan_num}>>>\n"
        plan_entry += f"@PLAN_ID:{plan_id}@\n"
        plan_entry += f"@PLAN_NUMBER:{plan_num}@\n"
        plan_entry += f"@TIMESTAMP:{timestamp}@\n"
        plan_entry += f"@MULTI_STEPS:{str(multi_steps).lower()}@\n"
        plan_entry += f"@TOTAL_STEPS:{len(output_steps)}@\n"
        plan_entry += f"\n>>>QUERY:{plan_num}>>>\n{user_query}\n<<<QUERY:{plan_num}<<<\n"
        
        # Add context if provided
        if context:
            plan_entry += f"\n>>>CONTEXT:{plan_num}>>>\n"
            for key, value in context.items():
                if value:
                    plan_entry += f"@{key.upper()}:{value}@\n"
            plan_entry += f"<<<CONTEXT:{plan_num}<<<\n"
        
        # Add steps
        plan_entry += f"\n>>>STEPS:{plan_num}>>>\n"
        for step in output_steps:
            step_nr = step.get("step_nr", 0)
            skill_name = step.get("skill_name", step.get("tool_name", "N/A"))
            rationale = step.get("rationale", "N/A")
            sub_query = step.get("sub_query", "")
            
            plan_entry += f"\n---STEP:{step_nr:03d}:{plan_num}---\n"
            plan_entry += f"@STEP_NR:{step_nr}@\n"
            plan_entry += f"@SKILL_NAME:{skill_name}@\n"
            plan_entry += f"@RATIONALE:{rationale}@\n"
            if sub_query:
                plan_entry += f"@SUB_QUERY:{sub_query}@\n"
            plan_entry += f"@STATUS:pending@\n"  # pending, in_progress, completed, failed
            plan_entry += f"@RESULT:@\n"  # Execution result (filled after step execution)
            plan_entry += f"---END_STEP:{step_nr:03d}:{plan_num}---\n"
        
        plan_entry += f"<<<STEPS:{plan_num}<<<\n"
        plan_entry += f"\n<<<END_PLAN:{plan_num}>>>\n"
        plan_entry += "\n" + "="*80 + "\n"
        
        # Append to file using shell command (cat or echo)
        try:
            file_path = str(self.plan_file)
            # Use cat with heredoc to append (shell command)
            subprocess.run(
                ['bash', '-c', f'cat >> {shlex.quote(file_path)} << \'EOF\'\n{plan_entry}EOF'],
                check=True,
                capture_output=True
            )
            
            self._update_metadata()
            print(Fore.GREEN + f"✓ Plan {plan_num} written successfully (ID: {plan_id})", Fore.RESET)
            return plan_id
        except subprocess.CalledProcessError:
            # Fallback to Python if shell fails
            try:
                with open(self.plan_file, 'a', encoding='utf-8') as f:
                    f.write(plan_entry)
                self._update_metadata()
                print(Fore.GREEN + f"✓ Plan {plan_num} written successfully (ID: {plan_id})", Fore.RESET)
                return plan_id
            except Exception as e:
                print(Fore.RED + f"Error writing plan: {e}", Fore.RESET)
                return None
        except Exception as e:
            print(Fore.RED + f"Error writing plan: {e}", Fore.RESET)
            return None
    
    def find_plan_by_query(self, query: str, exact_match: bool = False) -> List[str]:
        """
        Find plans by searching the query text using grep/sed.
        
        Args:
            query: Query text to search for
            exact_match: If True, only return exact matches
        
        Returns:
            List of plan IDs that match
        """
        try:
            file_path = str(self.plan_file)
            plan_ids = []
            
            # Use grep to find lines containing the query (case-insensitive)
            if exact_match:
                # For exact match, use grep with word boundaries
                grep_cmd = ['grep', '-i', '-B', '5', '-A', '50', f'^{re.escape(query)}$', file_path]
            else:
                # For partial match, use grep with the query text
                grep_cmd = ['grep', '-i', '-B', '5', '-A', '50', query, file_path]
            
            result = subprocess.run(
                grep_cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0 and result.stdout:
                # Extract plan blocks that contain the query
                # Use sed to extract plan blocks, then parse with Python regex
                # Get all plan blocks
                sed_result = subprocess.run(
                    ['sed', '-n', '/<<<PLAN:/,/<<<END_PLAN:/p', file_path],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if sed_result.returncode == 0:
                    content = sed_result.stdout
                    pattern = r'<<<PLAN:(\d{6})>>>(.*?)<<<END_PLAN:\1>>>'
                    matches = re.finditer(pattern, content, re.DOTALL)
                    
                    for match in matches:
                        plan_content = match.group(2)
                        query_match = re.search(r'>>>QUERY:\d{6}>>>\n(.*?)\n<<<QUERY:\d{6}<<<', plan_content, re.DOTALL)
                        
                        if query_match:
                            stored_query = query_match.group(1).strip()
                            if exact_match:
                                if stored_query.lower() == query.lower():
                                    id_match = re.search(r'@PLAN_ID:([^@]+)@', plan_content)
                                    if id_match:
                                        plan_ids.append(id_match.group(1))
                            else:
                                if query.lower() in stored_query.lower():
                                    id_match = re.search(r'@PLAN_ID:([^@]+)@', plan_content)
                                    if id_match:
                                        plan_ids.append(id_match.group(1))
            
            return plan_ids
        except Exception as e:
            print(Fore.RED + f"Error finding plans: {e}", Fore.RESET)
            return []
    
    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a plan by its ID using grep/sed.
        
        Args:
            plan_id: The plan ID to retrieve
        
        Returns:
            Dictionary containing the plan details, or None if not found
        """
        try:
            file_path = str(self.plan_file)
            
            # Use sed to extract plan blocks, then find the one with matching plan_id
            sed_result = subprocess.run(
                ['sed', '-n', '/<<<PLAN:/,/<<<END_PLAN:/p', file_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            if sed_result.returncode != 0:
                return None
            
            content = sed_result.stdout
            
            # Find the plan
            pattern = r'<<<PLAN:(\d{6})>>>(.*?)<<<END_PLAN:\1>>>'
            matches = re.finditer(pattern, content, re.DOTALL)
            
            for match in matches:
                plan_content = match.group(2)
                id_match = re.search(r'@PLAN_ID:([^@]+)@', plan_content)
                
                if id_match and id_match.group(1) == plan_id:
                    # Parse the plan
                    plan_num = match.group(1)
                    
                    # Extract metadata
                    timestamp_match = re.search(r'@TIMESTAMP:([^@]+)@', plan_content)
                    multi_steps_match = re.search(r'@MULTI_STEPS:([^@]+)@', plan_content)
                    total_steps_match = re.search(r'@TOTAL_STEPS:([^@]+)@', plan_content)
                    
                    # Extract query
                    query_match = re.search(r'>>>QUERY:\d{6}>>>\n(.*?)\n<<<QUERY:\d{6}<<<', plan_content, re.DOTALL)
                    
                    # Extract steps
                    steps = []
                    step_pattern = r'---STEP:(\d{3}):\d{6}---(.*?)---END_STEP:\1:\d{6}---'
                    step_matches = re.finditer(step_pattern, plan_content, re.DOTALL)
                    
                    for step_match in step_matches:
                        step_content = step_match.group(2)
                        step_nr_match = re.search(r'@STEP_NR:([^@]+)@', step_content)
                        skill_match = re.search(r'@SKILL_NAME:([^@]+)@', step_content)
                        rationale_match = re.search(r'@RATIONALE:([^@]+)@', step_content)
                        sub_query_match = re.search(r'@SUB_QUERY:([^@]+)@', step_content)
                        status_match = re.search(r'@STATUS:([^@]+)@', step_content)
                        result_match = re.search(r'@RESULT:([^@]*)@', step_content)
                        
                        step = {
                            "step_nr": int(step_nr_match.group(1)) if step_nr_match else 0,
                            "skill_name": skill_match.group(1) if skill_match else "N/A",
                            "rationale": rationale_match.group(1) if rationale_match else "N/A",
                            "sub_query": sub_query_match.group(1) if sub_query_match else "",
                            "status": status_match.group(1) if status_match else "pending",
                            "result": result_match.group(1) if result_match else ""
                        }
                        steps.append(step)
                    
                    return {
                        "plan_id": plan_id,
                        "plan_number": plan_num,
                        "timestamp": timestamp_match.group(1) if timestamp_match else None,
                        "query": query_match.group(1).strip() if query_match else None,
                        "multi_steps": multi_steps_match.group(1) == "true" if multi_steps_match else False,
                        "total_steps": int(total_steps_match.group(1)) if total_steps_match else 0,
                        "steps": steps
                    }
            
            return None
        except Exception as e:
            print(Fore.RED + f"Error getting plan: {e}", Fore.RESET)
            return None
    
    def update_step_status(self, plan_id: str, step_nr: int, status: str, result: str = None) -> bool:
        """
        Update the status and optionally the result of a specific step in a plan.
        Uses direct sed commands for sub-millisecond performance (no Python file I/O overhead).
        
        Args:
            plan_id: The plan ID
            step_nr: The step number to update
            status: New status (pending, in_progress, completed, failed)
            result: Optional execution result/output to store
        
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = str(self.plan_file)
            step_nr_padded = f"{step_nr:03d}"
            
            # Sanitize result to avoid breaking the format (remove @ symbols, limit length)
            if result is not None:
                sanitized_result = result.replace('@', '(at)').replace('\n', ' ').replace('"', '\\"')[:500]
            else:
                sanitized_result = None
            
            # Use sed for in-place editing (Ubuntu/Linux native)
            # Escape special characters for sed (need to escape /, &, and backslashes)
            escaped_status_sed = status.replace('\\', '\\\\').replace('/', '\\/').replace('&', '\\&')
            escaped_plan_id_sed = plan_id.replace('\\', '\\\\').replace('/', '\\/').replace('&', '\\&')
            
            # Build sed command to update status and result within the plan block
            # Use sed with address ranges: /@PLAN_ID:...@/,/<<<END_PLAN:/ to target the plan block
            # Then within that, target the step: /---STEP:...---/,/---STEP:/ or /---END_STEP:...---/
            sed_commands = []
            
            # Update STATUS within the plan block and step range
            # Build sed command using string concatenation to avoid f-string brace issues
            sed_cmd_status = (
                'sed -i.tmp -E "/@PLAN_ID:' + escaped_plan_id_sed + '@/,/<<<END_PLAN:/'
                '{ /---STEP:' + step_nr_padded + ':[0-9]+---/,/---END_STEP:' + step_nr_padded + ':[0-9]+---/'
                '{ s/@STATUS:[^@]+@/@STATUS:' + escaped_status_sed + '@/; } }"'
            )
            sed_commands.append(sed_cmd_status)
            
            # Update RESULT if provided
            if sanitized_result is not None:
                escaped_result_sed = sanitized_result.replace('\\', '\\\\').replace('/', '\\/').replace('&', '\\&')
                sed_cmd_result = (
                    'sed -i.tmp -E "/@PLAN_ID:' + escaped_plan_id_sed + '@/,/<<<END_PLAN:/'
                    '{ /---STEP:' + step_nr_padded + ':[0-9]+---/,/---END_STEP:' + step_nr_padded + ':[0-9]+---/'
                    '{ s/@RESULT:[^@]*@/@RESULT:' + escaped_result_sed + '@/; } }"'
                )
                sed_commands.append(sed_cmd_result)
            
            # Execute sed commands
            try:
                for sed_cmd in sed_commands:
                    proc = subprocess.run(
                        ['bash', '-c', f'{sed_cmd} {shlex.quote(file_path)}'],
                        capture_output=True,
                        check=False,
                        timeout=2
                    )
                    if proc.returncode != 0:
                        raise subprocess.CalledProcessError(proc.returncode, sed_cmd)
                
                # Remove temp file
                try:
                    os.remove(f"{file_path}.tmp")
                except:
                    pass
                
                self._update_metadata_fast()
                result_msg = f" with result" if result else ""
                print(Fore.GREEN + f"✓ Updated step {step_nr} status to '{status}'{result_msg} (via sed)", Fore.RESET)
                return True
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
                # Fallback to Python method
                pass
            
            # Final fallback to Python method
            return self._update_step_status_python_fallback(plan_id, step_nr, status, result)
            
        except Exception as e:
            print(Fore.RED + f"Error updating step status: {e}", Fore.RESET)
            # Fallback to Python method
            try:
                return self._update_step_status_python_fallback(plan_id, step_nr, status, result)
            except Exception as e2:
                print(Fore.RED + f"Fallback also failed: {e2}", Fore.RESET)
                return False
    
    def _update_step_status_python_fallback(self, plan_id: str, step_nr: int, status: str, result: str = None) -> bool:
        """Fallback Python-based implementation if sed/perl fails - uses minimal file I/O"""
        # Use cat to read file content
        try:
            proc = subprocess.run(
                ['cat', str(self.plan_file)],
                capture_output=True,
                text=True,
                check=True
            )
            content = proc.stdout
        except subprocess.CalledProcessError:
            # Last resort: Python file I/O
            with open(self.plan_file, 'r', encoding='utf-8') as f:
                content = f.read()
        
        pattern = r'<<<PLAN:(\d{6})>>>(.*?)<<<END_PLAN:\1>>>'
        
        def update_plan(match):
            plan_content = match.group(2)
            id_match = re.search(r'@PLAN_ID:([^@]+)@', plan_content)
            
            if id_match and id_match.group(1) == plan_id:
                step_pattern = f'(---STEP:{step_nr:03d}:\\d{{6}}---.*?)@STATUS:[^@]+@'
                plan_content = re.sub(
                    step_pattern,
                    f'\\1@STATUS:{status}@',
                    plan_content,
                    flags=re.DOTALL
                )
                
                if result is not None:
                    sanitized_result = result.replace('@', '(at)').replace('\n', ' ')[:500]
                    result_pattern = f'(---STEP:{step_nr:03d}:\\d{{6}}---.*?)@RESULT:[^@]*@'
                    plan_content = re.sub(
                        result_pattern,
                        f'\\1@RESULT:{sanitized_result}@',
                        plan_content,
                        flags=re.DOTALL
                    )
            
            return f'<<<PLAN:{match.group(1)}>>>{plan_content}<<<END_PLAN:{match.group(1)}>>>'
        
        updated_content = re.sub(pattern, update_plan, content, flags=re.DOTALL)
        
        # Use cat to write file content
        try:
            proc = subprocess.run(
                ['bash', '-c', f'cat > {shlex.quote(str(self.plan_file))}'],
                input=updated_content,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError:
            # Last resort: Python file I/O
            with open(self.plan_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
        
        self._update_metadata()
        return True
    
    def add_step_to_plan(
        self,
        plan_id: str,
        skill_name: str,
        rationale: str,
        sub_query: str = "",
        status: str = "pending"
    ) -> bool:
        """
        Add a new step to an existing plan using shell commands.
        
        Args:
            plan_id: The plan ID
            skill_name: Name of the skill for this step
            rationale: Rationale for this step
            sub_query: Optional sub-query for this step
            status: Initial status (default: pending)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = str(self.plan_file)
            
            # Use cat to read file content
            try:
                proc = subprocess.run(
                    ['cat', file_path],
                    capture_output=True,
                    text=True,
                    check=True
                )
                content = proc.stdout
            except subprocess.CalledProcessError:
                # Fallback to Python file I/O
                with open(self.plan_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            # Find the plan
            pattern = r'<<<PLAN:(\d{6})>>>(.*?)<<<END_PLAN:\1>>>'
            
            def add_step(match):
                plan_num = match.group(1)
                plan_content = match.group(2)
                id_match = re.search(r'@PLAN_ID:([^@]+)@', plan_content)
                
                if id_match and id_match.group(1) == plan_id:
                    # Get current total steps
                    total_steps_match = re.search(r'@TOTAL_STEPS:(\d+)@', plan_content)
                    current_total = int(total_steps_match.group(1)) if total_steps_match else 0
                    new_step_nr = current_total + 1
                    
                    # Update total steps count using sed
                    escaped_plan_id = shlex.quote(plan_id).strip("'\"")
                    subprocess.run(
                        ['sed', '-i', f'/@PLAN_ID:{escaped_plan_id}@/,/<<<END_PLAN:/s/@TOTAL_STEPS:[0-9]\\+@/@TOTAL_STEPS:{new_step_nr}@/', file_path],
                        check=False,
                        capture_output=True
                    )
                    
                    # Create new step entry
                    new_step = f"\n---STEP:{new_step_nr:03d}:{plan_num}---\n"
                    new_step += f"@STEP_NR:{new_step_nr}@\n"
                    new_step += f"@SKILL_NAME:{skill_name}@\n"
                    new_step += f"@RATIONALE:{rationale}@\n"
                    if sub_query:
                        new_step += f"@SUB_QUERY:{sub_query}@\n"
                    new_step += f"@STATUS:{status}@\n"
                    new_step += f"@RESULT:@\n"
                    new_step += f"---END_STEP:{new_step_nr:03d}:{plan_num}---\n"
                    
                    # Insert before the closing STEPS marker using sed
                    # Use sed's insert command (i\) to insert before the pattern
                    steps_marker = f"<<<STEPS:{plan_num}<<<"
                    escaped_steps_marker = steps_marker.replace('/', '\\/').replace('&', '\\&')
                    
                    # Escape new_step for sed insert command
                    # sed's i\ command needs each line to be escaped
                    new_step_lines = new_step.split('\n')
                    escaped_step_sed = '\\n'.join([line.replace('\\', '\\\\').replace('/', '\\/').replace('&', '\\&') for line in new_step_lines])
                    
                    # Use sed to insert before the marker within the plan block
                    try:
                        # Create a temporary file with the new step content
                        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
                            tmp.write(new_step)
                            tmp_step_file = tmp.name
                        
                        # Use sed to insert the content from temp file before the marker
                        # sed '/pattern/r file' reads file and inserts it after pattern
                        # We need before, so we'll use a different approach: use sed's i\ command via bash
                        # Pre-escape values to avoid backslashes in f-string expressions
                        escaped_plan_id_sed_for_insert = escaped_plan_id.replace('/', '\\/').replace('&', '\\&')
                        escaped_new_step = new_step.replace('$', '\\$').replace('`', '\\`')
                        bash_script = f'''
                        # Read temp file content
                        step_content=$(cat {shlex.quote(tmp_step_file)})
                        # Use sed to insert before marker within plan block
                        sed -i.tmp -E "/@PLAN_ID:{escaped_plan_id_sed_for_insert}@/,/<<<END_PLAN:/{{
                            /{escaped_steps_marker}/i\\
{escaped_new_step}
                        }}" {shlex.quote(file_path)}
                        '''
                        proc = subprocess.run(
                            ['bash', '-c', bash_script],
                            capture_output=True,
                            check=False,
                            timeout=2
                        )
                        
                        # Clean up temp file
                        try:
                            os.remove(tmp_step_file)
                            os.remove(f"{file_path}.tmp")
                        except:
                            pass
                        
                        if proc.returncode == 0:
                            # Success, skip Python fallback
                            self._update_metadata()
                            print(Fore.GREEN + f"✓ Added new step to plan {plan_id}", Fore.RESET)
                            return True
                    except Exception:
                        pass
                    
                    # Fallback: use Python regex replacement
                    plan_content = plan_content.replace(
                        f"<<<STEPS:{plan_num}<<<",
                        f"{new_step}<<<STEPS:{plan_num}<<<"
                    )
                
                return f'<<<PLAN:{plan_num}>>>{plan_content}<<<END_PLAN:{plan_num}>>>'
            
            # If perl failed, use Python regex
            updated_content = re.sub(pattern, add_step, content, flags=re.DOTALL)
            
            # Write using cat
            try:
                subprocess.run(
                    ['bash', '-c', f'cat > {shlex.quote(file_path)}'],
                    input=updated_content,
                    text=True,
                    check=True
                )
            except subprocess.CalledProcessError:
                # Fallback to Python file I/O
                with open(self.plan_file, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
            
            self._update_metadata()
            print(Fore.GREEN + f"✓ Added new step to plan {plan_id}", Fore.RESET)
            return True
        except Exception as e:
            print(Fore.RED + f"Error adding step to plan: {e}", Fore.RESET)
            return False
    
    def get_search_examples(self) -> str:
        """
        Return examples of bash/grep commands to search the plan file.
        Similar to agent_memory.py's get_search_examples().
        """
        examples = f"""
        === GREP/BASH SEARCH EXAMPLES FOR {self.plan_file} ===
        
        # Find all plans (just markers):
        grep '<<<PLAN:' {self.plan_file}
        
        # Find specific plan WITH CONTENT (shows 50 lines after):
        grep -A 50 '<<<PLAN:000005>>>' {self.plan_file}
        
        # View full plan for plan number 3:
        sed -n '/<<<PLAN:000003>>>/,/<<<END_PLAN:000003>>>/p' {self.plan_file}
        
        # Find all queries WITH CONTENT:
        grep -A 2 '>>>QUERY:' {self.plan_file}
        
        # Find plans containing specific keyword in query:
        grep -i -C 10 "calendar" {self.plan_file}
        
        # Get total number of plans:
        grep '@TOTAL_PLANS:' {self.plan_file}
        
        # Find all multi-step plans:
        grep -B 2 '@MULTI_STEPS:true@' {self.plan_file}
        
        # Find all single-step plans:
        grep -B 2 '@MULTI_STEPS:false@' {self.plan_file}
        
        # Count total plans:
        grep -c '<<<PLAN:' {self.plan_file}
        
        # Find all steps with specific skill:
        grep '@SKILL_NAME:calendar-assistant@' {self.plan_file}
        
        # Find all pending steps:
        grep '@STATUS:pending@' {self.plan_file}
        
        # Find all completed steps:
        grep '@STATUS:completed@' {self.plan_file}
        
        # Get all timestamps:
        grep '@TIMESTAMP:' {self.plan_file}
        
        # Extract plan numbers only:
        grep -o '<<<PLAN:[0-9]\\{{6}}>>>' {self.plan_file}
        
        # Find plan by ID:
        grep -A 50 '@PLAN_ID:your-uuid-here@' {self.plan_file}
        
        # Search for specific step number across all plans:
        grep '@STEP_NR:3@' {self.plan_file}
        
        # Find plans by date:
        grep '@TIMESTAMP:2026-02-' {self.plan_file}
        
        # Count steps per plan:
        grep '@TOTAL_STEPS:' {self.plan_file}
        """
        return examples
    
    def list_all_plans(self) -> List[Dict[str, Any]]:
        """
        List all plans with basic metadata using shell commands.
        
        Returns:
            List of dictionaries with plan summaries
        """
        try:
            file_path = str(self.plan_file)
            
            # Use sed to extract all plan blocks
            sed_result = subprocess.run(
                ['sed', '-n', '/<<<PLAN:/,/<<<END_PLAN:/p', file_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            if sed_result.returncode != 0:
                # Fallback: use cat to read entire file
                try:
                    cat_result = subprocess.run(
                        ['cat', file_path],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    content = cat_result.stdout
                except subprocess.CalledProcessError:
                    # Last resort: Python file I/O
                    with open(self.plan_file, 'r', encoding='utf-8') as f:
                        content = f.read()
            else:
                content = sed_result.stdout
            
            plans = []
            pattern = r'<<<PLAN:(\d{6})>>>(.*?)<<<END_PLAN:\1>>>'
            matches = re.finditer(pattern, content, re.DOTALL)
            
            for match in matches:
                plan_num = match.group(1)
                plan_content = match.group(2)
                
                # Extract basic info
                id_match = re.search(r'@PLAN_ID:([^@]+)@', plan_content)
                timestamp_match = re.search(r'@TIMESTAMP:([^@]+)@', plan_content)
                query_match = re.search(r'>>>QUERY:\d{6}>>>\n(.*?)\n<<<QUERY:\d{6}<<<', plan_content, re.DOTALL)
                multi_steps_match = re.search(r'@MULTI_STEPS:([^@]+)@', plan_content)
                total_steps_match = re.search(r'@TOTAL_STEPS:([^@]+)@', plan_content)
                
                plans.append({
                    "plan_number": plan_num,
                    "plan_id": id_match.group(1) if id_match else None,
                    "timestamp": timestamp_match.group(1) if timestamp_match else None,
                    "query": query_match.group(1).strip() if query_match else None,
                    "multi_steps": multi_steps_match.group(1) == "true" if multi_steps_match else False,
                    "total_steps": int(total_steps_match.group(1)) if total_steps_match else 0
                })
            
            return plans
        except Exception as e:
            print(Fore.RED + f"Error listing plans: {e}", Fore.RESET)
            return []


# Example usage
if __name__ == "__main__":
    # Initialize plan manager
    pm = PlanManager(plans_dir=".")
    
    print("\n" + "="*80)
    print("PLAN MANAGER TESTING")
    print("="*80)
    
    # Test case 1: Simple single-step plan
    print("\n--- Test 1: Single-step plan ---")
    plan1 = {
        "multi_steps": False,
        "output_steps": [
            {
                "step_nr": 1,
                "skill_name": "calendar-assistant",
                "rationale": "User wants to book a calendar event",
                "sub_query": "schedule a meeting tomorrow at 2pm"
            }
        ]
    }
    plan_id_1 = pm.write_plan(
        user_query="schedule a meeting tomorrow at 2pm",
        decomposition_result=plan1,
        context={"chapter_name": "Time Management", "sub_topic": "Calendar Basics"}
    )
    
    # Test case 2: Multi-step plan
    print("\n--- Test 2: Multi-step plan ---")
    plan2 = {
        "multi_steps": True,
        "output_steps": [
            {
                "step_nr": 1,
                "skill_name": "calendar-assistant",
                "rationale": "First book the time slot for creative work",
                "sub_query": "book 1 hour tomorrow for creative work"
            },
            {
                "step_nr": 2,
                "skill_name": "nvidia-ideagen",
                "rationale": "Generate creative ideas to help user get started",
                "sub_query": "Generate ideas for creative work"
            },
            {
                "step_nr": 3,
                "skill_name": "final_response",
                "rationale": "Combine results from both skills",
                "sub_query": "Summarize booked time and generated ideas"
            }
        ]
    }
    plan_id_2 = pm.write_plan(
        user_query="book 1 hour tomorrow and give me creative ideas",
        decomposition_result=plan2,
        context={"chapter_name": "Project Planning", "sub_topic": "Creative Sessions"}
    )
    
    # Test case 3: Find plans
    print("\n--- Test 3: Find plans by query ---")
    found_plans = pm.find_plan_by_query("meeting")
    print(f"Found {len(found_plans)} plan(s) with 'meeting': {found_plans}")
    
    # Test case 4: Retrieve plan
    print("\n--- Test 4: Retrieve plan ---")
    if plan_id_1:
        retrieved_plan = pm.get_plan(plan_id_1)
        print(f"Retrieved plan: {json.dumps(retrieved_plan, indent=2)}")
    
    # Test case 5: Update step status
    print("\n--- Test 5: Update step status ---")
    if plan_id_2:
        pm.update_step_status(plan_id_2, 1, "completed")
        pm.update_step_status(plan_id_2, 2, "in_progress")
    
    # Test case 6: Add step to plan
    print("\n--- Test 6: Add new step to plan ---")
    if plan_id_2:
        pm.add_step_to_plan(
            plan_id_2,
            skill_name="summary",
            rationale="Additional summary needed",
            sub_query="Provide final summary",
            status="pending"
        )
    
    # Test case 7: List all plans
    print("\n--- Test 7: List all plans ---")
    all_plans = pm.list_all_plans()
    print(f"\nTotal plans: {len(all_plans)}")
    for plan in all_plans:
        print(f"  Plan {plan['plan_number']}: {plan['query'][:50]}... ({plan['total_steps']} steps)")
    
    # Test case 8: Show grep examples
    print("\n--- Test 8: Grep search examples ---")
    print(pm.get_search_examples())
    
    print("\n" + "="*80)
    print("Testing Complete!")
    print(f"Check the file: {pm.plan_file}")
    print("="*80)

