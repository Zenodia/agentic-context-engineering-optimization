"""
NVIDIA Vision Language Model Skill Implementation
Agent Skills API Compliant with NAT Integration

This is the implementation code that gets called after the agent
reads the SKILL.md instructions and decides to use this skill.

Includes @skill_tool decorated functions for NAT auto-discovery.
"""

import os
import sys
import base64
import mimetypes
from openai import OpenAI, AsyncOpenAI
from typing import Generator, Dict, List, Optional, Any, AsyncGenerator
import json
from datetime import datetime
from pathlib import Path
from PIL import Image
import asyncio
from multiprocessing import Pool, cpu_count
from functools import partial

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


class NvidiaVLMSkill:
    """
    NVIDIA-powered Vision Language Model skill for AI agents
    
    This implementation is activated when an agent:
    1. Discovers the skill via SKILL.md metadata in system prompt
    2. Reads the full SKILL.md instructions
    3. Decides the user needs image analysis
    4. Calls this implementation
    """
    
    def __init__(self, api_key: Optional[str] = None, results_dir: Optional[str] = None):
        """
        Initialize the NVIDIA VLM skill
        
        Args:
            api_key: NVIDIA API key (defaults to INFERENCE_API_KEY env var)
            results_dir: Custom directory for saved results (defaults to 'vlm_results/')
        
        Raises:
            ValueError: If INFERENCE_API_KEY is not set
        """
        self.api_key = api_key or os.getenv("INFERENCE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "INFERENCE_API_KEY must be set as environment variable or passed to constructor. "
                "Get your key at: https://build.nvidia.com/"
            )
        
        self.client = OpenAI(
            base_url="https://inference-api.nvidia.com",
            api_key=self.api_key
        )
        
        self.async_client = AsyncOpenAI(
            base_url="https://inference-api.nvidia.com",
            api_key=self.api_key
        )
        
        self.model = "nvidia/nvidia/nemotron-nano-12b-v2-vl"
        
        # Create directory for saved results
        self.results_dir = Path(results_dir) if results_dir else Path("vlm_results")
        self.results_dir.mkdir(exist_ok=True)
        
        self.version = "1.0.0"
        self.name = "nvidia-vlm"
        
        # Skill location for agent discovery
        self.skill_location = Path(__file__).parent.parent / "SKILL.md"
    
    def _encode_image_from_path(self, image_path: str) -> tuple[str, str]:
        """
        Encode image from file path to base64
        
        Args:
            image_path: Path to the image file
        
        Returns:
            Tuple of (base64_string, mime_type)
        
        Raises:
            FileNotFoundError: If image file doesn't exist
        """
        image_path_obj = Path(image_path)
        if not image_path_obj.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Read image as bytes
        with open(image_path_obj, "rb") as image_file:
            image_bytes = image_file.read()
        
        # Encode to base64
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        
        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(str(image_path_obj))
        if mime_type is None:
            # Default to common image types based on extension
            ext = image_path_obj.suffix.lower()
            mime_map = {
                '.jpg': 'image/jpeg', 
                '.jpeg': 'image/jpeg', 
                '.png': 'image/png',
                '.gif': 'image/gif', 
                '.webp': 'image/webp', 
                '.bmp': 'image/bmp'
            }
            mime_type = mime_map.get(ext, 'image/jpeg')
        
        return image_base64, mime_type
    
    def _validate_image(self, image_path: str) -> Dict[str, Any]:
        """
        Validate image file and get metadata
        
        Args:
            image_path: Path to the image file
        
        Returns:
            Dictionary with image metadata
        """
        try:
            img = Image.open(image_path)
            return {
                "valid": True,
                "format": img.format,
                "size": img.size,
                "mode": img.mode,
                "file_size": Path(image_path).stat().st_size
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    async def analyze_image_stream(
        self,
        image_path: str,
        prompt: str = "Identify what is in this image and describe it in detail.",
        temperature: float = 0.2,
        max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        """
        Analyze image with streaming output (recommended for UX)
        
        Args:
            image_path: Path to the image file
            prompt: The text prompt/question about the image
            temperature: Sampling temperature (0-1, lower = more focused)
            max_tokens: Maximum response length
        
        Yields:
            Streamed text chunks
        """
        try:
            # Validate image
            validation = self._validate_image(image_path)
            if not validation["valid"]:
                yield f"❌ Error: Invalid image file - {validation['error']}"
                return
            
            # Encode image
            image_base64, mime_type = self._encode_image_from_path(image_path)
            
            # Build messages
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
            
            # Stream the response
            stream = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        
        except FileNotFoundError as e:
            yield f"❌ Error: {str(e)}"
        except Exception as e:
            yield f"❌ Error analyzing image: {str(e)}\n\nPlease try again or check your API key."
    
    def analyze_image(
        self,
        image_path: str,
        prompt: str = "Identify what is in this image and describe it in detail.",
        temperature: float = 0.2,
        max_tokens: int = 1024
    ) -> str:
        """
        Analyze image (non-streaming version)
        
        Args:
            image_path: Path to the image file
            prompt: The text prompt/question about the image
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum response length
        
        Returns:
            Complete analysis text
        """
        try:
            # Validate image
            validation = self._validate_image(image_path)
            if not validation["valid"]:
                return f"❌ Error: Invalid image file - {validation['error']}"
            
            # Encode image
            image_base64, mime_type = self._encode_image_from_path(image_path)
            
            # Build messages
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
            
            # Get response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            return response.choices[0].message.content
        
        except FileNotFoundError as e:
            return f"❌ Error: {str(e)}"
        except Exception as e:
            return f"❌ Error analyzing image: {str(e)}"
    
    def describe_image_detailed(
        self,
        image_path: str,
        aspects: Optional[List[str]] = None
    ) -> str:
        """
        Get detailed description of image covering multiple aspects
        
        Args:
            image_path: Path to the image file
            aspects: Specific aspects to focus on (e.g., ["colors", "objects", "scene"])
        
        Returns:
            Detailed description
        """
        aspects_text = ""
        if aspects:
            aspects_text = f"\n\nPlease focus on these aspects:\n" + "\n".join(f"- {a}" for a in aspects)
        
        prompt = f"""Provide a comprehensive description of this image including:
1. Overall scene and context
2. Main objects and their positions
3. Colors, lighting, and atmosphere
4. Notable details and textures
5. Any text visible in the image
6. The mood or emotion conveyed{aspects_text}

Be thorough and specific in your description."""
        
        return self.analyze_image(image_path, prompt, temperature=0.2, max_tokens=2048)
    
    def extract_text_from_image(self, image_path: str) -> str:
        """
        Extract text content from image (OCR)
        
        Args:
            image_path: Path to the image file
        
        Returns:
            Extracted text
        """
        prompt = """Extract ALL text visible in this image. 

Requirements:
- List all text exactly as it appears
- Preserve formatting where relevant
- Include text from signs, labels, documents, screens, etc.
- If there is no text, explicitly state "No text detected"
- Organize the text logically (e.g., top to bottom, left to right)

Format your response as:
**Extracted Text:**
[text content here]

**Context:**
[brief note about where/how the text appears]"""
        
        return self.analyze_image(image_path, prompt, temperature=0.1, max_tokens=2048)
    
    def identify_objects(self, image_path: str) -> str:
        """
        Identify and list objects in the image
        
        Args:
            image_path: Path to the image file
        
        Returns:
            List of identified objects
        """
        prompt = """Identify all significant objects in this image.

For each object, provide:
1. Object name/type
2. Position in the image (e.g., foreground, background, left, right)
3. Notable attributes (color, size, condition)
4. Approximate quantity if multiple

Format as a clear, organized list."""
        
        return self.analyze_image(image_path, prompt, temperature=0.2, max_tokens=1536)
    
    def visual_qa(
        self,
        image_path: str,
        question: str
    ) -> str:
        """
        Answer specific questions about the image
        
        Args:
            image_path: Path to the image file
            question: Question to answer about the image
        
        Returns:
            Answer to the question
        """
        prompt = f"""Answer the following question about this image:

**Question:** {question}

Provide a clear, accurate answer based on what you can observe in the image. If you cannot determine the answer from the image, explain why."""
        
        return self.analyze_image(image_path, prompt, temperature=0.3, max_tokens=1024)
    
    def analyze_images_batch(
        self,
        image_paths: List[str],
        prompt: str = "Identify what is in this image and describe it in detail.",
        temperature: float = 0.2,
        max_tokens: int = 1024,
        use_multiprocessing: bool = True,
        max_workers: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple images in parallel using multiprocessing
        
        This method is optimized for batch operations when analyzing many images.
        It processes images in parallel for faster execution.
        
        Args:
            image_paths: List of image file paths to analyze
            prompt: The text prompt/question about the images
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum response length
            use_multiprocessing: Whether to use multiprocessing (default: True)
            max_workers: Maximum number of worker processes (default: cpu_count())
        
        Returns:
            List of dictionaries with analysis results:
            - image_path: Path to the analyzed image
            - analysis: Analysis text
            - success: Whether analysis was successful
            - error: Error message if failed
        """
        if not image_paths:
            return []
        
        # For small batches, use single process
        if len(image_paths) <= 2 or not use_multiprocessing:
            results = []
            for image_path in image_paths:
                try:
                    analysis = self.analyze_image(image_path, prompt, temperature, max_tokens)
                    results.append({
                        "image_path": image_path,
                        "analysis": analysis,
                        "success": True
                    })
                except Exception as e:
                    results.append({
                        "image_path": image_path,
                        "analysis": None,
                        "success": False,
                        "error": str(e)
                    })
            return results
        
        # For larger batches, use multiprocessing
        if max_workers is None:
            max_workers = min(cpu_count(), len(image_paths))
        
        # Process in parallel
        try:
            # Add api_key and model to each input for the worker function
            work_items = [
                (image_path, prompt, temperature, max_tokens, self.api_key, self.model)
                for image_path in image_paths
            ]
            
            with Pool(processes=max_workers) as pool:
                results = pool.starmap(_analyze_image_worker_static, work_items)
            
            return results
        
        except Exception as e:
            # Fallback to single process on error
            results = []
            for image_path in image_paths:
                try:
                    analysis = self.analyze_image(image_path, prompt, temperature, max_tokens)
                    results.append({
                        "image_path": image_path,
                        "analysis": analysis,
                        "success": True
                    })
                except Exception as e:
                    results.append({
                        "image_path": image_path,
                        "analysis": None,
                        "success": False,
                        "error": str(e)
                    })
            return results
    
    def compare_images(
        self,
        image_path1: str,
        image_path2: str,
        comparison_aspects: Optional[List[str]] = None
    ) -> str:
        """
        Compare two images (requires sequential analysis)
        
        Args:
            image_path1: Path to first image
            image_path2: Path to second image
            comparison_aspects: Specific aspects to compare
        
        Returns:
            Comparison analysis
        """
        # Analyze both images
        desc1 = self.describe_image_detailed(image_path1, comparison_aspects)
        desc2 = self.describe_image_detailed(image_path2, comparison_aspects)
        
        # Format comparison
        comparison = f"""# Image Comparison

## Image 1: {Path(image_path1).name}
{desc1}

## Image 2: {Path(image_path2).name}
{desc2}

## Analysis Summary
Based on the descriptions above:

**Similarities:**
- Both images contain visual content that can be analyzed

**Differences:**
- Detailed comparison requires manual review of the descriptions above

**Note:** For more accurate comparison, please review the individual descriptions and specify particular aspects to compare."""
        
        return comparison
    
    def save_analysis(
        self,
        image_path: str,
        analysis: str,
        analysis_type: str = "general"
    ) -> str:
        """
        Save image analysis results to file
        
        Args:
            image_path: Path to the analyzed image
            analysis: The analysis text
            analysis_type: Type of analysis performed
        
        Returns:
            Path to saved results file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_name = Path(image_path).stem
        
        filename = f"vlm_{analysis_type}_{image_name}_{timestamp}.md"
        filepath = self.results_dir / filename
        
        markdown_content = f"""# VLM Analysis: {Path(image_path).name}

**Analysis Type:** {analysis_type}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Image:** {image_path}

---

{analysis}

---

*Generated using NVIDIA Nemotron VLM via Agent Skills*
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return str(filepath)
    
    def get_skill_info(self) -> Dict[str, Any]:
        """Get skill metadata and status information"""
        return {
            "name": self.name,
            "version": self.version,
            "model": self.model,
            "capabilities": [
                "image_analysis",
                "detailed_description",
                "text_extraction_ocr",
                "object_identification",
                "visual_question_answering",
                "image_comparison",
                "save_analysis_results",
                "streaming_output",
                "async_processing"
            ],
            "supported_formats": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"],
            "status": "initialized",
            "api_available": True,
            "results_directory": str(self.results_dir.absolute()),
            "skill_location": str(self.skill_location.absolute()) if self.skill_location.exists() else "not found"
        }


# ============================================================================
# Static worker functions for multiprocessing (must be at module level)
# ============================================================================

def _analyze_image_worker_static(
    image_path: str,
    prompt: str,
    temperature: float,
    max_tokens: int,
    api_key: str,
    model: str
) -> Dict[str, Any]:
    """
    Static worker function for multiprocessing image analysis
    
    This function is called in a separate process and needs to
    reinitialize the VLM skill since it can't be pickled.
    Must be at module level for multiprocessing to work.
    """
    try:
        # Reinitialize skill in worker process
        skill = NvidiaVLMSkill(api_key=api_key)
        skill.model = model
        
        analysis = skill.analyze_image(image_path, prompt, temperature, max_tokens)
        return {
            "image_path": image_path,
            "analysis": analysis,
            "success": True
        }
    except Exception as e:
        return {
            "image_path": image_path,
            "analysis": None,
            "success": False,
            "error": f"Error in worker process: {str(e)}"
        }


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
        api_key = os.getenv("INFERENCE_API_KEY")
        try:
            _global_skill_instance = NvidiaVLMSkill(api_key=api_key)
        except ValueError as e:
            # API key not set - return None
            print(f"Warning: {str(e)}")
            return None
    return _global_skill_instance


@skill_tool(
    name="analyze_image",
    description="Analyze an image and provide detailed visual understanding. Best for general image analysis. Supports batch processing with multiprocessing for multiple images.",
    return_direct=False
)
def analyze_image(
    image_path: str,
    prompt: str = "Identify what is in this image and describe it in detail.",
    temperature: float = 0.2,
    batch_image_paths: Optional[List[str]] = None,
    use_multiprocessing: bool = True
) -> str:
    """
    Analyze an image with a custom prompt
    
    Supports both single image and batch processing. For batch processing,
    provide batch_image_paths list and the function will process all images in parallel.
    
    Args:
        image_path: Path to the image file (required if batch_image_paths is None)
        prompt: Custom question or instruction about the image (optional)
        temperature: Creativity level 0.0-1.0 (default: 0.2 for precise analysis)
        batch_image_paths: Optional list of image paths for batch processing
        use_multiprocessing: Whether to use multiprocessing for batches (default: True)
    
    Returns:
        Analysis text describing the image(s), or JSON string for batch results
    
    Examples:
        >>> analyze_image("photo.jpg")
        >>> analyze_image("diagram.png", "Explain this technical diagram")
        >>> analyze_image("", batch_image_paths=["img1.jpg", "img2.jpg", "img3.jpg"])
    """
    skill = _get_skill_instance()
    if skill is None:
        return "❌ Error: INFERENCE_API_KEY not set. Get your key at https://build.nvidia.com/"
    
    # Check if batch processing is requested
    if batch_image_paths and len(batch_image_paths) > 1:
        # Batch processing mode
        results = skill.analyze_images_batch(
            batch_image_paths,
            prompt=prompt,
            temperature=temperature,
            use_multiprocessing=use_multiprocessing
        )
        
        # Format results as JSON string for return
        return json.dumps({
            "batch_processed": True,
            "total_images": len(batch_image_paths),
            "successful_count": sum(1 for r in results if r.get("success", False)),
            "results": results
        }, indent=2)
    else:
        # Single image mode (original behavior)
        return skill.analyze_image(image_path, prompt, temperature)


@skill_tool(
    name="describe_image_detailed",
    description="Get a comprehensive, detailed description of an image covering scene, objects, colors, text, and mood.",
    return_direct=False
)
def describe_image_detailed(
    image_path: str,
    aspects: Optional[List[str]] = None
) -> str:
    """
    Get comprehensive detailed description of an image
    
    Args:
        image_path: Path to the image file (required)
        aspects: Specific aspects to focus on (optional, e.g., ["colors", "objects", "scene"])
    
    Returns:
        Detailed multi-aspect description
    
    Examples:
        >>> describe_image_detailed("landscape.jpg")
        >>> describe_image_detailed("product.jpg", ["colors", "materials", "design"])
    """
    skill = _get_skill_instance()
    if skill is None:
        return "❌ Error: INFERENCE_API_KEY not set. Get your key at https://build.nvidia.com/"
    
    return skill.describe_image_detailed(image_path, aspects)


@skill_tool(
    name="extract_text_from_image",
    description="Extract all visible text from an image (OCR). Useful for documents, signs, screenshots, etc.",
    return_direct=False
)
def extract_text_from_image(image_path: str) -> str:
    """
    Extract text content from image (OCR capability)
    
    Args:
        image_path: Path to the image file (required)
    
    Returns:
        Extracted text with context
    
    Examples:
        >>> extract_text_from_image("document.jpg")
        >>> extract_text_from_image("screenshot.png")
        >>> extract_text_from_image("sign.jpg")
    """
    skill = _get_skill_instance()
    if skill is None:
        return "❌ Error: INFERENCE_API_KEY not set. Get your key at https://build.nvidia.com/"
    
    return skill.extract_text_from_image(image_path)


@skill_tool(
    name="identify_objects_in_image",
    description="Identify and list all significant objects in an image with their positions and attributes.",
    return_direct=False
)
def identify_objects_in_image(image_path: str) -> str:
    """
    Identify objects in the image
    
    Args:
        image_path: Path to the image file (required)
    
    Returns:
        Organized list of identified objects with attributes
    
    Examples:
        >>> identify_objects_in_image("room.jpg")
        >>> identify_objects_in_image("street_scene.png")
    """
    skill = _get_skill_instance()
    if skill is None:
        return "❌ Error: INFERENCE_API_KEY not set. Get your key at https://build.nvidia.com/"
    
    return skill.identify_objects(image_path)


@skill_tool(
    name="visual_question_answering",
    description="Answer specific questions about an image using visual reasoning.",
    return_direct=False
)
def visual_question_answering(image_path: str, question: str) -> str:
    """
    Answer questions about an image
    
    Args:
        image_path: Path to the image file (required)
        question: Specific question about the image (required)
    
    Returns:
        Answer based on visual analysis
    
    Examples:
        >>> visual_question_answering("traffic.jpg", "How many cars are visible?")
        >>> visual_question_answering("menu.jpg", "What is the price of the burger?")
        >>> visual_question_answering("diagram.png", "What does the red arrow point to?")
    """
    skill = _get_skill_instance()
    if skill is None:
        return "❌ Error: INFERENCE_API_KEY not set. Get your key at https://build.nvidia.com/"
    
    return skill.visual_qa(image_path, question)


@skill_tool(
    name="compare_images",
    description="Compare two images and identify similarities and differences.",
    return_direct=False
)
def compare_images(
    image_path1: str,
    image_path2: str,
    comparison_aspects: Optional[List[str]] = None
) -> str:
    """
    Compare two images
    
    Args:
        image_path1: Path to first image (required)
        image_path2: Path to second image (required)
        comparison_aspects: Specific aspects to compare (optional)
    
    Returns:
        Comparison analysis
    
    Examples:
        >>> compare_images("before.jpg", "after.jpg")
        >>> compare_images("design_v1.png", "design_v2.png", ["layout", "colors"])
    """
    skill = _get_skill_instance()
    if skill is None:
        return "❌ Error: INFERENCE_API_KEY not set. Get your key at https://build.nvidia.com/"
    
    return skill.compare_images(image_path1, image_path2, comparison_aspects)


@skill_tool(
    name="save_vlm_analysis",
    description="Save VLM analysis results to a markdown file for later reference.",
    return_direct=False
)
def save_vlm_analysis(
    image_path: str,
    analysis: str,
    analysis_type: str = "general"
) -> Dict[str, Any]:
    """
    Save image analysis results to file
    
    Args:
        image_path: Path to the analyzed image (required)
        analysis: The analysis text to save (required)
        analysis_type: Type of analysis performed (default: "general")
    
    Returns:
        Dictionary with file path and success status
    
    Examples:
        >>> result = analyze_image("photo.jpg")
        >>> save_vlm_analysis("photo.jpg", result, "detailed_description")
    """
    skill = _get_skill_instance()
    if skill is None:
        return {
            "error": "INFERENCE_API_KEY not set. Get your key at https://build.nvidia.com/",
            "success": False
        }
    
    try:
        filepath = skill.save_analysis(image_path, analysis, analysis_type)
        return {
            "success": True,
            "file_path": filepath,
            "message": f"✅ Analysis saved to: {filepath}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error saving analysis: {str(e)}"
        }


@skill_tool(
    name="get_vlm_skill_info",
    description="Get information about the VLM skill capabilities and status",
    return_direct=False
)
def get_vlm_skill_info() -> Dict[str, Any]:
    """
    Get metadata about the NVIDIA VLM skill
    
    Returns:
        Dictionary with skill information including capabilities and configuration
    """
    skill = _get_skill_instance()
    if skill is None:
        return {
            "error": "Skill not initialized - INFERENCE_API_KEY not set",
            "name": "nvidia-vlm",
            "status": "not_initialized"
        }
    
    return skill.get_skill_info()


# Main execution - supports both CLI JSON mode and example usage
if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='NVIDIA Vision Language Model Skill')
    parser.add_argument('--json', action='store_true',
                       help='JSON mode for subprocess execution')
    parser.add_argument('--example', action='store_true',
                       help='Run example usage')
    parser.add_argument('image_path', nargs='?',
                       help='Path to image file for testing')
    
    args = parser.parse_args()
    
    if args.json:
        # JSON CLI mode for subprocess execution
        try:
            # Read JSON input from stdin
            input_data = json.loads(sys.stdin.read())
            command = input_data.get('command', '')
            parameters = input_data.get('parameters', {})
            
            # Initialize skill
            api_key = parameters.get('api_key') or os.getenv('INFERENCE_API_KEY')
            if not api_key:
                print(json.dumps({
                    'success': False,
                    'error': 'INFERENCE_API_KEY not set'
                }))
                exit(1)
            
            skill = NvidiaVLMSkill(api_key=api_key)
            
            # Execute command
            if command == 'analyze_image':
                image_path = parameters.get('image_path')
                batch_image_paths = parameters.get('batch_image_paths')
                prompt = parameters.get('prompt', 'Identify what is in this image and describe it in detail.')
                temperature = parameters.get('temperature', 0.2)
                max_tokens = parameters.get('max_tokens', 1024)
                use_multiprocessing = parameters.get('use_multiprocessing', True)
                
                # Check if batch processing is requested
                if batch_image_paths and len(batch_image_paths) > 1:
                    # Batch processing mode
                    results = skill.analyze_images_batch(
                        batch_image_paths,
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        use_multiprocessing=use_multiprocessing
                    )
                    
                    print(json.dumps({
                        'success': True,
                        'batch_processed': True,
                        'total_images': len(batch_image_paths),
                        'successful_count': sum(1 for r in results if r.get('success', False)),
                        'results': results,
                        'command': command
                    }))
                else:
                    # Single image mode (original behavior)
                    if not image_path:
                        print(json.dumps({
                            'success': False,
                            'error': 'image_path parameter is required'
                        }))
                        exit(1)
                    
                    result = skill.analyze_image(
                        image_path=image_path,
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    print(json.dumps({
                        'success': True,
                        'result': result,
                        'command': command
                    }))
                
            elif command == 'compare_images':
                image_path1 = parameters.get('image_path1')
                image_path2 = parameters.get('image_path2')
                prompt = parameters.get('prompt')
                
                if not image_path1 or not image_path2:
                    print(json.dumps({
                        'success': False,
                        'error': 'Both image_path1 and image_path2 are required'
                    }))
                    exit(1)
                
                result = skill.compare_images(
                    image_path1=image_path1,
                    image_path2=image_path2,
                    prompt=prompt
                )
                
                print(json.dumps({
                    'success': True,
                    'result': result,
                    'command': command
                }))
                
            elif command == 'get_skill_info':
                info = skill.get_skill_info()
                print(json.dumps({
                    'success': True,
                    'result': info,
                    'command': command
                }))
                
            else:
                print(json.dumps({
                    'success': False,
                    'error': f'Unknown command: {command}'
                }))
                exit(1)
                
        except json.JSONDecodeError as e:
            print(json.dumps({
                'success': False,
                'error': f'Invalid JSON input: {str(e)}'
            }))
            exit(1)
        except Exception as e:
            print(json.dumps({
                'success': False,
                'error': str(e)
            }))
            exit(1)
    
    else:
        # Interactive/demo mode
        print("\n" + "="*60)
        print("NVIDIA Vision Language Model Skill - Agent Skills API Compliant")
        print("="*60 + "\n")
        
        # Check for API key
        api_key = os.getenv("INFERENCE_API_KEY")
        if not api_key:
            print("❌ Error: INFERENCE_API_KEY environment variable not set")
            print("\nPlease set it using:")
            print("  PowerShell: $env:INFERENCE_API_KEY='your-key-here'")
            print("  CMD:        set INFERENCE_API_KEY=your-key-here")
            print("  Linux/Mac:  export INFERENCE_API_KEY='your-key-here'")
            print("\nGet your key at: https://build.nvidia.com/")
            exit(1)
        
        # Initialize and test skill
        try:
            skill = NvidiaVLMSkill()
            print("✅ Skill initialized successfully\n")
            
            # Show skill info
            info = skill.get_skill_info()
            print("📊 Skill Information:")
            print(json.dumps(info, indent=2))
            print("\n" + "="*60 + "\n")
            
            # Test with a sample image if provided
            if args.image_path:
                test_image = args.image_path
                print(f"🧪 Testing VLM analysis on: {test_image}")
                print("\n" + "-"*60 + "\n")
                
                result = skill.analyze_image(test_image)
                print(result)
                
                print("\n" + "-"*60 + "\n")
                print("✅ Test completed successfully!")
            else:
                print("💡 To test image analysis, run with an image path:")
                print(f"   python {sys.argv[0]} path/to/image.jpg")
            
            print("\n" + "="*60 + "\n")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            exit(1)

