"""
Traditional React Agent using LangChain's create_agent
Implements query decomposition routing and sequential tool execution
"""

import json
import os
import time
import re
import requests
from pathlib import Path
from typing import Any, Dict, List, Annotated, Sequence, TypedDict, Literal, Optional, Tuple

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, ToolMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.tools import StructuredTool
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import AgentMiddleware, before_model, after_model
from colorama import Fore, Style
# Import the skill loader from tranditional_tool_calling
from tranditional_tool_calling import OldWays
# Import the LLM instance from query_decomposition (already configured based on USE_SELF_HOSTED_LLM)
from query_decomposition import llm as query_decomposition_llm
# Note: We no longer use query_decomposition_call - the LLM constructs tool calls directly


# Note: Query decomposition prompt structure is now embedded in middleware system prompt
# We no longer use a separate QUERY_DECOMPOSITION_PROMPT constant


class CacheMetricsTracker:
    """
    Helper class to track KV cache hit rate metrics for tool calling scenarios.
    Tracks incremental metrics (before/after) rather than cumulative totals.
    """
    
    def __init__(self, metrics_url: str = "http://localhost:8000/v1/metrics"):
        self.metrics_url = metrics_url
        self.baseline_queries = None
        self.baseline_hits = None
    
    def _get_cache_metrics(self) -> Optional[Tuple[float, float]]:
        """
        Fetch current cache metrics from vLLM.
        
        Returns:
            Tuple of (queries_total, hits_total) or None if unavailable
        """
        try:
            response = requests.get(self.metrics_url, timeout=2)
            response.raise_for_status()
            
            query_count = None
            hits = None
            
            for line in response.text.split('\n'):
                # Match vllm:prefix_cache_queries_total with optional Prometheus labels
                match_queries = re.match(r'^vllm:prefix_cache_queries_total(?:\{[^}]+\})?\s+([\d.]+)', line)
                if match_queries:
                    query_count = float(match_queries.group(1))
                
                # Match vllm:prefix_cache_hits_total with optional Prometheus labels
                match_hits = re.match(r'^vllm:prefix_cache_hits_total(?:\{[^}]+\})?\s+([\d.]+)', line)
                if match_hits:
                    hits = float(match_hits.group(1))
            
            if query_count is not None and hits is not None:
                return (query_count, hits)
            return None
        except Exception:
            return None
    
    def reset_baseline(self):
        """Reset baseline metrics to current values"""
        metrics = self._get_cache_metrics()
        if metrics:
            self.baseline_queries, self.baseline_hits = metrics
        else:
            self.baseline_queries = None
            self.baseline_hits = None
    
    def get_incremental_hit_rate(self) -> Optional[float]:
        """
        Calculate incremental cache hit rate since baseline was set.
        
        Returns:
            Cache hit rate as percentage (0-100), or None if unavailable
        """
        if self.baseline_queries is None or self.baseline_hits is None:
            return None
        
        current_metrics = self._get_cache_metrics()
        if not current_metrics:
            return None
        
        current_queries, current_hits = current_metrics
        
        # Calculate incremental values
        incremental_queries = current_queries - self.baseline_queries
        incremental_hits = current_hits - self.baseline_hits
        
        if incremental_queries > 0:
            hit_rate = (incremental_hits / incremental_queries) * 100
            return hit_rate
        
        return None
    
    def get_current_hit_rate(self) -> Optional[float]:
        """
        Get current cumulative cache hit rate (not incremental).
        
        Returns:
            Cache hit rate as percentage (0-100), or None if unavailable
        """
        metrics = self._get_cache_metrics()
        if not metrics:
            return None
        
        query_count, hits = metrics
        if query_count > 0:
            return (hits / query_count) * 100
        return None


