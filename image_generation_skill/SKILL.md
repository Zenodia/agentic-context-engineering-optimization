---
name: image-generation
version: 1.0.0
description: AI-powered image generation skill using NVIDIA's Flux.1 Schnell model for fast, high-quality text-to-image generation. Create stunning images from text prompts with customizable dimensions and quality settings.
author: Zenodia
license: MIT
tags:
  - image-generation
  - text-to-image
  - ai-art
  - flux
  - nvidia
  - generative-ai
runtime:
  type: python
  version: ">=3.10"
dependencies:
  - requests>=2.31.0
  - PyYAML>=6.0
permissions:
  - file:write
  - network:api
environment:
  NVIDIA_API_KEY:
    description: NVIDIA API key for accessing Flux.1 Schnell model
    required: true
---

# NVIDIA Image Generation Skill

An AI-powered image generation skill that uses NVIDIA's Flux.1 Schnell model to help users create high-quality images from text descriptions. Fast generation with excellent results.

## When to Use This Skill

Use this skill whenever users need to:
- Generate images from text descriptions
- Create visual content quickly
- Design mockups or concept art
- Visualize ideas or scenarios
- Generate multiple variations of a concept
- Create custom artwork or illustrations
- Produce images for presentations or documents

**Trigger phrases:** "generate an image", "create a picture", "make an image of", "show me", "visualize", "draw", "design", "I need an image of"

## Core Capabilities

### 1. Text-to-Image Generation
Generate high-quality images from text prompts:
- Fast generation (Schnell = "fast" in German)
- High-quality output with excellent detail
- Customizable dimensions (512x512 to 1920x1080+)
- Reproducible results with seed control
- Quality control via inference steps

### 2. Multiple Variations
Create several variations of the same concept:
- Generate 2-10 variations in one call
- Automatic seed variation for diversity
- Batch processing with progress tracking
- Organized file naming

### 3. Customizable Parameters
Fine-tune generation to your needs:
- **Width & Height:** Any dimensions (recommended: 512-1920px)
- **Seed:** Control randomness for reproducibility
- **Steps:** Trade speed for quality (4-50 steps)
- **Prompt:** Detailed text descriptions

## Usage Instructions

### For AI Agents

When a user requests image generation, follow this workflow:

#### Method 1: Single Image Generation (Most Common)

```python
from scripts.image_gen_skill import ImageGenerationSkill

# Initialize the skill
skill = ImageGenerationSkill()

# Generate an image
prompt = "a simple coffee shop interior"
result = skill.generate_image(
    prompt=prompt,
    width=1024,
    height=1024,
    seed=0,
    steps=4
)

if result["success"]:
    print(f"✅ Image generated: {result['image_path']}")
    print(f"Metadata: {result['metadata']}")
else:
    print(f"❌ Error: {result['error']}")
```

#### Method 2: Multiple Variations

```python
# Generate multiple variations
result = skill.generate_multiple_images(
    prompt="futuristic city skyline at night",
    count=4,
    width=1024,
    height=768,
    steps=4
)

print(f"Generated {result['successful']}/{result['total']} images")
for i, img_result in enumerate(result['results']):
    if img_result['success']:
        print(f"  {i+1}. {img_result['image_path']}")
```

#### Method 3: Custom Dimensions

```python
# Generate wide landscape image
result = skill.generate_image(
    prompt="panoramic mountain landscape at sunset",
    width=1920,
    height=1080,
    steps=8  # Higher steps for better quality
)
```

#### Method 4: Reproducible Generation

```python
# Use specific seed for reproducibility
result = skill.generate_image(
    prompt="abstract geometric pattern",
    seed=42,  # Same seed = same image
    steps=4
)
```

## Example Interactions

### Example 1: Simple Image Request

**User:** "Generate an image of a simple coffee shop interior"

**Agent Action:**
1. Parse the prompt from user input
2. Invoke `generate_image()` with the prompt
3. Display the result and image path
4. Offer to generate variations or adjust parameters

**Agent Response:**
```
🎨 Generating your image...

✅ Image generated successfully!
📁 Saved to: generated_images/img_20260202_143022_a_simple_coffee_shop_inter.png

The image shows a cozy coffee shop interior with warm lighting, wooden furniture, 
and a modern aesthetic.

Would you like me to:
1. Generate more variations with different styles?
2. Adjust the dimensions (currently 1024x1024)?
3. Generate with higher quality (more steps)?
```

