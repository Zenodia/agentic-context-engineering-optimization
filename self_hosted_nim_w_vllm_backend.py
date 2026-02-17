import requests
import json
import re
from typing import List, Dict, Any, Optional, Union
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage

class Response:
    """
    Response class that mimics ChatNVIDIA's response interface
    """
    def __init__(self, content: str):
        self.content = content


def _strip_thinking_tags(content: str) -> str:
    """
    Strip thinking tags from reasoning model output.
    Handles various formats like <think>...</think>, <thinking>...</thinking>, <reasoning>...</reasoning>, etc.
    """
    # Remove thinking tags and their content (case-insensitive, handles nested tags)
    # Pattern matches: <think>...</think>, <thinking>...</thinking>, <reasoning>...</reasoning>
    patterns = [
        r'<think[^>]*>.*?</think>',
        r'<thinking[^>]*>.*?</thinking>',
        r'<reasoning[^>]*>.*?</reasoning>',
        r'<thought[^>]*>.*?</thought>',
        r'<redacted_reasoning[^>]*>.*?</think>',
    ]
    
    result = content
    for pattern in patterns:
        result = re.sub(pattern, '', result, flags=re.DOTALL | re.IGNORECASE)
    
    return result.strip()


def _ensure_english_only_prompt(base_system_prompt: Optional[str] = None) -> str:
    """
    Enhance system prompt to enforce English-only output
    """
    english_enforcement = """IMPORTANT LANGUAGE REQUIREMENTS:
- You MUST respond ONLY in English
- Do NOT use any other languages (Chinese, Spanish, French, etc.)
- All output must be in English, including code comments and explanations
- If the user asks in another language, respond in English
"""
    
    if base_system_prompt:
        return f"{base_system_prompt}\n\n{english_enforcement}"
    return english_enforcement


def self_hosted_nim_w_vllm_backend_get_response(
    query: Optional[str] = None,
    messages: Optional[List[Dict[str, str]]] = None,
    system_prompt: Optional[str] = None
):
    """
    Get streaming response from self-hosted NIM with vLLM backend
    
    Args:
        query: Single query string (may contain system_prompt + user_query combined)
        messages: List of message dicts with 'role' and 'content' keys
        system_prompt: Optional system prompt to prepend
    
    Returns:
        Generator that yields content tokens (with thinking tags stripped)
    """
    # API endpoint
    url = "http://localhost:8000/v1/chat/completions"

    # Headers
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    # Build messages list
    message_list = []
    
    # Add system prompt if provided (only enhance if system_prompt exists)
    if system_prompt:
        enhanced_system_prompt = _ensure_english_only_prompt(system_prompt)
        message_list.append({"role": "system", "content": enhanced_system_prompt})
    
    # Use messages if provided, otherwise use query
    if messages:
        message_list.extend(messages)
    elif query:
        # If query contains system prompt + user query (common pattern), try to split
        # For now, treat entire query as user message
        message_list.append({"role": "user", "content": query})
    else:
        raise ValueError("Either 'query' or 'messages' must be provided")

    # Request payload
    payload = {
        "model": "nvidia/llama-3.1-nemotron-nano-8b-v1",
        "messages": message_list,
        "top_p": 1,
        "n": 1,
        "max_tokens": 4000,
        "stream": True,
        "frequency_penalty": 0.0,  # Reduced from 1.0 to avoid suppressing output
        # Removed stop tokens - let the streaming logic handle thinking tags instead
        # Additional parameters to discourage non-English output
        "temperature": 0.7,  # Lower temperature for more consistent English output
    }

    # Make POST request with streaming
    response = requests.post(url, headers=headers, json=payload, stream=True)

    # Check if request was successful
    if response.status_code == 200:
        # Buffer to accumulate content for thinking tag detection
        content_buffer = ""
        in_thinking_tag = False
        
        # Process streaming response
        for line in response.iter_lines():
            if line:
                # Decode the line
                decoded_line = line.decode('utf-8')
                
                # Skip SSE prefix if present
                if decoded_line.startswith('data: '):
                    decoded_line = decoded_line[6:]
                
                # Skip [DONE] marker
                if decoded_line.strip() == '[DONE]':
                    break
                
                # Parse JSON from the line
                try:
                    data = json.loads(decoded_line)
                    # Extract content from the delta if it exists
                    if 'choices' in data and len(data['choices']) > 0:
                        delta = data['choices'][0].get('delta', {})
                        if 'content' in delta:
                            token = delta['content']
                            
                            # If we're in a thinking tag, check if we're exiting
                            if in_thinking_tag:
                                content_buffer += token
                                # Check for various closing tag formats (redacted_reasoning is the actual format used)
                                closing_tags = ['</think>', '</think>', '</think>', '</thinking>', '</reasoning>', '</thought>']
                                for closing_tag in closing_tags:
                                    if closing_tag in content_buffer.lower():
                                        # Find where closing tag ends
                                        close_idx = content_buffer.lower().find(closing_tag)
                                        if close_idx >= 0:
                                            # Skip everything up to and including the closing tag
                                            content_after = content_buffer[close_idx + len(closing_tag):]
                                            in_thinking_tag = False
                                            content_buffer = content_after
                                            # If there's content after the closing tag, yield it immediately
                                            if content_buffer:
                                                yield content_buffer
                                                content_buffer = ""
                                            break
                            else:
                                # Not in thinking tag - check if we're entering one
                                content_buffer += token
                                
                                # Check if we're entering a thinking tag (redacted_reasoning is the actual format)
                                if '<redacted_reasoning' in content_buffer.lower() or '<think' in content_buffer.lower():
                                    # Find where thinking tag starts
                                    think_start_idx = -1
                                    for pattern in ['<redacted_reasoning', '<think']:
                                        idx = content_buffer.lower().find(pattern)
                                        if idx >= 0:
                                            think_start_idx = idx
                                            break
                                    
                                    if think_start_idx >= 0:
                                        # Yield content before thinking tag
                                        pre_think = content_buffer[:think_start_idx]
                                        if pre_think:
                                            yield pre_think
                                        # Mark that we're in a thinking tag
                                        in_thinking_tag = True
                                        content_buffer = content_buffer[think_start_idx:]
                                else:
                                    # No thinking tags detected, yield immediately for real-time streaming
                                    if content_buffer:
                                        yield content_buffer
                                        content_buffer = ""
                except json.JSONDecodeError:
                    # If it's not JSON, skip it
                    pass
        
        # After streaming is complete, strip any remaining thinking tags from buffer and yield
        if content_buffer and not in_thinking_tag:
            cleaned = _strip_thinking_tags(content_buffer)
            if cleaned:
                yield cleaned
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        yield ""