# Custom middleware for system prompt injection and cache tracking
class CustomAgentMiddleware(AgentMiddleware):
    """Middleware to inject custom system prompts and track KV cache metrics"""
    
    def __init__(self, agent_instance):
        """
        Initialize middleware with reference to agent instance
        
        Args:
            agent_instance: Reference to TraditionalReactAgent instance
        """
        self.agent = agent_instance
    
    @before_model
    def inject_system_prompt(self, state: AgentState, runtime) -> Dict[str, Any] | None:
        """
        Inject custom system prompt with plan and history before model call.
        Also tracks cache metrics before the LLM call.
        """
        # Track cache metrics before LLM call
        cache_tracker = getattr(self.agent, 'cache_tracker', None)
        if cache_tracker:
            cache_tracker.reset_baseline()
        
        messages = state.get("messages", [])
        
        # Use the is_simple_query value computed in invoke() to avoid redundant calculation
        # If not set (e.g., in edge cases), fall back to recalculating from current message
        is_simple = getattr(self.agent, 'is_simple_query', None)
        if is_simple is None:
            # Fallback: extract user input and recalculate if needed
            user_input = ""
            for msg in reversed(messages):
                if isinstance(msg, HumanMessage):
                    user_input = msg.content
                    break
            is_simple = self.agent._is_simple_query(user_input)
        
        # Update plan and history from previous tool execution results
        tool_call_map = {}
        
        # First pass: collect all tool calls
        for msg in messages:
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_call_id = tc.get('id')
                    if tool_call_id:
                        tool_call_map[tool_call_id] = {
                            'name': tc.get('name', 'unknown'),
                            'args': tc.get('args', {}),
                            'result': None
                        }
        
        # Second pass: match tool results to tool calls
        tool_calls_made = []
        tool_results_received = []
        
        for msg in messages:
            if isinstance(msg, ToolMessage):
                tool_call_id = msg.tool_call_id
                if tool_call_id in tool_call_map:
                    tool_info = tool_call_map[tool_call_id]
                    tool_result = str(msg.content)
                    tool_info['result'] = tool_result
                    
                    # Add to history if not already there
                    entry = {
                        'tool_call_id': tool_call_id,
                        'tool_name': tool_info['name'],
                        'tool_args': tool_info['args'],
                        'tool_result': tool_result
                    }
                    
                    existing_ids = [e.get('tool_call_id') for e in self.agent.tool_call_history]
                    if tool_call_id not in existing_ids:
                        self.agent.tool_call_history.append(entry)
                        tool_calls_made.append({
                            'name': tool_info['name'],
                            'args': tool_info['args']
                        })
                        tool_results_received.append(tool_result)
        
        # Update plan from tool calls
        if tool_calls_made and tool_results_received:
            self.agent._update_plan_from_tool_calls(tool_calls_made, tool_results_received)
        
        # Build system prompt
        if is_simple:
            system_prompt = """You are a helpful AI assistant. Respond naturally to greetings and simple questions."""
        else:
            available_skills = self.agent._get_available_skills_description()
            
            plan_text = ""
            if self.agent.current_plan:
                plan_text = self.agent._format_plan_as_text(self.agent.current_plan)
            
            history_section = self.agent._format_history_section()
            
            system_prompt = f"""You are a Query Decomposition Agent specialized in analyzing user queries and creating step-by-step plans.

Your task is to determine if the query requires multiple skills or can be handled by a single skill.

<Available Skills>

{available_skills}

IMPORTANT: These are the ONLY skills available. You CANNOT use any other skills not listed here.
If a query requires capabilities beyond these skills, you MUST use the "none" skill.

Additional skills:
- chitchat: For casual conversation, greetings, small talk
- final_response: For directly responding to the user (used as the final step)
- none: Use when query cannot be fulfilled with available skills

</Available Skills>

<Instructions>

1. Analyze Query Complexity:
   - ATOMIC queries: require only 1 skill (e.g., "book a meeting" or "generate ideas")
   - COMPLEX queries: require 2+ skills (e.g., "book time and generate ideas")

2. For ATOMIC Queries:
   - Set "multi_steps" to false
   - Identify the primary skill needed
   - If it's a simple greeting or question, use "final_response"
   
3. For COMPLEX Queries:
   - Set "multi_steps" to true
   - Decompose into atomic steps
   - Each step uses EXACTLY ONE skill
   - Order steps logically
   - Last step should typically be "final_response" if needed for synthesis

</Instructions>

<Context>
{plan_text}{history_section}
</Context>

You have access to tools that correspond to these skills. Use them when needed to complete the user's request."""
        
        # Remove existing system messages and add new one
        filtered_messages = [msg for msg in messages if not isinstance(msg, SystemMessage)]
        new_messages = [SystemMessage(content=system_prompt)] + filtered_messages
        
        return {"messages": new_messages}
    
    @after_model
    def track_cache_metrics(self, state: AgentState, runtime) -> Dict[str, Any] | None:
        """
        Track KV cache metrics after model call.
        Also tracks tool calls and updates metrics.
        """
        # Debug: Verify middleware is being called
        print(f"   🔍 DEBUG: track_cache_metrics called (middleware hook triggered)")
        
        messages = state.get("messages", [])
        if not messages:
            # Debug: Log when messages are empty
            print(f"   ⚠️  track_cache_metrics: No messages in state")
            return None
        
        # Find the last AIMessage (LLM response) - it might not be the very last message
        # if tool results were added after
        last_ai_message = None
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                last_ai_message = msg
                break
        
        # If no AIMessage found, still track the call (might be a different message type)
        if last_ai_message is None:
            # Still track the LLM call even if we can't find an AIMessage
            # This can happen if the message structure is different
            last_message = messages[-1]
            print(f"   ⚠️  track_cache_metrics: No AIMessage found, last message type: {type(last_message).__name__}")
            
            # Still append to metrics to count the call
            self.agent.llm_call_metrics.append({
                'cache_hit_rate': None,
                'has_tool_calls': False,
                'num_tool_calls': 0,
                'tool_names': []
            })
            return None
        
        # Track cache metrics after LLM call
        cache_tracker = getattr(self.agent, 'cache_tracker', None)
        cache_hit_rate = None
        has_tool_calls = False
        num_tool_calls_in_response = 0
        
        # Check if this LLM call resulted in tool calls
        if hasattr(last_ai_message, 'tool_calls') and last_ai_message.tool_calls:
            has_tool_calls = True
            num_tool_calls_in_response = len(last_ai_message.tool_calls)
        
        if cache_tracker:
            # Get incremental cache hit rate for THIS specific LLM call
            cache_hit_rate = cache_tracker.get_incremental_hit_rate()
            
            # Track tool-calling LLM calls with cache metrics
            if has_tool_calls and cache_hit_rate is not None:
                self.agent.tool_call_metrics.append(cache_hit_rate)
                tool_names = [tc.get('name', 'unknown') for tc in last_ai_message.tool_calls]
                print(f"   💾 LLM call cache hit rate: {cache_hit_rate:.1f}% (tool-calling decision: {', '.join(tool_names[:3])}{'...' if len(tool_names) > 3 else ''})")
            elif cache_hit_rate is not None:
                print(f"   💾 LLM call cache hit rate: {cache_hit_rate:.1f}% (response generation)")
        
        # Track all LLM calls
        tool_names = []
        if has_tool_calls and hasattr(last_ai_message, 'tool_calls'):
            tool_names = [tc.get('name', 'unknown') for tc in last_ai_message.tool_calls]
        
        # Always append to track the LLM call
        self.agent.llm_call_metrics.append({
            'cache_hit_rate': cache_hit_rate,
            'has_tool_calls': has_tool_calls,
            'num_tool_calls': num_tool_calls_in_response,
            'tool_names': tool_names
        })
        
        # Store in response metadata if available
        if cache_hit_rate is not None and hasattr(last_ai_message, 'response_metadata'):
            if last_ai_message.response_metadata is None:
                last_ai_message.response_metadata = {}
            last_ai_message.response_metadata['kv_cache_hit_rate'] = cache_hit_rate
            last_ai_message.response_metadata['has_tool_calls'] = has_tool_calls
        
        return None