### Example 2: Multiple Variations

**User:** "Create 4 variations of a futuristic robot design"

**Agent Action:**
1. Recognize request for multiple variations
2. Invoke `generate_multiple_images()` with count=4
3. Show progress and results
4. Offer to refine specific variations

**Agent Response:**
```
🎨 Generating 4 variations of your concept...

✅ Generated 4/4 images successfully!

📁 Saved to:
  1. generated_images/futuristic_robot_design_var1.png
  2. generated_images/futuristic_robot_design_var2.png
  3. generated_images/futuristic_robot_design_var3.png
  4. generated_images/futuristic_robot_design_var4.png

All variations show unique interpretations of a futuristic robot with different 
styles and details.

Which variation would you like to explore further?
```

### Example 3: Custom Parameters

**User:** "Generate a wide landscape image of mountains, make it high quality"

**Agent Action:**
1. Recognize need for custom dimensions (wide = 16:9)
2. Increase steps for higher quality
3. Generate with appropriate settings
4. Provide technical details

**Agent Response:**
```
🎨 Generating high-quality wide landscape image...

Settings:
- Resolution: 1920x1080 (16:9 widescreen)
- Quality: 8 steps (higher quality)

✅ Image generated successfully!
📁 Saved to: generated_images/img_20260202_143525_mountains_landscape.png

The image features a stunning mountain landscape with excellent detail 
and sharp clarity thanks to the higher quality settings.

Generation details:
- Model: Flux.1 Schnell
- Dimensions: 1920x1080
- Steps: 8
- Seed: 0
```

### Example 4: Reproducible Generation

**User:** "Generate the same image again with seed 42"

**Agent Action:**
1. Use specific seed for reproducibility
2. Generate with same prompt and seed
3. Confirm reproducible result

**Agent Response:**
```
🎨 Generating image with seed 42 for reproducibility...

✅ Image generated!
📁 Saved to: generated_images/img_20260202_143622_abstract_pattern.png

Using seed 42 ensures this exact image can be regenerated. 
Save this seed number if you need to reproduce this result later.
```

## Best Practices for Agents

### 1. Always Confirm API Key Availability

Before invoking any generation method, check if NVIDIA_API_KEY is set:

```python
try:
    skill = ImageGenerationSkill()
except ValueError as e:
    return """
    ❌ NVIDIA API key is not configured. To use image generation:
    
    1. Get your free API key at: https://build.nvidia.com/
    2. Set the environment variable:
       - Windows PowerShell: $env:NVIDIA_API_KEY="your-key"
       - Windows CMD: set NVIDIA_API_KEY=your-key
       - Linux/Mac: export NVIDIA_API_KEY='your-key'
    3. Restart the application
    """
```

### 2. Optimize Prompts for Better Results

Help users write effective prompts:

**Good Prompts:**
- "A cozy coffee shop interior with warm lighting and wooden furniture"
- "Futuristic city skyline at night with neon lights and flying cars"
- "Abstract geometric pattern with blue and gold colors"

**Poor Prompts:**
- "coffee" (too vague)
- "make something cool" (not descriptive)
- Very long prompts (>200 words - be concise)

### 3. Choose Appropriate Dimensions

Guide users on dimension selection:

| Use Case | Recommended Size | Aspect Ratio |
|----------|-----------------|--------------|
| Square images | 1024x1024 | 1:1 |
| Portrait | 768x1024 | 3:4 |
| Landscape | 1024x768 | 4:3 |
| Widescreen | 1920x1080 | 16:9 |
| Social media | 1080x1080 | 1:1 |

### 4. Adjust Steps for Quality

Help users understand the quality-speed tradeoff:

| Steps | Quality | Speed | Use Case |
|-------|---------|-------|----------|
| 4 | Good | Fast | Quick iterations, testing |
| 6-8 | Better | Medium | General use, good balance |
| 10-20 | Excellent | Slower | Final output, high quality |
| 20+ | Best | Slow | Professional use, critical quality |

**Note:** Flux.1 Schnell is optimized for 4 steps, so higher values may not improve much.

