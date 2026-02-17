# Agent Skills - 5-Step Process Flow Diagram

## 📊 Visual Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER SUBMITS QUERY                           │
│          "Schedule a team meeting tomorrow at 2pm"              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1-2: DISCOVER & LOAD METADATA (Already Done at Startup)  │
├─────────────────────────────────────────────────────────────────┤
│  📂 Scanned: ExpAgentSkill/                                     │
│  ✅ Found: calendar_assistant_skill/SKILL.md                    │
│  ✅ Found: nvidia_ideagen_skill/SKILL.md                        │
│                                                                 │
│  📋 Loaded Metadata:                                            │
│     • calendar-assistant: "A comprehensive calendar..."        │
│     • nvidia-ideagen: "AI-powered idea generation..."          │
│                                                                 │
│  💾 Status: 2 skills ready                                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: MATCH USER TASK TO RELEVANT SKILL                     │
├─────────────────────────────────────────────────────────────────┤
│  🔍 Analyzing Query: "Schedule a team meeting..."               │
│                                                                 │
│  🎯 Keyword Matching:                                           │
│     ├─ calendar-assistant:                                      │
│     │   ✓ "schedule" found                                     │
│     │   ✓ "meeting" found                                      │
│     │   → Score: 2                                             │
│     │                                                           │
│     └─ nvidia-ideagen:                                          │
│         ✗ No matches                                            │
│         → Score: 0                                              │
│                                                                 │
│  ✅ BEST MATCH: calendar-assistant (score: 2)                  │
│     Reasoning: "Matched 2 keywords: schedule, meeting"         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: ACTIVATE SKILL (Progressive Prompt Disclosure)        │
├─────────────────────────────────────────────────────────────────┤
│  ⚡ Loading: calendar-assistant                                 │
│                                                                 │
│  📖 Reading SKILL.md:                                           │
│     • Base content: 3,200 characters                           │
│     • Capabilities: Natural language → ICS                     │
│     • Usage examples: Meetings, appointments, deadlines        │
│                                                                 │
│  🔧 Discovering Tools (Progressive Disclosure):                │
│     • natural_language_to_ics                                  │
│       - Signature: (query: str) -> Tuple[bytes, str, dict]    │
│       - Parameters: query (str, required)                      │
│       - Description: Convert natural language to ICS           │
│     • create_calendar_event                                    │
│       - Signature: (summary, start_datetime, duration, ...)   │
│       - Parameters: 7 parameters with types                    │
│     • parse_calendar_event                                     │
│     • read_reference                                           │
│     → Total: 4 tools with full signatures (+5,300 chars)      │
│                                                                 │
│  📁 Listing Resources:                                          │
│     ✓ references/ directory: 3 files                           │
│     ✓ assets/ directory: 2 files                               │
│                                                                 │
│  📊 Progressive Disclosure Summary:                             │
│     • Base instructions: 3,200 chars                           │
│     • Tool descriptions: +5,300 chars                          │
│     • Resource listings: +300 chars                            │
│     • Total prompt injection: ~8,800 chars (~2,200 tokens)    │
│                                                                 │
│  🎯 Entry Script Located:                                       │
│     • calendar_skill.py (supports --json mode)                │
│                                                                 │
│  ✅ ACTIVATION COMPLETE (Progressive Disclosure)                │
│     Status: Ready for subprocess execution                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: EXECUTE VIA SUBPROCESS (Offloading LLM Context)        │
├─────────────────────────────────────────────────────────────────┤
│  🚀 Subprocess Execution: calendar_skill.py --json              │
│                                                                 │
│  📥 JSON Input (stdin):                                        │
│     {                                                          │
│       "command": "natural_language_to_ics",                    │
│       "parameters": {                                          │
│         "query": "Schedule a team meeting tomorrow at 2pm",    │
│         "api_key": "nvapi-***"                                 │
│       }                                                        │
│     }                                                          │
│                                                                │
│  ⚙️ Processing (Outside LLM Context):                         │
│     subprocess.run([python, calendar_skill.py, --json])       │
│     ├─ 1. Parse natural language with NVIDIA API              │
│     ├─ 2. Extract event details:                              │
│     │      • Summary: "Team Meeting"                          │
│     │      • Date: 2026-01-20                                 │
│     │      • Time: 14:00                                      │
│     │      • Duration: 1 hour                                 │
│     ├─ 3. Generate ICS file format                            │
│     ├─ 4. Add VEVENT components                               │
│     └─ 5. Set reminders (1 hour before)                       │
│                                                                 │
│  📤 JSON Output (stdout):                                       │
│     {                                                           │
│       "success": true,                                         │
│       "ics_content": "BEGIN:VCALENDAR\n...",                  │
│       "parsed_data": {...},                                   │
│       "output_size": 524                                      │
│     }                                                          │
│                                                                 │
│  📊 Execution Details:                                          │
│     • Method: subprocess (Python 3.x)                          │
│     • Working directory: calendar_assistant_skill/             │
│     • Timeout: 30 seconds                                      │
│     • Return code: 0 (success)                                │
│     • LLM tokens used during execution: 0                     │
│     • ✅ Context offloaded - Executed outside LLM              │
│                                                                 │
│  📁 Resources Accessed:                                         │
│     • references/ available (not accessed this run)            │
│     • assets/ available (not accessed this run)                │
│                                                                 │
│  ✅ EXECUTION COMPLETE (Subprocess)                             │
│     Total execution time: 2.3 seconds                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RESPONSE TO USER                             │
├─────────────────────────────────────────────────────────────────┤
│  🔄 Agent Skills Process                                        │
│                                                                 │
│  ✅ Steps 1-2: Discover & Load Metadata                        │
│     Found 2 skills: calendar-assistant, nvidia-ideagen         │
│                                                                 │
│  ✅ Step 3: Match Complete                                     │
│     Selected: calendar-assistant (Matched 2 keywords)          │
│                                                                 │
│  ✅ Step 4: Activation Complete                                │
│     - Base instructions: 3,200 chars                           │
│     - Progressive disclosure: +5,600 chars                     │
│     - Tools discovered: 4                                      │
│     - Entry script: calendar_skill.py                          │
│     - Total prompt tokens injected: ~2,200                     │
│                                                                 │
│  ✅ Step 5: Execution Complete (Subprocess)                    │
│     - Offloading execution from LLM context                    │
│     - Running calendar-assistant via subprocess                │
│     - Using Python subprocess instead of tool calling          │
│                                                                 │
│  ───────────────────────────────────────                       │
│                                                                 │
│  📤 Skill Output:                                               │
│                                                                 │
│  ✅ Calendar Event Created via Subprocess!                     │
│                                                                 │
│  📅 Event Details:                                             │
│  • Title: Team Meeting                                         │
│  • Date: 2026-01-20                                            │
│  • Time: 14:00                                                 │
│  • Duration: 1 hour                                            │
│  • Location: Not specified                                     │
│  • Description: Not specified                                  │
│  • Reminder: 1 hour before                                     │
│                                                                 │
│  📥 Download the .ics file using the button on the right →     │
│                                                                 │
│  ℹ️ Execution Info:                                            │
│     - Method: subprocess                                       │
│     - Tool: natural_language_to_ics                            │
│     - Output size: 524 bytes                                   │
│     - ✅ Context offloaded - Executed outside LLM              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Step-by-Step Breakdown

