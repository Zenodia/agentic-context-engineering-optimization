#!/usr/bin/env python3
"""
Verification script for image_generation_skill

Tests that the skill follows the Agent Skills standard:
- SKILL.md (required) with YAML frontmatter
- scripts/ (optional) for executable code
- assets/ (optional) for templates and resources
- references/ (optional) for documentation

Reference: https://agentskills.io/what-are-skills
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists and report"""
    exists = filepath.exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath.name}")
    return exists

def main():
    print("\n" + "="*70)
    print("Image Generation Skill - Agent Skills Standard Verification")
    print("="*70 + "\n")
    print("Reference: https://agentskills.io/what-are-skills\n")
    
    # Define base path
    skill_path = Path(__file__).parent / "image_generation_skill"
    
    if not skill_path.exists():
        print("❌ Error: image_generation_skill directory not found!")
        return False
    
    print(f"📁 Skill directory: {skill_path}\n")
    
    # Check all required files
    print("Checking required files:")
    print("-" * 70)
    
    all_good = True
    
    # Core files (Agent Skills standard)
    all_good &= check_file_exists(skill_path / "SKILL.md", "SKILL.md (required: core documentation)")
    
    # Optional: config.yaml (custom extension, not in standard but useful)
    config_exists = check_file_exists(skill_path / "config.yaml", "config.yaml (optional: configuration)")
    
    # Scripts directory (optional but recommended)
    print("\nChecking scripts/ directory:")
    print("-" * 70)
    scripts_dir = skill_path / "scripts"
    all_good &= check_file_exists(scripts_dir / "__init__.py", "scripts/__init__.py")
    all_good &= check_file_exists(scripts_dir / "image_gen_skill.py", "scripts/image_gen_skill.py (main)")
    
    # Optional directories (Agent Skills standard)
    print("\nChecking optional directories:")
    print("-" * 70)
    assets_exists = check_file_exists(skill_path / "assets", "assets/ (optional: templates, resources)")
    refs_exists = check_file_exists(skill_path / "references", "references/ (optional: documentation)")
    
    # Check SKILL.md content
    print("\nChecking SKILL.md structure:")
    print("-" * 70)
    
    skill_md = skill_path / "SKILL.md"
    try:
        with open(skill_md, 'r', encoding='utf-8') as f:
            content = f.read()
        
        has_frontmatter = content.startswith("---")
        has_name = "name: image-generation" in content
        has_description = "description:" in content
        has_dependencies = "dependencies:" in content
        
        print(f"{'✅' if has_frontmatter else '❌'} Has YAML frontmatter")
        print(f"{'✅' if has_name else '❌'} Has skill name")
        print(f"{'✅' if has_description else '❌'} Has description")
        print(f"{'✅' if has_dependencies else '❌'} Has dependencies")
        
        all_good &= has_frontmatter and has_name and has_description
    except Exception as e:
        print(f"❌ Error reading SKILL.md: {e}")
        all_good = False
    
    # Check config.yaml
    print("\nChecking config.yaml structure:")
    print("-" * 70)
    
    try:
        import yaml
        config_path = skill_path / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        has_name_cfg = 'name' in config
        has_version = 'version' in config
        has_skill_type = 'skill_type' in config
        has_runtime = 'runtime' in config
        
        print(f"{'✅' if has_name_cfg else '❌'} Has name field")
        print(f"{'✅' if has_version else '❌'} Has version field")
        print(f"{'✅' if has_skill_type else '❌'} Has skill_type field")
        print(f"{'✅' if has_runtime else '❌'} Has runtime config")
        
        if has_name_cfg:
            print(f"   Name: {config['name']}")
        if has_version:
            print(f"   Version: {config['version']}")
        if has_skill_type:
            print(f"   Type: {config['skill_type']}")
        
        all_good &= has_name_cfg and has_version and has_skill_type
    except Exception as e:
        print(f"❌ Error reading config.yaml: {e}")
        all_good = False
    
    # Check main script
    print("\nChecking main script:")
    print("-" * 70)
    
    try:
        script_path = scripts_dir / "image_gen_skill.py"
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        has_class = "class ImageGenerationSkill" in script_content
        has_decorator = "@skill_tool" in script_content
        has_generate = "def generate_image" in script_content
        has_multiple = "def generate_multiple_images" in script_content
        
        print(f"{'✅' if has_class else '❌'} Has ImageGenerationSkill class")
        print(f"{'✅' if has_decorator else '❌'} Has @skill_tool decorators")
        print(f"{'✅' if has_generate else '❌'} Has generate_image method")
        print(f"{'✅' if has_multiple else '❌'} Has generate_multiple_images method")
        
        all_good &= has_class and has_decorator and has_generate
    except Exception as e:
        print(f"❌ Error reading main script: {e}")
        all_good = False
    
    # Check API key
    print("\nChecking environment:")
    print("-" * 70)
    
    api_key = os.getenv("NVIDIA_API_KEY")
    has_api_key = api_key is not None and len(api_key) > 0
    
    print(f"{'✅' if has_api_key else '⚠️ '} NVIDIA_API_KEY environment variable")
    if not has_api_key:
        print("   Note: API key not set. Set it to test generation:")
        print("   PowerShell: $env:NVIDIA_API_KEY='your-key'")
        print("   CMD: set NVIDIA_API_KEY=your-key")
        print("   Linux/Mac: export NVIDIA_API_KEY='your-key'")
    
    # Try to import the skill
    print("\nTesting skill import:")
    print("-" * 70)
    
    try:
        # Add parent directory to path
        if str(skill_path.parent) not in sys.path:
            sys.path.insert(0, str(skill_path.parent))
        
        from image_generation_skill.scripts.image_gen_skill import ImageGenerationSkill
        print("✅ Successfully imported ImageGenerationSkill")
        
        # Try to get skill info
        try:
            if has_api_key:
                skill = ImageGenerationSkill()
                info = skill.get_skill_info()
                print("✅ Successfully initialized skill")
                print(f"   Skill name: {info['name']}")
                print(f"   Version: {info['version']}")
                print(f"   Model: {info['model']}")
                print(f"   Status: {info['status']}")
            else:
                print("⚠️  Skipping initialization (no API key)")
        except Exception as e:
            print(f"⚠️  Could not initialize skill: {e}")
    except Exception as e:
        print(f"❌ Failed to import skill: {e}")
        all_good = False
    
    # Final summary
    print("\n" + "="*70)
    if all_good:
        print("✅ VERIFICATION PASSED")
        print("\nThe image_generation_skill follows the Agent Skills standard!")
        print("\nStructure:")
        print("  ✓ SKILL.md (required) - core documentation with YAML frontmatter")
        print("  ✓ scripts/ - executable code")
        print("  ✓ assets/ - templates and resources")
        print("  ✓ references/ - documentation")
        print("\nNext steps:")
        print("1. Set NVIDIA_API_KEY environment variable")
        print("2. Run: python test_image_gen_skill.py (in project root)")
        print("3. Run: python gradio_agent_chatbot.py")
        print("4. Try: 'Generate an image of a coffee shop'")
    else:
        print("❌ VERIFICATION FAILED")
        print("\nSome required files or configurations are missing.")
        print("Please check the errors above.")
        print("\nAgent Skills Standard: https://agentskills.io/what-are-skills")
    print("="*70 + "\n")
    
    return all_good

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