### 5. Handle Multiple Generations Gracefully

For batch processing, provide progress updates:

```python
print("🎨 Generating 4 variations...")
print("This may take 10-20 seconds...")

result = skill.generate_multiple_images(prompt, count=4)

print(f"\n✅ Generated {result['successful']}/{result['total']} images")
```

### 6. Save and Organize Results

Images are automatically saved with organized naming:
- Timestamp included for uniqueness
- Prompt snippet in filename for easy identification
- All images in `generated_images/` directory
- Metadata can be saved separately

### 7. Offer Follow-up Actions

After generating images, suggest next steps:

```
✅ Image generated successfully!

Next steps:
• 🔄 Generate more variations with different styles
• 📐 Try different dimensions or aspect ratios
• ⚙️ Adjust quality settings (more steps)
• 🎨 Refine the prompt for different results
• 💾 Save metadata for reproduction
```

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "NVIDIA_API_KEY not set" | Missing API key | Guide user to set environment variable |
| "API request failed: 401" | Invalid API key | Verify key is correct |
| "API request failed: 429" | Rate limit exceeded | Suggest waiting or reducing frequency |
| "No image data in response" | API issue | Retry or check API status |
| "Connection timeout" | Network issue | Retry with exponential backoff |

### Fallback Strategy

If image generation fails, offer alternatives:

```python
try:
    result = skill.generate_image(prompt)
except Exception as e:
    return """
    ❌ Image generation failed. Let me help you:
    
    1. Would you like to try with different settings?
    2. Should I attempt to refine your prompt?
    3. Would you prefer to use a different size or quality?
    
    Please let me know how you'd like to proceed.
    """
```

## Technical Details

### NVIDIA Model Specifications

**Model:** `black-forest-labs/flux.1-schnell`
- **Type:** Text-to-image diffusion model
- **Speed:** Optimized for fast generation (Schnell = Fast)
- **Quality:** High-quality, detailed outputs
- **Optimization:** Best at 4 inference steps
- **API:** NVIDIA AI Foundation Models
- **Endpoint:** https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-schnell

### Supported Image Formats

- Output: PNG (Base64 encoded)
- Maximum file size: Depends on dimensions
- Color space: RGB

### Generation Parameters

```python
{
    "prompt": str,           # Text description (required)
    "width": int,            # Image width in pixels (default: 1024)
    "height": int,           # Image height in pixels (default: 1024)
    "seed": int,             # Random seed (default: 0)
    "steps": int             # Inference steps (default: 4)
}
```

### Output Format

Generation results include:

```python
{
    "success": bool,         # Whether generation succeeded
    "image_path": str,       # Path to saved image file
    "image_data": str,       # Base64 encoded image data
    "metadata": {
        "prompt": str,
        "width": int,
        "height": int,
        "seed": int,
        "steps": int,
        "generated_at": str,  # ISO timestamp
        "model": str
    },
    "error": str             # Error message if failed (optional)
}
```

### File Storage

- **Location:** `generated_images/` directory (created automatically)
- **Naming:** `img_{timestamp}_{prompt_snippet}.png`
- **Format:** PNG
- **Metadata:** Can be saved as separate JSON file

## Integration Patterns

### Web Applications

```python
import gradio as gr
from scripts.image_gen_skill import ImageGenerationSkill

skill = ImageGenerationSkill()

def generate_handler(prompt, width, height, steps):
    try:
        result = skill.generate_image(prompt, width, height, steps=steps)
        if result["success"]:
            return result["image_path"]
        else:
            return f"Error: {result['error']}"
    except Exception as e:
        return f"Error: {str(e)}"

interface = gr.Interface(
    fn=generate_handler,
    inputs=[
        gr.Textbox(label="Prompt", placeholder="Describe the image..."),
        gr.Slider(512, 1920, value=1024, label="Width"),
        gr.Slider(512, 1920, value=1024, label="Height"),
        gr.Slider(4, 20, value=4, step=1, label="Quality Steps")
    ],
    outputs=gr.Image(type="filepath")
)
```

### Command-Line Tools

