---
name: nvidia-ideagen
version: 1.0.0
description: AI-powered idea generation skill using NVIDIA's Nemotron model for brainstorming, concept development, and creative ideation. Generate, expand, and manage ideas through natural language.
author: Zenodia
license: MIT
tags:
  - ideation
  - brainstorming
  - creativity
  - nvidia
  - llm
  - innovation
runtime:
  type: python
  version: ">=3.10"
dependencies:
  - openai>=1.0.0
  - PyYAML>=6.0
permissions:
  - file:write
  - network:api
environment:
  NVIDIA_API_KEY:
    description: NVIDIA API key for accessing Nemotron model
    required: true
---

# NVIDIA Idea Generation Skill

An AI-powered idea generation skill that uses NVIDIA's Nemotron model (`llama-3.1-nemotron-nano-8b-v1`) to help users brainstorm, develop, and expand ideas through natural language interactions. 

## When to Use This Skill

Use this skill whenever users need to:
- Generate multiple ideas on a specific topic
- Brainstorm concepts for a domain or field
- Expand existing ideas with detailed analysis
- Develop creative solutions to problems
- Explore innovative approaches to challenges
- Build a personal idea library

**Trigger phrases:** "generate ideas", "brainstorm", "come up with concepts", "expand this idea", "ideate", "think of solutions", "creative ideas"

## Core Capabilities

### 1. Quick Idea Generation
Generate multiple creative ideas rapidly on any topic with adjustable creativity levels:
- Customizable number of ideas (1-10)
- Adjustable creativity temperature (0.0-1.0)
- Optional context and constraints
- Structured output with titles, descriptions, and action items
- Streaming support for real-time output

### 2. Deep Brainstorming
Conceptual brainstorming for specific domains with constraints:
- Domain-specific ideation
- Focus area specification
- Constraint-based generation
- Implementation considerations
- Benefit analysis

### 3. Idea Expansion
Take existing ideas and expand them with detailed analysis:
- **Detailed expansion**: Comprehensive breakdown with implementation steps
- **Technical expansion**: Architecture, technologies, and technical details
- **Creative expansion**: Variations, alternatives, and innovative extensions
- **Business expansion**: Market analysis, ROI, and stakeholder considerations

### 4. Idea Management
Save, load, and organize generated ideas:
- Markdown format for easy reading
- Timestamp and metadata tracking
- Search and list capabilities
- Personal idea library building

## Usage Instructions

### For AI Agents

When a user mentions idea generation, brainstorming, or creative thinking, follow this workflow:

#### Method 1: Quick Idea Generation (Most Common)

```python
from scripts.ideagen_skill import NvidiaIdeaGenSkill

# Initialize the skill
skill = NvidiaIdeaGenSkill()

# Generate ideas
user_topic = "sustainable urban transportation solutions"
ideas_text = ""

for chunk in skill.generate_ideas_stream(
    topic=user_topic,
    num_ideas=5,
    creativity=0.7,
    context="Focus on solutions for cities with population under 1 million"
):
    ideas_text += chunk
    # Stream to user for real-time feedback

# Save if user requests
if user_wants_to_save:
    filepath = skill.save_ideas(user_topic, ideas_text)
    print(f"✅ Saved to: {filepath}")
```

#### Method 2: Constrained Brainstorming

```python
# For domain-specific ideation with requirements
constraints = [
    "Must be cost-effective",
    "Should work offline",
    "Target small businesses"
]

concepts_text = ""
for chunk in skill.brainstorm_concepts(
    domain="Healthcare Technology",
    focus_area="Remote patient monitoring",
    constraints=constraints
):
    concepts_text += chunk

# Present to user with structured formatting
```

#### Method 3: Idea Expansion

```python
# When user wants to develop an existing idea
existing_idea = """
A mobile app that gamifies recycling for city residents by 
giving points for each recyclable item scanned and redeemed.
"""

expanded_text = ""
for chunk in skill.expand_idea(
    idea=existing_idea,
    expansion_type="business"  # or "detailed", "technical", "creative"
):
    expanded_text += chunk

# Present detailed analysis to user
```

## Example Interactions

### Example 1: Quick Brainstorming Session

**User:** "Generate 5 ideas for improving remote team collaboration"

**Agent Action:**
1. Invoke `generate_ideas_stream()` with topic
2. Set num_ideas=5, creativity=0.7
3. Stream output to user in real-time
4. Offer to save ideas if useful

**Agent Response:**
```
I'll generate 5 innovative ideas for remote team collaboration. Here they are:

[Stream ideas as they generate...]

Would you like me to:
1. Save these ideas for later reference?
2. Expand any of these ideas with more details?
3. Generate more ideas with different parameters?
```

### Example 2: Constrained Domain Brainstorming

**User:** "I need concepts for educational software for elementary math, but it needs to work offline and be engaging"

**Agent Action:**
1. Parse domain: "Educational Software"
2. Parse focus: "Elementary math learning"
3. Parse constraints: ["Must work offline", "Must be engaging"]
4. Invoke `brainstorm_concepts()` with these parameters
5. Stream results