### **STEP 1-2: Discover & Load** (Startup Only)
```
When:     At application startup
Duration: ~500ms
Output:   Dictionary of available skills with metadata
Status:   Shown as "✅ already completed" in UI
```

**What Happens:**
1. Scan `ExpAgentSkill/` directory
2. Find all folders with `SKILL.md` files
3. Parse YAML frontmatter for name and description
4. Load `config.yaml` for each skill
5. Store in `SkillLoader.skills` dictionary

**Displayed:**
```
✅ Steps 1-2: Discover & Load Metadata
   Found 2 skills: calendar-assistant, nvidia-ideagen
```

---

### **STEP 3: Match** (Per Query)
```
When:     For each user query
Duration: ~50ms
Output:   Best matching skill name + reasoning
Status:   Shown as "⏳" then "✅"
```

**What Happens:**
1. Convert query to lowercase
2. Check query against keyword triggers for each skill
3. Count keyword matches and score each skill
4. Return skill with highest score

**Displayed:**
```
⏳ Step 3: Matching Task to Skill - Analyzing query...
✅ Step 3: Match Complete
   Selected skill: `calendar-assistant`
   (Matched 2 keyword(s): schedule, meeting)
```

---

### **STEP 4: Activate with Progressive Disclosure** (Per Query)
```
When:     After successful match
Duration: ~150ms
Output:   Progressive prompt with full tool descriptions
Status:   Shown as "⏳" then "✅"
```