```python
#!/usr/bin/env python3
import sys
from scripts.image_gen_skill import ImageGenerationSkill

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_cli.py '<prompt>' [width] [height]")
        return
    
    skill = ImageGenerationSkill()
    prompt = sys.argv[1]
    width = int(sys.argv[2]) if len(sys.argv) > 2 else 1024
    height = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
    
    print(f"🎨 Generating: {prompt}")
    result = skill.generate_image(prompt, width, height)
    
    if result["success"]:
        print(f"✅ Saved to: {result['image_path']}")
    else:
        print(f"❌ Error: {result['error']}")

if __name__ == "__main__":
    main()
```

### Batch Processing

```python
from pathlib import Path

prompts = [
    "a cozy coffee shop interior",
    "futuristic city skyline",
    "abstract geometric pattern"
]

skill = ImageGenerationSkill()

for i, prompt in enumerate(prompts, 1):
    print(f"Generating {i}/{len(prompts)}: {prompt}")
    result = skill.generate_image(prompt)
    
    if result["success"]:
        print(f"  ✅ {result['image_path']}")
    else:
        print(f"  ❌ {result['error']}")
```

## Configuration Options

### Initialization Parameters

```python
skill = ImageGenerationSkill(
    api_key="your_nvidia_api_key",  # Optional if env var set
    output_dir="custom/path"        # Optional custom output directory
)
```

### Generation Options

**Standard Generation:**
- `prompt` (str, required): Text description
- `width` (int): Image width in pixels
- `height` (int): Image height in pixels
- `seed` (int): Random seed
- `steps` (int): Inference steps
- `save` (bool): Whether to save to disk
- `filename` (str): Custom filename

**Multiple Variations:**
- `prompt` (str, required): Text description
- `count` (int): Number of variations
- `width` (int): Image width
- `height` (int): Image height
- `steps` (int): Inference steps
- `vary_seed` (bool): Use different seeds

## Advanced Features

### Seed Control for Reproducibility

Generate the same image multiple times:

```python
# First generation
result1 = skill.generate_image("abstract art", seed=42)

# Later - regenerate exact same image
result2 = skill.generate_image("abstract art", seed=42)

# result1 and result2 will be identical
```

### Quality Optimization

Balance speed and quality:

```python
# Fast iteration (4 steps)
quick = skill.generate_image(prompt, steps=4)

# Balanced (6-8 steps)
balanced = skill.generate_image(prompt, steps=6)

# High quality (10+ steps)
high_quality = skill.generate_image(prompt, steps=12)
```

### Dimension Presets

Common presets for convenience:

```python
# Social media square
instagram = skill.generate_image(prompt, width=1080, height=1080)

# HD wallpaper
wallpaper = skill.generate_image(prompt, width=1920, height=1080)

# Portrait mode
portrait = skill.generate_image(prompt, width=768, height=1024)
```

## Troubleshooting

### Issue: Images look low quality
**Solution:** Increase the `steps` parameter (try 8-12 instead of 4)

### Issue: Generation is too slow
**Solution:** Use default 4 steps; Flux.1 Schnell is optimized for speed

### Issue: Images don't match prompt
**Solution:** Make prompt more specific and descriptive; add details about style, lighting, composition

### Issue: Rate limit errors
**Solution:** Add delay between requests; reduce batch sizes; check API tier limits

### Issue: Out of memory errors
**Solution:** Reduce image dimensions; avoid extremely large sizes (>2048px)

## Skill Information

Query skill metadata:

```python
info = skill.get_skill_info()
print(info)
# {
#   "name": "image-generation",
#   "version": "1.0.0",
#   "model": "black-forest-labs/flux.1-schnell",
#   "capabilities": [...],
#   "supported_resolutions": [...],
#   "status": "initialized"
# }
```

## Future Enhancements

Planned features for future versions:
- Style presets (photorealistic, artistic, anime, etc.)
- Image-to-image transformations
- Inpainting and outpainting
- ControlNet for precise control
- Batch optimization for large-scale generation
- Integration with other NVIDIA models
- Advanced prompt templates
- Style transfer capabilities
- Resolution upscaling
- Custom model fine-tuning support

---

**Note:** This skill requires Python 3.10+ and an NVIDIA API key. Get your free API key at https://build.nvidia.com/

Always validate prompts, provide clear feedback, handle errors gracefully, and offer appropriate follow-up actions for the best user experience.