**Agent Response:**
```
I'll brainstorm educational software concepts for elementary math with your constraints...

[Streaming concepts with implementation details...]

These concepts all prioritize offline functionality and engagement. 
Would you like me to expand any of these in more detail?
```

### Example 3: Idea Expansion

**User:** "Can you expand on the gamified recycling app idea from a business perspective?"

**Agent Action:**
1. Invoke `expand_idea()` with expansion_type="business"
2. Stream detailed business analysis
3. Cover market size, revenue models, competition, ROI

**Agent Response:**
```
I'll analyze the gamified recycling app from a business perspective...

[Streaming business analysis including:]
- Market opportunity and sizing
- Target demographics
- Revenue models (subscriptions, partnerships, municipal contracts)
- Competitive landscape
- Implementation costs and timeline
- Key success metrics
- Risk factors and mitigation strategies

Would you like me to save this analysis or explore another angle (technical/creative)?
```

## Best Practices for Agents

### 1. Always Confirm API Key Availability

Before invoking any generation method, check if NVIDIA_API_KEY is set:

```python
try:
    skill = NvidiaIdeaGenSkill()
except ValueError as e:
    return """
    ❌ NVIDIA API key is not configured. To use idea generation:
    
    1. Get your free API key at: https://build.nvidia.com/
    2. Set the environment variable:
       - Windows PowerShell: $env:NVIDIA_API_KEY="your-key"
       - Windows CMD: set NVIDIA_API_KEY=your-key
       - Linux/Mac: export NVIDIA_API_KEY='your-key'
    3. Restart the application
    """
```

### 2. Guide Creativity Settings

Help users choose appropriate creativity levels:

| Creativity | Use Case | Example |
|------------|----------|---------|
| 0.3-0.4 | Conservative, practical ideas | Business plans, technical documentation |
| 0.5-0.7 | Balanced innovation | General brainstorming, product features |
| 0.8-0.9 | Highly creative | Marketing campaigns, artistic projects |
| 0.9-1.0 | Experimental | Research, unconventional solutions |

### 3. Structure User Interaction

**Always ask clarifying questions if topic is vague:**
```
User: "Give me some ideas"

Agent: "I'd be happy to generate ideas! To provide the most relevant suggestions:
1. What topic or domain are you interested in?
2. How many ideas would you like? (I can generate 1-10)
3. Any specific constraints or requirements?
4. Should the ideas be practical, creative, or experimental?"
```

### 4. Offer Follow-up Actions

After generating ideas, always suggest next steps:
```
✅ Ideas generated successfully!

Next steps:
• 💾 Save these ideas to your idea library
• 🔍 Expand any idea with detailed analysis
• 🔄 Generate more variations with different creativity
• 📋 Combine ideas for hybrid approaches
```

### 5. Handle Streaming Gracefully

Stream output for better user experience:
```python
# Good: Stream with progress indication
print("🤔 Generating ideas...")
for chunk in skill.generate_ideas_stream(topic, num_ideas):
    print(chunk, end="", flush=True)
print("\n✅ Complete!")

# Bad: Wait for full generation then dump text
result = skill.generate_ideas(topic, num_ideas)  # User waits with no feedback
print(result)  # Sudden wall of text
```

### 6. Manage Saved Ideas

Help users organize their idea library:
```python
# List saved ideas periodically
saved_ideas = skill.list_saved_ideas()
if len(saved_ideas) > 10:
    print(f"💡 You have {len(saved_ideas)} saved ideas in your library!")
    print("Consider reviewing and organizing them.")
```

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "NVIDIA_API_KEY not set" | Missing API key | Guide user to set environment variable |
| "API rate limit exceeded" | Too many requests | Suggest waiting or reducing idea count |
| "Connection timeout" | Network issue | Retry with exponential backoff |
| "Invalid topic" | Empty or too short | Ask user to provide more details |
| "Model overloaded" | NVIDIA API busy | Retry after brief delay |

### Fallback Strategy

If idea generation fails, offer alternatives:
```python
try:
    ideas = skill.generate_ideas_stream(topic, num_ideas)
except Exception as e:
    return """
    ❌ Idea generation failed. Let me help you brainstorm manually:
    
    Please provide:
    1. What problem are you trying to solve?
    2. Who is your target audience?
    3. What resources do you have available?
    4. Any constraints I should know about?
    
    I'll help you develop ideas based on your answers.
    """
```

## Technical Details

### NVIDIA Model Specifications

**Model:** `nvidia/llama-3.1-nemotron-nano-8b-v1`
- **Size:** 8B parameters (nano variant)
- **Context Window:** 4,096 tokens
- **Streaming:** Supported
- **API:** OpenAI-compatible interface
- **Endpoint:** https://integrate.api.nvidia.com/v1

### Generation Parameters

```python
{
    "temperature": 0.7,          # Creativity (0.0-1.0)
    "top_p": 0.95,              # Nucleus sampling
    "max_tokens": 4096,         # Maximum response length
    "frequency_penalty": 0.2,   # Reduce repetition
    "presence_penalty": 0.1,    # Encourage topic diversity
    "stream": True              # Enable streaming
}
```