**What Happens:**
1. Retrieve skill from SkillLoader
2. Load full `SKILL.md` content (not just frontmatter)
3. Discover @skill_tool decorated functions **with signatures**
4. Generate detailed parameter descriptions for each tool
5. List available resources (references/, assets/)
6. Locate entry script for subprocess execution
7. Build progressive prompt (base + tools + resources)

**Displayed:**
```
⏳ Step 4: Activating Skill - Loading `calendar-assistant` with progressive disclosure...
✅ Step 4: Activation Complete
   - Base instructions: 3,200 chars
   - Progressive disclosure: +5,600 chars
   - Tools discovered: 4
   - Entry script: calendar_skill.py
   - Total prompt tokens injected: ~2,200 (offloading LLM context)
```

**Progressive Disclosure Details:**
- Base SKILL.md: ~3,200 chars (~800 tokens)
- Tool signatures: ~2,000 chars (~500 tokens)
- Parameter descriptions: ~3,000 chars (~750 tokens)
- Resource listings: ~600 chars (~150 tokens)
- **Total: ~8,800 chars (~2,200 tokens)**

---

### **STEP 5: Execute via Subprocess** (Per Query)
```
When:     After successful activation
Duration: ~1-5 seconds (depends on skill)
Output:   Skill execution results (text, files, etc.)
Status:   Shown as "⏳" then "✅"
Method:   Python subprocess with JSON I/O
```

**What Happens:**
1. Prepare JSON input with command and parameters
2. Locate entry script (e.g., `calendar_skill.py`)
3. Execute via `subprocess.run()`:
   - Command: `python calendar_skill.py --json`
   - Input: JSON via stdin
   - Output: JSON via stdout
   - Working dir: skill directory
   - Timeout: 30 seconds
4. Parse JSON output
5. Extract results and display to user

**Subprocess Communication:**
```python
# Input (stdin)
{
  "command": "natural_language_to_ics",
  "parameters": {
    "query": "Meeting tomorrow at 2pm",
    "api_key": "nvapi-xxx"
  }
}

# Output (stdout)
{
  "success": true,
  "ics_content": "BEGIN:VCALENDAR...",
  "parsed_data": {...},
  "output_size": 524
}
```

**Displayed:**
```
⏳ Step 5: Executing Skill via Subprocess
   - Offloading execution from LLM context
   - Running calendar-assistant scripts directly
   - Using Python subprocess instead of tool calling

───

📤 Skill Output:

✅ Calendar Event Created via Subprocess!
...

ℹ️ Execution Info:
- Method: subprocess
- Tool: natural_language_to_ics
- Output size: 524 bytes
- ✅ Context offloaded - Executed outside LLM
```

**Key Difference from LangChain:**
- **Before**: LLM → Tool call → LangChain StructuredTool.invoke() → Return to LLM
- **After**: Match → subprocess.run() → JSON output → Display (no LLM involvement in execution)

---

## 🔄 Alternative Flow: No Skill Match

```
STEP 3: MATCH
    ↓
    ✗ No keywords matched any skill
    ↓
⊘ Step 3: No Skill Match
   "No skill matched, using general AI response"
    ↓
Skip to General LLM Response
    ↓
Use NVIDIA Nemotron for general Q&A
```

---

## ⚠️ Error Handling Flow