class TraditionalReactAgent:
    """
    Traditional React Agent using LangChain's create_agent
    
    Uses create_agent from langchain.agents which provides a production-ready
    agent implementation with automatic tool binding and ReAct loop.
    
    Features:
    - Automatic tool binding via create_agent
    - Custom middleware for system prompt injection and KV cache tracking
    - StructuredTool integration for all skills
    - Plan and history tracking for context-aware responses
    
    Reference: https://docs.langchain.com/oss/python/langchain/agents
    """
    
    def __init__(self, skills_base_path: str | Path, llm=None, exclude_skills: Optional[List[str]] = None):
        """
        Initialize the Traditional React Agent
        
        Args:
            skills_base_path: Path to the skills directory
            llm: LangChain LLM instance (optional)
            exclude_skills: Optional list of skill names to exclude from discovery
                           (e.g., ['nvidia_vlm_skill', 'image_generation_skill'])
        """
        self.skills_base_path = Path(skills_base_path)
        
        # Initialize skill loader
        print("🔧 Loading skills and tools...")
        self.loader = OldWays(self.skills_base_path, exclude_skills=exclude_skills)
        self.skills = self.loader.list_skills()
        
        # Load tools from all skills using StructuredTool
        self.tools = []
        for skill in self.skills:
            try:
                skill_tools = self.loader.create_langchain_tools(skill.name)
                # Wrap each tool with timing
                wrapped_tools = [self._wrap_tool_with_timing(tool) for tool in skill_tools]
                self.tools.extend(wrapped_tools)
                print(f"   ✅ Loaded {len(skill_tools)} tools from skill: {skill.name}")
            except Exception as e:
                print(f"   ⚠️  Could not load tools for {skill.name}: {e}")
        
        # Create tool name to tool mapping
        self.tool_map = {tool.name: tool for tool in self.tools}
        
        # Initialize LLM - use provided llm or import from query_decomposition
        if llm:
            self.llm = llm
        else:
            # Use the LLM instance from query_decomposition.py (already configured)
            self.llm = query_decomposition_llm
            print(f"✅ Using LLM from query_decomposition: {type(self.llm).__name__}")
        
        # create_agent handles tool binding automatically
        
        # Plan state tracking (constructed from tool calls made)
        self.current_plan = None  # Stores the plan constructed from tool calls
        self.current_user_query = None  # Stores the current user query
        self.tool_call_history = []  # Track tool calls and results for history_section
        self.is_simple_query = False  # Track if current query is simple (computed in invoke)
        
        # Cache metrics tracking for tool calling scenarios
        self.cache_tracker = CacheMetricsTracker()
        
        # Track LLM call metrics for detailed analysis
        self.llm_call_metrics = []  # List of cache hit rates for each LLM call
        self.tool_call_metrics = []  # List of cache hit rates for tool-calling LLM calls
        
        # Create middleware for system prompt injection and cache tracking
        self.middleware = CustomAgentMiddleware(self)
        
        # Build the agent using create_agent from LangChain (with tools for complex queries)
        self.graph = create_agent(
            model=self.llm,
            tools=self.tools,
            middleware=[self.middleware]
        )
        
        # Build a separate agent graph without tools for simple queries (greetings, etc.)
        # This prevents tool calls for simple queries
        self.simple_graph = create_agent(
            model=self.llm,
            tools=[],  # No tools for simple queries
            middleware=[self.middleware]
        )
        
        print(f"✅ Initialized agent with {len(self.tools)} tools from {len(self.skills)} skills")
    
    def _get_available_skills_description(self) -> str:
        """Generate skills description for the prompt"""
        skills_desc = []
        for skill in self.skills:
            skills_desc.append(f"- {skill.name}: {skill.description}")
        return "\n".join(skills_desc)
    
    def _format_plan_as_text(self, plan: Dict[str, Any]) -> str:
        """Format plan dictionary as text for inclusion in system prompt"""
        if not plan or not plan.get("output_steps"):
            return ""
        
        steps = plan.get("output_steps", [])
        plan_text = f"\n=== CURRENT PLAN ({len(steps)} steps) ===\n"
        for step in steps:
            plan_text += f"\nStep {step['step_nr']}: {step['skill_name']}\n"
            plan_text += f"  Rationale: {step['rationale']}\n"
            plan_text += f"  Sub-query: {step['sub_query']}\n"
            status = step.get('status', 'pending')
            plan_text += f"  Status: {status}\n"
            if step.get('result'):
                plan_text += f"  Result: {step['result']}\n"
        plan_text += "\n=== END PLAN ===\n"
        return plan_text
    
    def _format_history_section(self) -> str:
        """Format tool call history as history_section for system prompt"""
        if not self.tool_call_history:
            return ""
        
        history_text = "\n<History>\n"
        for entry in self.tool_call_history:
            tool_name = entry.get('tool_name', 'unknown')
            tool_result = entry.get('tool_result', '')
            
            # Format exactly as "tool_message: tool call result"
            # Include tool name and result for clarity
            history_text += f"tool_message: {tool_name} -> {tool_result}\n"
        
        history_text += "</History>\n"
        return history_text
    
    def _update_plan_from_tool_calls(self, tool_calls: List[Dict], tool_results: List[str]):
        """Update or create plan from tool calls made"""
        if not self.current_plan:
            # Create new plan from tool calls
            self.current_plan = {
                "multi_steps": len(tool_calls) > 1,
                "output_steps": []
            }
        
        # Add or update steps based on tool calls
        for i, (tool_call, result) in enumerate(zip(tool_calls, tool_results), start=1):
            tool_name = tool_call.get('name', 'unknown')
            tool_args = tool_call.get('args', {})
            
            # Find if step already exists or create new
            step_exists = False
            for step in self.current_plan.get("output_steps", []):
                if step.get('skill_name') == tool_name and step.get('status') == 'pending':
                    step['status'] = 'completed'
                    step['result'] = str(result)[:500]  # Truncate long results
                    step_exists = True
                    break
            
            if not step_exists:
                # Create new step
                step = {
                    "step_nr": len(self.current_plan.get("output_steps", [])) + 1,
                    "skill_name": tool_name,
                    "rationale": f"Tool {tool_name} was called to handle the request",
                    "sub_query": f"Execute {tool_name} with args: {tool_args}",
                    "status": "completed",
                    "result": str(result)[:500]
                }
                self.current_plan["output_steps"].append(step)
    
    def _is_simple_query(self, user_input: str) -> bool:
        """
        Detect if query is a simple greeting or chat that doesn't need tools.
        This allows fast-path responses without tool binding overhead.
        """
        if not user_input:
            return True
        
        # Normalize input
        query_lower = user_input.lower().strip()
        
        # Simple greetings and casual queries
        simple_patterns = [
            'hello', 'hi', 'hey', 'greetings',
            'how are you', 'what\'s up', 'whats up',
            'thanks', 'thank you', 'bye', 'goodbye',
            'what can you do', 'help', 'who are you'
        ]
        
        # Check if query matches simple patterns (exact or starts with)
        for pattern in simple_patterns:
            if query_lower == pattern or query_lower.startswith(pattern + ' '):
                return True
        
        # Very short queries (< 20 chars) are likely simple
        if len(query_lower) < 20 and not any(keyword in query_lower for keyword in ['schedule', 'book', 'create', 'generate', 'find', 'search', 'list', 'show']):
            return True
        
        return False
    
    def _wrap_tool_with_timing(self, tool: StructuredTool) -> StructuredTool:
        """Wrap a tool function with timing and color printing"""
        original_func = tool.func
        
        def timed_tool_func(*args, **kwargs):
            """Wrapper that times tool execution"""
            tool_name = tool.name
            print(f"{Fore.CYAN}🔧 Executing tool: {tool_name}{Style.RESET_ALL}")
            if kwargs:
                # Show first few args
                args_items = list(kwargs.items())[:3]
                args_str = ", ".join([f"{k}={str(v)[:50]}" for k, v in args_items])
                if len(kwargs) > 3:
                    args_str += f" ... (+{len(kwargs) - 3} more)"
                print(f"   {Fore.CYAN}   Args: {args_str}{Style.RESET_ALL}")
            
            # Time the execution
            start_time = time.time()
            try:
                result = original_func(*args, **kwargs)
                end_time = time.time()
                elapsed = end_time - start_time
                print(f"{Fore.GREEN}✅ Tool '{tool_name}' completed in {elapsed:.3f}s{Style.RESET_ALL}")
                return result
            except Exception as e:
                end_time = time.time()
                elapsed = end_time - start_time
                print(f"{Fore.RED}❌ Tool '{tool_name}' failed after {elapsed:.3f}s: {str(e)}{Style.RESET_ALL}")
                raise
        
        # Create a new StructuredTool with the wrapped function
        return StructuredTool(
            name=tool.name,
            description=tool.description,
            func=timed_tool_func,
            args_schema=tool.args_schema,
            return_direct=tool.return_direct
        )
    
    
    def demonstrate_tool_binding(self):
        """
        Demonstrate how create_agent handles tool binding
        
        This shows that create_agent automatically handles:
        1. Tool binding to the LLM
        2. Automatic tool calling
        3. Tool calls accessed via AIMessage.tool_calls
        
        Reference: https://docs.langchain.com/oss/python/langchain/agents
        """
        print("\n🔍 Demonstrating Tool Binding with create_agent:")
        print(f"   LLM: {self.llm.__class__.__name__}")
        print(f"   Tools available: {len(self.tools)}")
        print(f"   Tool names: {[tool.name for tool in self.tools[:5]]}...")
        
        # Test a simple invocation with the agent
        test_message = "What tools do you have access to?"
        result = self.graph.invoke({
            "messages": [HumanMessage(content=test_message)]
        })
        
        last_message = result["messages"][-1] if result.get("messages") else None
        
        if last_message:
            print(f"\n   Response type: {type(last_message)}")
            print(f"   Has tool_calls: {hasattr(last_message, 'tool_calls')}")
            
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                print(f"   Tool calls made: {len(last_message.tool_calls)}")
                for tc in last_message.tool_calls:
                    print(f"      - {tc.get('name', 'unknown')}: {tc.get('args', {})}")
            else:
                print(f"   Response: {last_message.content[:200] if hasattr(last_message, 'content') else str(last_message)[:200]}...")
        
        return result
    
    def invoke(self, user_input: str, chat_history: List[BaseMessage] = None, enable_print: bool = True) -> Dict[str, Any]:
        """
        Invoke the agent with a user query using the tool-calling interface
        
        The agent will:
        1. Let the LLM construct tool calls directly (no upfront decomposition)
        2. Execute the tools automatically in a ReAct loop
        3. Track tool calls and results, building a plan dynamically
        4. Inject plan state and tool call history into system prompt on each iteration
        5. Return a final response
        
        Args:
            user_input: The user's query
            chat_history: Optional list of previous messages for context
            
        Returns:
            Dictionary with the final state including all messages and timing info
        """
        if enable_print:
            print("\n" + "="*70)
            print(Fore.YELLOW + "🤖 Traditional React Agent (create_agent)" )
            #("="*70)
        
            print(f"📝 Query: {user_input}")
        
        # Start timing
        start_time = time.time()
        print(f"⏰ Start time: {time.strftime('%H:%M:%S', time.localtime(start_time))}\n")
        
        # Track cache metrics for entire query execution
        cache_tracker = getattr(self, 'cache_tracker', None)
        if cache_tracker:
            cache_tracker.reset_baseline()
        
        # Reset LLM call metrics for this query
        self.llm_call_metrics = []
        self.tool_call_metrics = []
        
        # Store current query
        self.current_user_query = user_input
        
        # Reset plan and history for new query
        self.current_plan = None
        self.tool_call_history = []
        
        # No upfront query decomposition - LLM will construct tool calls directly
        # Store is_simple as instance variable so middleware can use it without recalculating
        self.is_simple_query = self._is_simple_query(user_input)
        
        # Reset baseline for ReAct loop (tool calling phase)
        if cache_tracker:
            cache_tracker.reset_baseline()
        
        # Prepare initial state
        messages = list(chat_history) if chat_history else []
        messages.append(HumanMessage(content=user_input))
        
        initial_state = {
            "messages": messages
        }
        
        # Choose the appropriate graph based on query complexity
        # For simple queries, use graph without tools to prevent unnecessary tool calls
        if self.is_simple_query:
            if enable_print:
                print(f"💬 Simple query detected - using agent without tools")
            # Use simple graph (no tools) for greetings and simple queries
            final_state = self.simple_graph.invoke(initial_state)
        else:
            # Run the full graph with tools for complex queries
            # The agent will automatically:
            # - Use bind_tools() to let the LLM know about available tools
            # - Parse tool_calls from AIMessage when LLM wants to use tools
            # - Execute the tools via ToolNode
            # - Continue the ReAct loop until no more tool calls
            final_state = self.graph.invoke(initial_state)
        
        # End timing
        end_time = time.time()
        elapsed_time = end_time - start_time
        if enable_print:        
            print("\n" + "="*70)
        
            print("✅ Agent Execution Complete")
            
        print(f"⏱️  Total execution time: {elapsed_time:.2f} seconds")
        print(f"⏰ End time: {time.strftime('%H:%M:%S', time.localtime(end_time))}")
        print("="*70 + "\n")
        
        # Extract the final response
        final_messages = final_state["messages"]
        final_response = final_messages[-1].content if final_messages else ""
        
        # Calculate detailed cache metrics
        tool_calling_cache_hit_rate = None
        overall_cache_hit_rate = None
        avg_llm_call_cache_hit_rate = None
        avg_tool_call_cache_hit_rate = None
        
        # ALWAYS count LLM calls (regardless of cache_tracker availability)
        # Count all LLM calls including:
        # - Each _call_model invocation (tool-calling decisions)
        # - Any query decomposition calls
        # - Final response calls
        num_llm_calls = len(self.llm_call_metrics) if self.llm_call_metrics else 0
        
        # FALLBACK: If middleware didn't track calls, count AIMessages in final state
        # Each AIMessage represents one LLM call
        if num_llm_calls == 0:
            # Count AIMessages that were added during this query execution
            # (exclude any that were in chat_history)
            initial_message_count = len(chat_history) if chat_history else 0
            ai_messages_in_execution = [
                msg for msg in final_messages[initial_message_count:]
                if isinstance(msg, AIMessage)
            ]
            num_llm_calls = len(ai_messages_in_execution)
            
            # If we're using fallback counting, populate metrics from AIMessages
            if num_llm_calls > 0 and not self.llm_call_metrics:
                for msg in ai_messages_in_execution:
                    has_tool_calls = hasattr(msg, 'tool_calls') and msg.tool_calls is not None and len(msg.tool_calls) > 0
                    tool_names = []
                    if has_tool_calls:
                        tool_names = [tc.get('name', 'unknown') for tc in msg.tool_calls]
                    
                    self.llm_call_metrics.append({
                        'cache_hit_rate': None,  # Can't get cache metrics without middleware
                        'has_tool_calls': has_tool_calls,
                        'num_tool_calls': len(msg.tool_calls) if has_tool_calls else 0,
                        'tool_names': tool_names
                    })
        
        # Count tool-calling LLM calls (LLM calls that resulted in tool calls)
        num_tool_calls = sum(1 for m in self.llm_call_metrics if m.get('has_tool_calls', False)) if self.llm_call_metrics else 0
        
        if cache_tracker:
            # Get incremental cache hit rate for tool calling
            tool_calling_cache_hit_rate = cache_tracker.get_incremental_hit_rate()
            # Get overall cache hit rate (cumulative)
            overall_cache_hit_rate = cache_tracker.get_current_hit_rate()
            
            # Calculate average cache hit rates from tracked metrics
            if self.llm_call_metrics:
                cache_rates = [m['cache_hit_rate'] for m in self.llm_call_metrics if m.get('cache_hit_rate') is not None]
                if cache_rates:
                    avg_llm_call_cache_hit_rate = sum(cache_rates) / len(cache_rates)
            
            if self.tool_call_metrics:
                if self.tool_call_metrics:
                    avg_tool_call_cache_hit_rate = sum(self.tool_call_metrics) / len(self.tool_call_metrics)
            
            # Print detailed cache metrics
            if tool_calling_cache_hit_rate is not None:
                print(f"   💾 Tool calling phase cache hit rate: {tool_calling_cache_hit_rate:.1f}%")
            if avg_llm_call_cache_hit_rate is not None:
                print(f"   💾 Average LLM call cache hit rate: {avg_llm_call_cache_hit_rate:.1f}% ({num_llm_calls} calls)")
            if avg_tool_call_cache_hit_rate is not None:
                print(f"   💾 Average tool-calling LLM cache hit rate: {avg_tool_call_cache_hit_rate:.1f}% ({num_tool_calls} tool calls)")
            if overall_cache_hit_rate is not None:
                print(f"   💾 Overall cache hit rate: {overall_cache_hit_rate:.1f}%")
        
        # Always print LLM call count (even if cache metrics aren't available)
        if num_llm_calls > 0:
            print(f"   📊 Total LLM calls: {num_llm_calls} (including {num_tool_calls} tool-calling decisions)")
        else:
            # Show 0 calls explicitly to indicate tracking is working
            print(f"   📊 Total LLM calls: {num_llm_calls} (middleware tracking may not be active)")
        
        # Print per-call cache hit rates breakdown for analysis
        if self.llm_call_metrics:
            tool_calling_rates = [m['cache_hit_rate'] for m in self.llm_call_metrics 
                                if m.get('has_tool_calls') and m.get('cache_hit_rate') is not None]
            non_tool_calling_rates = [m['cache_hit_rate'] for m in self.llm_call_metrics 
                                     if not m.get('has_tool_calls') and m.get('cache_hit_rate') is not None]
            
            if tool_calling_rates:
                print(f"   📊 Per-call tool-calling cache hit rates: {[f'{r:.1f}%' for r in tool_calling_rates]}")
                if len(tool_calling_rates) > 0:
                    min_rate = min(tool_calling_rates)
                    max_rate = max(tool_calling_rates)
                    print(f"      Range: {min_rate:.1f}% - {max_rate:.1f}% (each tool call decision is a separate LLM call)")
            if non_tool_calling_rates:
                print(f"   📊 Per-call non-tool-calling cache hit rates: {[f'{r:.1f}%' for r in non_tool_calling_rates]}")
        
        return {
            "output": final_response,
            "messages": final_messages,
            "intermediate_steps": self._extract_intermediate_steps(final_messages),
            "execution_time": elapsed_time,
            "start_time": start_time,
            "end_time": end_time,
            "cache_metrics": {
                "tool_calling_cache_hit_rate": tool_calling_cache_hit_rate,
                "overall_cache_hit_rate": overall_cache_hit_rate,
                "avg_llm_call_cache_hit_rate": avg_llm_call_cache_hit_rate,
                "avg_tool_call_cache_hit_rate": avg_tool_call_cache_hit_rate,
                "num_llm_calls": num_llm_calls,
                "num_tool_calls": num_tool_calls,
                "llm_call_metrics": self.llm_call_metrics,  # Detailed per-call metrics with cache hit rates
                "per_call_cache_hit_rates": [m['cache_hit_rate'] for m in self.llm_call_metrics if m.get('cache_hit_rate') is not None],  # List of per-call hit rates
                "tool_calling_cache_hit_rates": [m['cache_hit_rate'] for m in self.llm_call_metrics if m.get('has_tool_calls') and m.get('cache_hit_rate') is not None],  # Per-call hit rates for tool-calling decisions
                "non_tool_calling_cache_hit_rates": [m['cache_hit_rate'] for m in self.llm_call_metrics if not m.get('has_tool_calls') and m.get('cache_hit_rate') is not None]  # Per-call hit rates for non-tool-calling LLM calls
            }
        }
    
    def _extract_intermediate_steps(self, messages: List[BaseMessage]) -> List[tuple]:
        """Extract intermediate steps (tool calls and results) from messages"""
        steps = []
        
        for i, msg in enumerate(messages):
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                # Found a message with tool calls
                for tool_call in msg.tool_calls:
                    # Find the corresponding tool message
                    tool_result = None
                    for j in range(i + 1, len(messages)):
                        if isinstance(messages[j], ToolMessage):
                            if messages[j].tool_call_id == tool_call.get('id'):
                                tool_result = messages[j].content
                                break
                    
                    steps.append((
                        {"tool": tool_call.get('name'), "args": tool_call.get('args')},
                        tool_result or "No result"
                    ))
        
        return steps