class SelfHostedNIMLLM:
    """
    Wrapper class for self-hosted NIM LLM that mimics ChatNVIDIA interface
    """
    
    def __init__(self, model: str = "meta/llama-3.1-8b-instruct", **kwargs):
        """
        Initialize the self-hosted NIM LLM wrapper
        
        Args:
            model: Model name (for compatibility, not used)
            **kwargs: Additional parameters (ignored for now)
        """
        self.model = model
    
    def invoke(self, messages: List[BaseMessage]) -> Any:
        """
        Invoke the LLM with LangChain messages
        
        Args:
            messages: List of LangChain BaseMessage objects
        
        Returns:
            Response object with .content attribute (mimics ChatNVIDIA response)
        """
        # Convert LangChain messages to API format
        api_messages = []
        system_content = None
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                system_content = msg.content
            elif isinstance(msg, HumanMessage):
                api_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                api_messages.append({"role": "assistant", "content": msg.content})
        
        # Collect all tokens from the generator
        full_content = ""
        for token in self_hosted_nim_w_vllm_backend_get_response(
            messages=api_messages,
            system_prompt=system_content
        ):
            full_content += token
        
        # Final pass to strip any remaining thinking tags (in case streaming detection missed some)
        full_content = _strip_thinking_tags(full_content)
        
        # Return AIMessage to be compatible with LangChain message handling
        return AIMessage(content=full_content)
    
    def bind_tools(self, tools, tool_choice=None, **kwargs):
        """
        Bind tools to the LLM (for compatibility with LangChain tool calling)
        
        Args:
            tools: List of tools to bind
            tool_choice: Optional tool choice parameter (for compatibility with LangChain)
            **kwargs: Additional keyword arguments (for compatibility)
        
        Note: This is a stub - the self-hosted backend doesn't support tool binding yet
        """
        # Store tools for potential future use
        self.bound_tools = tools
        self.tool_choice = tool_choice
        # Return self for now - tool calling would need to be implemented
        return self


if __name__ == "__main__":
    # Iterate over the generator to get tokens as they stream
    for token in self_hosted_nim_w_vllm_backend_get_response("Describe the mechanism of breaking down a complex problem into smaller sub-problems and solve them one by one. For example, how to solve a math problem step by step?"):
        print(token, end='', flush=True)  # Print each token without newline, flush to see immediately
    print()  # Print final newline