```
Any Step Fails
    ↓
❌ Step X: Failed
   Error: [specific error message]
    ↓
Return error to user
    ↓
Suggest retry or provide debugging info
```

---

## 📊 Performance Metrics

| Step | Average Duration | Method | Tokens Used | UI Indicator |
|------|-----------------|--------|-------------|--------------|
| 1-2 (Startup) | 500ms | File scanning | ~100/skill | ✅ (pre-completed) |
| 3 (Match) | 50ms | Keyword matching | 0 | ⏳ → ✅ |
| 4 (Activate) | 150ms | Progressive disclosure | ~2,200 | ⏳ → ✅ |
| 5 (Execute) | 1-5s | **Subprocess** | **0** | ⏳ → ✅ |
| **Total** | **1.2-5.2s** | End-to-end | **~2,300** | Complete flow |

**Token Usage Comparison:**

| Approach | Step 4 | Step 5 | Total | Notes |
|----------|--------|--------|-------|-------|
| **LangChain StructuredTool** | ~800 | ~1,500 | ~2,300 | Tokens used during execution |
| **Subprocess Execution** | ~2,200 | **0** | ~2,200 | **Execution offloaded** |

**Key Insight**: Subprocess execution uses similar total tokens BUT:
- More tokens upfront (Step 4) for complete understanding
- Zero tokens during execution (Step 5) - offloaded to subprocess
- Better context management and cleaner separation

---

## 🎨 Visual Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Completed successfully |
| ⏳ | In progress |
| ⊘ | Skipped (e.g., no match) |
| ❌ | Failed with error |
| 🔍 | Searching/analyzing |
| ⚡ | Loading/activating |
| 🚀 | Executing |
| 📤 | Output generated |

---

## 🔗 References

- **Agent Skills Specification**: https://agentskills.io/integrate-skills#overview
- **Implementation**: `gradio_agent_chatbot.py`
- **SkillLoader**: `skill_loader.py`
- **Test Suite**: `test_skill.py`

---

## 🔄 Subprocess Execution Architecture

### Why Subprocess Instead of LangChain StructuredTool?

**Traditional Approach (LangChain):**
```
User Query
   ↓
Step 3: Match skill
   ↓
Step 4: Load basic SKILL.md (~800 tokens)
   ↓
Step 5: LLM decides to call tool
   ↓
LangChain StructuredTool.invoke()
   ↓
Python function executes (within LLM context)
   ↓
Result returns to LLM (~1,500 tokens consumed)
   ↓
LLM formats response
   ↓
Display to user
```

**Subprocess Approach (Current):**
```
User Query
   ↓
Step 3: Match skill
   ↓
Step 4: Progressive disclosure (~2,200 tokens)
   ├─ Full SKILL.md
   ├─ All tool signatures
   ├─ Parameter descriptions
   └─ Resource listings
   ↓
Step 5: subprocess.run() (0 tokens)
   ├─ JSON input via stdin
   ├─ Execute skill script
   ├─ JSON output via stdout
   └─ Parse and display
   ↓
Display to user
```

### Benefits of Subprocess Execution

1. **Context Offloading**: Skills execute outside LLM's context window
2. **Progressive Disclosure**: More information upfront for better understanding
3. **Clean Separation**: LLM for reasoning, subprocess for execution
4. **Scalability**: Multiple skills can run in parallel
5. **Debugging**: Clear JSON I/O boundaries
6. **Security**: Process isolation and sandboxing

### Implementation Files

- `skill_loader.py`: Added `execute_skill_subprocess()` and `generate_progressive_prompt()`
- `gradio_agent_chatbot.py`: Updated Steps 4 & 5 for subprocess execution
- `calendar_skill.py`: Added `--json` CLI mode for subprocess
- `ideagen_skill.py`: Added `--json` CLI mode for subprocess
- `SUBPROCESS_EXECUTION.md`: Complete documentation of changes

---

**Created**: January 19, 2026  
**Updated**: February 2, 2026 (Subprocess Execution)  
**Status**: ✅ Implementation Complete (Subprocess)