# Get skills path
skills_path = Path(__file__).parent

# Initialize agent variable (will be set when module is run directly)
agent = None

# ============================================================================
# Main and Testing
# ============================================================================

def main(agent=None):
    """Main function to test the Traditional React Agent"""
    
    # Initialize agent if not provided
    if agent is None:
        try:
            agent = TraditionalReactAgent(skills_path, llm=query_decomposition_llm)
        except Exception as e:
            print(Fore.RED + f"Error initializing agent: {e}" + Style.RESET_ALL)
            import traceback
            traceback.print_exc()
            return
    
    # Test queries
    test_queries = [
        "Book myself for 1 hour tomorrow at 2pm for creative work, then generate 5 innovative AI project ideas",
        "list all available resources",
        "What tools and skills do you have access to?"
    ]
    
    print("\n📝 Running test queries...\n")
    
    # Track timing for all queries
    query_times = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*70}")
        print(f"Test Query {i}: {query}")
        print(f"{'='*70}\n")
        
        try:
            # Start timing
            start_time = time.time()
            
            result = agent.invoke(query)
            
            # End timing
            end_time = time.time()
            elapsed_time = end_time - start_time
            query_times.append({
                'query': query,
                'time': elapsed_time,
                'success': True
            })
            
            print(f"\n📊 Result for '{query}':")
            print(f"Output: {result.get('output', result)}\n")
            print(f"⏱️  Time taken: {elapsed_time:.2f} seconds\n")
            
            # Show intermediate steps if verbose
            if 'intermediate_steps' in result:
                print(f"Intermediate steps: {len(result['intermediate_steps'])}")
                for step_idx, (action, observation) in enumerate(result['intermediate_steps'], 1):
                    print(f"  Step {step_idx}:")
                    print(f"    Action: {action}")
                    print(f"    Observation: {str(observation)[:200]}...")
        except Exception as e:
            # Track failed query time
            end_time = time.time()
            elapsed_time = end_time - start_time if 'start_time' in locals() else 0
            query_times.append({
                'query': query,
                'time': elapsed_time,
                'success': False,
                'error': str(e)
            })
            
            print(f"❌ Error processing query '{query}': {e}")
            print(f"⏱️  Time before error: {elapsed_time:.2f} seconds\n")
            import traceback
            traceback.print_exc()
    
    # Display timing summary
    print("\n" + "="*70)
    print("⏱️  TIMING SUMMARY")
    print("="*70)
    
    successful_queries = [q for q in query_times if q['success']]
    failed_queries = [q for q in query_times if not q['success']]
    
    if successful_queries:
        print("\n✅ Successful Queries:")
        for i, q in enumerate(successful_queries, 1):
            print(f"  {i}. {q['query'][:60]}...")
            print(f"     Time: {q['time']:.2f}s")
    
    if failed_queries:
        print("\n❌ Failed Queries:")
        for i, q in enumerate(failed_queries, 1):
            print(f"  {i}. {q['query'][:60]}...")
            print(f"     Time before error: {q['time']:.2f}s")
            print(f"     Error: {q['error']}")
    
    # Overall statistics
    if query_times:
        total_time = sum(q['time'] for q in query_times)
        avg_time = total_time / len(query_times)
        min_time = min(q['time'] for q in query_times)
        max_time = max(q['time'] for q in query_times)
        
        print(f"\n📊 Statistics:")
        print(f"   Total queries: {len(query_times)}")
        print(f"   Successful: {len(successful_queries)}")
        print(f"   Failed: {len(failed_queries)}")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Average time: {avg_time:.2f}s")
        print(f"   Min time: {min_time:.2f}s")
        print(f"   Max time: {max_time:.2f}s")
    
    print("\n" + "="*70)
    print("Testing Complete")
    print("="*70 + "\n")


if __name__ == "__main__":
    # Initialize agent with LLM from query_decomposition (already configured)
    try:
        # Use the LLM instance from query_decomposition.py (already configured based on USE_SELF_HOSTED_LLM)
        agent = TraditionalReactAgent(skills_path, llm=query_decomposition_llm)
    except Exception as e:
        print(Fore.RED + f"Error initializing agent: {e}" + Style.RESET_ALL)
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)

    # Demonstrate tool binding
    print("\n" + "="*70)
    print("Tool Binding Demonstration")
    print("="*70)
    agent.demonstrate_tool_binding()
    
    # Run main with the initialized agent
    main(agent=agent)

