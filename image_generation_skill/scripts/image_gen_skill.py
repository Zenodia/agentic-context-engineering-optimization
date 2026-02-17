"""
NVIDIA Image Generation Skill Implementation
Agent Skills API Compliant with NAT Integration

This is the implementation code that gets called after the agent
reads the SKILL.md instructions and decides to use this skill.

Uses NVIDIA's Flux.1 Schnell model for fast, high-quality image generation.

Includes @skill_tool decorated functions for NAT auto-discovery.
"""

import os
import sys
import requests
import base64
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
import random
# Import skill_tool decorator from skill_loader
try:
    from skill_loader import skill_tool
except ImportError:
    # Fallback: Add parent directory to path
    parent_dir = Path(__file__).parent.parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    try:
        from skill_loader import skill_tool
    except ImportError:
        # If still can't import, define a dummy decorator
        def skill_tool(name=None, description=None, return_direct=False):
            def decorator(func):
                func._is_skill_tool = True
                func._tool_name = name or func.__name__
                func._tool_description = description or func.__doc__ or ""
                func._tool_return_direct = return_direct
                return func
            return decorator


class ImageGenerationSkill:
    """
    NVIDIA-powered Image Generation skill for AI agents
    
    This implementation is activated when an agent:
    1. Discovers the skill via SKILL.md metadata in system prompt
    2. Reads the full SKILL.md instructions
    3. Decides the user needs image generation
    4. Calls this implementation
    """
    
    def __init__(self, api_key: Optional[str] = None, output_dir: Optional[str] = None):
        """
        Initialize the NVIDIA Image Generation skill
        
        Args:
            api_key: NVIDIA API key (defaults to NVIDIA_API_KEY env var)
            output_dir: Custom directory for generated images (defaults to 'generated_images/')
        
        Raises:
            ValueError: If NVIDIA_API_KEY is not set
        """
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "NVIDIA_API_KEY must be set as environment variable or passed to constructor. "
                "Get your key at: https://build.nvidia.com/"
            )
        
        self.invoke_url = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-schnell"
        
        # Create directory for generated images
        self.output_dir = Path(output_dir) if output_dir else Path("generated_images")
        self.output_dir.mkdir(exist_ok=True)
        
        self.version = "1.0.0"
        self.name = "image-generation"
        
        # Skill location for agent discovery
        self.skill_location = Path(__file__).parent.parent / "SKILL.md"
    
    def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        seed: int = 0,
        steps: int = 4,
        save: bool = True,
        filename: Optional[str] = None,
        include_image_data: bool = True
    ) -> Dict[str, Any]:
        """
        Generate an image from a text prompt
        
        Args:
            prompt: Text description of the image to generate
            width: Image width in pixels (default: 1024)
            height: Image height in pixels (default: 1024)
            seed: Random seed for reproducibility (default: 0)
            steps: Number of inference steps (default: 4, higher = better quality but slower)
            save: Whether to save the image to disk (default: True)
            filename: Custom filename (without extension, defaults to auto-generated)
            include_image_data: Whether to include base64 image data in response (default: True)
        
        Returns:
            Dictionary containing:
                - success: Whether generation was successful
                - image_path: Path to saved image (if save=True)
                - image_data: Base64 encoded image data
                - metadata: Generation metadata (prompt, dimensions, etc.)
                - error: Error message if failed
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            }
            
            # Build payload with required NVIDIA API parameters
            payload = {
                "prompt": prompt,
                "width": width,
                "height": height,
                "seed": seed,
                "steps": steps
            }
            
            # Add optional parameters for better control
            # Note: flux.1-schnell doesn't use cfg_scale, but flux.1-dev does
            # We'll add it conditionally based on the model
            if "flux.1-dev" in self.invoke_url:
                payload["mode"] = "base"
                payload["cfg_scale"] = 3.5
            
            # Make API request
            response = requests.post(self.invoke_url, headers=headers, json=payload)
            response.raise_for_status()
            response_body = response.json()
            
            # Extract image data - try multiple possible response formats
            image_data = None
            
            # Format 1: Direct "image" field
            if "image" in response_body:
                image_data = response_body["image"]
            # Format 2: OpenAI-style "data" array with "b64_json"
            elif "data" in response_body and len(response_body["data"]) > 0:
                image_data = response_body["data"][0].get("b64_json")
            # Format 3: "artifacts" array with "base64"
            elif "artifacts" in response_body and len(response_body["artifacts"]) > 0:
                image_data = response_body["artifacts"][0].get("base64")
            # Format 4: "images" array
            elif "images" in response_body and len(response_body["images"]) > 0:
                image_data = response_body["images"][0]
            
            if not image_data:
                # Debug: Print actual response structure
                response_keys = list(response_body.keys())
                return {
                    "success": False,
                    "error": f"No image data in response. Available fields: {response_keys}",
                    "response": response_body
                }
            
            # Save image if requested
            image_path = None
            if save:
                if filename:
                    safe_filename = self._sanitize_filename(filename)
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    prompt_snippet = self._sanitize_filename(prompt[:30])
                    safe_filename = f"img_{timestamp}_{prompt_snippet}"
                
                image_path = self.output_dir / f"{safe_filename}.png"
                
                # Decode and save image
                image_bytes = base64.b64decode(image_data)
                with open(image_path, 'wb') as f:
                    f.write(image_bytes)
                
                image_path = str(image_path.absolute())
            
            result = {
                "success": True,
                "image_path": image_path,
                "metadata": {
                    "prompt": prompt,
                    "width": width,
                    "height": height,
                    "seed": seed,
                    "steps": steps,
                    "generated_at": datetime.now().isoformat(),
                    "model": "black-forest-labs/flux.1-schnell"
                }
            }
            
            # Only include large base64 data if requested (reduces subprocess overhead)
            if include_image_data:
                result["image_data"] = image_data
            
            return result
        
        except requests.exceptions.HTTPError as e:
            return {
                "success": False,
                "error": f"API request failed: {e}",
                "status_code": e.response.status_code if e.response else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error generating image: {str(e)}"
            }
    
    
    def generate_multiple_images(
        self,
        prompt: str,
        count: int = 4,
        width: int = 1024,
        height: int = 1024,
        steps: int = 4,
        vary_seed: bool = True,
        include_image_data: bool = False,
        use_parallel: bool = True,
        max_workers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate multiple variations of an image (with optional parallel processing)
        
        Uses ThreadPoolExecutor for I/O-bound API calls, which is faster than
        multiprocessing for network requests.
        
        Args:
            prompt: Text description of the images to generate
            count: Number of images to generate (default: 4)
            width: Image width in pixels
            height: Image height in pixels
            steps: Number of inference steps
            vary_seed: Use different seeds for variation (default: True)
            include_image_data: Whether to include base64 data in results (default: False)
            use_parallel: Use parallel processing for faster generation (default: True)
            max_workers: Maximum number of parallel workers (default: min(count, 4))
        
        Returns:
            Dictionary containing list of results and summary
        """
        # Prepare parameters for each image
        params_list = []
        if vary_seed:
            # Generate unique random seeds for each image to ensure variation
            seeds = [random.randint(0, 2**31 - 1) for _ in range(count)]
        else:
            # Use the same seed (0) for all images
            seeds = [0] * count
        
        for i in range(count):
            params = {
                'prompt': prompt,
                'width': width,
                'height': height,
                'seed': seeds[i],
                'steps': steps,
                'filename': f"{self._sanitize_filename(prompt[:20])}_var{i+1}",
                'include_image_data': include_image_data
            }
            params_list.append(params)
        
        # Generate images (parallel or sequential)
        if use_parallel and count > 1:
            # Use ThreadPoolExecutor for I/O-bound API calls
            # ThreadPoolExecutor is faster than multiprocessing for network I/O
            if max_workers is None:
                max_workers = min(count, 4)  # Limit to avoid overwhelming the API
            
            results = [None] * count  # Pre-allocate to maintain order
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks with index tracking
                future_to_index = {
                    executor.submit(
                        self.generate_image,
                        prompt=params['prompt'],
                        width=params['width'],
                        height=params['height'],
                        seed=params['seed'],
                        steps=params['steps'],
                        save=True,
                        filename=params['filename'],
                        include_image_data=params['include_image_data']
                    ): idx for idx, params in enumerate(params_list)
                }
                
                # Collect results as they complete (maintains order by index)
                for future in as_completed(future_to_index):
                    idx = future_to_index[future]
                    try:
                        result = future.result()
                        results[idx] = result
                    except Exception as e:
                        # Handle individual task failures
                        results[idx] = {
                            "success": False,
                            "error": f"Task failed: {str(e)}"
                        }
        else:
            # Sequential generation (fallback)
            results = []
            for params in params_list:
                result = self.generate_image(
                    prompt=params['prompt'],
                    width=params['width'],
                    height=params['height'],
                    seed=params['seed'],
                    steps=params['steps'],
                    save=True,
                    filename=params['filename'],
                    include_image_data=params['include_image_data']
                )
                results.append(result)
        
        # Count successes and failures
        successful = sum(1 for r in results if r.get("success", False))
        failed = count - successful
        
        return {
            "success": successful > 0,
            "total": count,
            "successful": successful,
            "failed": failed,
            "results": results,
            "prompt": prompt,
            "parallel_used": use_parallel and count > 1,
            "execution_method": "ThreadPoolExecutor" if (use_parallel and count > 1) else "sequential"
        }
    
    def _sanitize_filename(self, text: str) -> str:
        """Sanitize text to be safe for filenames"""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            text = text.replace(char, '_')
        
        # Replace spaces with underscores
        text = text.replace(' ', '_')
        
        # Replace multiple underscores with single underscore
        while '__' in text:
            text = text.replace('__', '_')
        
        # Remove leading/trailing spaces, dots, and underscores
        text = text.strip('._')
        
        # Limit length
        text = text[:50]
        
        return text or "image"
    
    def save_generation_metadata(
        self,
        image_path: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Save generation metadata to a JSON file
        
        Args:
            image_path: Path to the generated image
            metadata: Metadata dictionary
        
        Returns:
            Path to saved metadata file
        """
        image_path_obj = Path(image_path)
        metadata_path = image_path_obj.with_suffix('.json')
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        return str(metadata_path)
    
    def get_skill_info(self) -> Dict[str, Any]:
        """Get skill metadata and status information"""
        return {
            "name": self.name,
            "version": self.version,
            "model": "black-forest-labs/flux.1-schnell",
            "capabilities": [
                "text_to_image",
                "multiple_variations",
                "custom_dimensions",
                "seed_control",
                "quality_control"
            ],
            "supported_resolutions": [
                "512x512", "1024x1024", "1024x768", "768x1024", "1920x1080"
            ],
            "status": "initialized",
            "api_available": True,
            "output_directory": str(self.output_dir.absolute()),
            "skill_location": str(self.skill_location.absolute()) if self.skill_location.exists() else "not found"
        }


# ============================================================================
# Note: Removed multiprocessing worker function
# ThreadPoolExecutor uses instance methods directly, no need for static workers
# ============================================================================


# ============================================================================
# NAT Auto-Discovery Tool Functions
# These @skill_tool decorated functions are auto-discovered by the skill loader
# ============================================================================

# Global skill instance for tool functions
_global_skill_instance = None


def _get_skill_instance():
    """Get or create the global skill instance"""
    global _global_skill_instance
    if _global_skill_instance is None:
        api_key = os.getenv("NVIDIA_API_KEY")
        try:
            _global_skill_instance = ImageGenerationSkill(api_key=api_key)
        except ValueError as e:
            # API key not set - return None
            print(f"Warning: {str(e)}")
            return None
    return _global_skill_instance


@skill_tool(
    name="generate_image",
    description="Generate an image from a text prompt using NVIDIA's Flux.1 Schnell model. Fast, high-quality image generation.",
    return_direct=False
)
def generate_image(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    seed: int = 0,
    steps: int = 4
) -> Dict[str, Any]:
    """
    Generate an image from a text description
    
    Args:
        prompt: Text description of the image to generate (required)
        width: Image width in pixels (default: 1024)
        height: Image height in pixels (default: 1024)
        seed: Random seed for reproducibility (default: 0)
        steps: Number of inference steps, higher = better quality (default: 4)
    
    Returns:
        Dictionary with success status, image_path, and metadata
    
    Examples:
        >>> generate_image("a simple coffee shop interior")
        >>> generate_image("sunset over mountains", width=1920, height=1080)
        >>> generate_image("futuristic city skyline", steps=8)
    """
    skill = _get_skill_instance()
    if skill is None:
        return {
            "success": False,
            "error": "NVIDIA_API_KEY not set. Get your key at https://build.nvidia.com/"
        }
    
    return skill.generate_image(prompt, width, height, seed, steps)


@skill_tool(
    name="generate_multiple_images",
    description="Generate multiple variations of an image from a text prompt. Uses ThreadPoolExecutor for faster parallel generation (optimized for I/O-bound API calls).",
    return_direct=False
)
def generate_multiple_images(
    prompt: str,
    count: int = 4,
    width: int = 1024,
    height: int = 1024,
    steps: int = 4,
    use_parallel: bool = True,
    max_workers: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate multiple image variations from a single prompt (with parallel processing)
    
    Uses ThreadPoolExecutor which is faster than multiprocessing for I/O-bound
    tasks like API calls. This provides better performance with less overhead.
    
    Args:
        prompt: Text description of the images to generate (required)
        count: Number of variations to generate (default: 4)
        width: Image width in pixels (default: 1024)
        height: Image height in pixels (default: 1024)
        steps: Number of inference steps (default: 4)
        use_parallel: Use parallel processing for faster generation (default: True)
        max_workers: Maximum number of parallel workers (default: min(count, 4))
    
    Returns:
        Dictionary with list of results and summary statistics
    
    Examples:
        >>> generate_multiple_images("abstract art with vibrant colors", count=4)
        >>> generate_multiple_images("product photo of a smartwatch", count=3, steps=8)
    """
    skill = _get_skill_instance()
    if skill is None:
        return {
            "success": False,
            "error": "NVIDIA_API_KEY not set. Get your key at https://build.nvidia.com/"
        }
    
    return skill.generate_multiple_images(
        prompt, count, width, height, steps,
        use_parallel=use_parallel,
        max_workers=max_workers
    )


@skill_tool(
    name="get_image_generation_skill_info",
    description="Get information about the image generation skill capabilities and status",
    return_direct=False
)
def get_image_generation_skill_info() -> Dict[str, Any]:
    """
    Get metadata about the NVIDIA Image Generation skill
    
    Returns:
        Dictionary with skill information including capabilities and configuration
    """
    skill = _get_skill_instance()
    if skill is None:
        return {
            "error": "Skill not initialized - NVIDIA_API_KEY not set",
            "name": "image-generation",
            "status": "not_initialized"
        }
    
    return skill.get_skill_info()


# Main execution for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='NVIDIA Image Generation Skill')
    parser.add_argument('--json', action='store_true',
                       help='JSON mode for subprocess execution')
    parser.add_argument('prompt', nargs='*',
                       help='Image prompt (for direct testing)')
    
    args = parser.parse_args()
    
    if args.json:
        # JSON CLI mode for subprocess execution
        try:
            # Read JSON input from stdin
            input_data = json.loads(sys.stdin.read())
            command = input_data.get('command', '')
            parameters = input_data.get('parameters', {})
            
            # Initialize skill
            api_key = parameters.get('api_key') or os.getenv('NVIDIA_API_KEY')
            if not api_key:
                output = {
                    'success': False,
                    'error': 'NVIDIA_API_KEY not set. Get your key at https://build.nvidia.com/'
                }
                print(json.dumps(output))
                exit(1)
            
            skill = ImageGenerationSkill(api_key=api_key)
            
            # Execute command
            if command == 'generate_image':
                prompt = parameters.get('prompt', '')
                width = parameters.get('width', 1024)
                height = parameters.get('height', 1024)
                seed = parameters.get('seed', 0)
                steps = parameters.get('steps', 4)
                
                # Don't include image_data in subprocess response to reduce overhead
                result = skill.generate_image(prompt, width, height, seed, steps, include_image_data=False)
                print(json.dumps(result))
            
            elif command == 'generate_multiple_images':
                prompt = parameters.get('prompt', '')
                count = parameters.get('count', 4)
                width = parameters.get('width', 1024)
                height = parameters.get('height', 1024)
                steps = parameters.get('steps', 4)
                # Backward compatibility: support both old and new parameter names
                use_parallel = parameters.get('use_parallel', 
                                            parameters.get('use_multiprocessing', True))
                max_workers = parameters.get('max_workers', None)
                
                # Don't include image_data in subprocess response to reduce overhead
                result = skill.generate_multiple_images(
                    prompt, count, width, height, steps,
                    include_image_data=False,
                    use_parallel=use_parallel,
                    max_workers=max_workers
                )
                print(json.dumps(result))
            
            elif command == 'get_image_generation_skill_info':
                result = skill.get_skill_info()
                print(json.dumps(result))
            
            else:
                output = {
                    'success': False,
                    'error': f'Unknown command: {command}'
                }
                print(json.dumps(output))
        
        except Exception as e:
            output = {
                'success': False,
                'error': f'Subprocess execution failed: {str(e)}'
            }
            print(json.dumps(output))
    
    else:
        # Interactive testing mode
        print("\n" + "="*60)
        print("NVIDIA Image Generation Skill - Agent Skills API Compliant")
        print("="*60 + "\n")
        
        # Check for API key
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            print("❌ Error: NVIDIA_API_KEY environment variable not set")
            print("\nPlease set it using:")
            print("  PowerShell: $env:NVIDIA_API_KEY='your-key-here'")
            print("  CMD:        set NVIDIA_API_KEY=your-key-here")
            print("  Linux/Mac:  export NVIDIA_API_KEY='your-key-here'")
            print("\nGet your key at: https://build.nvidia.com/")
            exit(1)
        
        # Initialize and test skill
        try:
            skill = ImageGenerationSkill()
            print("✅ Skill initialized successfully\n")
            
            # Show skill info
            info = skill.get_skill_info()
            print("📊 Skill Information:")
            print(json.dumps(info, indent=2))
            print("\n" + "="*60 + "\n")
            
            # Test image generation if prompt provided
            if args.prompt:
                prompt = " ".join(args.prompt)
                print(f"🎨 Generating image with prompt: {prompt}")
                print("\n" + "-"*60 + "\n")
                
                result = skill.generate_image(prompt)
                
                if result["success"]:
                    print(f"✅ Image generated successfully!")
                    print(f"📁 Saved to: {result['image_path']}")
                    print(f"\n📝 Metadata:")
                    print(json.dumps(result['metadata'], indent=2))
                else:
                    print(f"❌ Generation failed: {result.get('error')}")
                
                print("\n" + "-"*60 + "\n")
            else:
                print("💡 To test image generation, run with a prompt:")
                print(f'   python {sys.argv[0]} "a simple coffee shop interior"')
            
            print("\n" + "="*60 + "\n")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            exit(1)