### Output Format

All ideas are saved in Markdown format:
```markdown
# Ideas: [Topic Name]

**Generated:** YYYY-MM-DD HH:MM:SS

---

[Generated content with structured formatting]

---

*Generated using NVIDIA Nemotron Model*
```

### File Storage

- **Location:** `ideas/` directory (created automatically)
- **Naming:** `ideas_{topic}_{timestamp}.md`
- **Encoding:** UTF-8
- **Format:** Markdown with frontmatter-style metadata

## Integration Patterns

### Web Applications

```python
import gradio as gr
from scripts.ideagen_skill import NvidiaIdeaGenSkill

skill = NvidiaIdeaGenSkill()

def generate_handler(topic, num_ideas, creativity):
    try:
        result = ""
        for chunk in skill.generate_ideas_stream(topic, num_ideas, creativity=creativity):
            result += chunk
        return result
    except Exception as e:
        return f"❌ Error: {str(e)}"

interface = gr.Interface(
    fn=generate_handler,
    inputs=[
        gr.Textbox(label="Topic"),
        gr.Slider(1, 10, value=5, label="Number of Ideas"),
        gr.Slider(0, 1, value=0.7, label="Creativity")
    ],
    outputs=gr.Markdown()
)
```

### Command-Line Tools

```python
#!/usr/bin/env python3
import sys
from scripts.ideagen_skill import NvidiaIdeaGenSkill

def main():
    skill = NvidiaIdeaGenSkill()
    topic = " ".join(sys.argv[1:])
    
    for chunk in skill.generate_ideas_stream(topic, num_ideas=5):
        print(chunk, end="", flush=True)

if __name__ == "__main__":
    main()
```

### Jupyter Notebooks

```python
from scripts.ideagen_skill import NvidiaIdeaGenSkill
from IPython.display import Markdown, display

skill = NvidiaIdeaGenSkill()

topic = input("What would you like ideas about? ")
ideas = ""

for chunk in skill.generate_ideas_stream(topic, num_ideas=3):
    ideas += chunk

display(Markdown(ideas))
```

## Configuration Options

### Initialization Parameters

```python
skill = NvidiaIdeaGenSkill(
    api_key="your_nvidia_api_key",  # Optional if env var set
    ideas_dir="custom/path"          # Optional custom storage path
)
```

### Generation Options

**Quick Ideas:**
- `topic` (str, required): Topic to generate ideas about
- `num_ideas` (int, 1-10): Number of ideas to generate
- `context` (str, optional): Additional context or constraints
- `creativity` (float, 0.0-1.0): Temperature setting

**Brainstorming:**
- `domain` (str, required): Domain/field for brainstorming
- `focus_area` (str, optional): Specific area within domain
- `constraints` (list[str], optional): Requirements or limitations

**Expansion:**
- `idea` (str, required): Idea to expand
- `expansion_type` (str): "detailed", "technical", "creative", or "business"

## Advanced Features

### Custom Prompting

The skill uses carefully crafted system prompts for each mode:

**Quick Ideas Prompt:**
- Emphasizes structured output with clear sections
- Includes actionable next steps
- Provides feature lists and impact analysis

**Brainstorming Prompt:**
- Focuses on practical, implementable concepts
- Considers constraints explicitly
- Provides benefit analysis and implementation notes

**Expansion Prompt:**
- Tailored to expansion type
- Comprehensive coverage of chosen perspective
- Actionable recommendations

### Batch Generation

Generate ideas for multiple topics:
```python
topics = [
    "AI in healthcare",
    "Sustainable packaging",
    "Educational games"
]

for topic in topics:
    ideas = skill.generate_ideas(topic, num_ideas=3)
    skill.save_ideas(topic, ideas)
    print(f"✅ Generated and saved ideas for: {topic}")
```

## Troubleshooting

### Issue: Ideas are too generic
**Solution:** Provide more specific context and constraints

### Issue: API is slow
**Solution:** Normal for streaming; depends on NVIDIA API response time

### Issue: Repetitive ideas
**Solution:** Increase creativity parameter or rephrase topic

### Issue: Ideas don't match topic well
**Solution:** Be more specific in topic description; avoid overly broad topics

## Skill Information

Query skill metadata:
```python
info = skill.get_skill_info()
print(info)
# {
#   "name": "nvidia-ideagen",
#   "version": "1.0.0",
#   "model": "nvidia/llama-3.1-nemotron-nano-8b-v1",
#   "capabilities": [...]
# }
```

## Future Enhancements

Planned features for future versions:
- Multi-model support (OpenAI, Anthropic, local models)
- Idea combination and synthesis
- Template-based generation
- Collaborative brainstorming sessions
- Knowledge base integration
- Export to multiple formats (PDF, DOCX)
- Idea versioning and history
- Integration with project management tools

---

**Note:** This skill requires Python 3.10+ and an NVIDIA API key. Get your free API key at https://build.nvidia.com/

Always provide clear feedback to users, stream output for better UX, and handle errors gracefully for the best experience.

