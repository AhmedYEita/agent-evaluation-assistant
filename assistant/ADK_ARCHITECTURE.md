# ADK-Based Assistant Architecture

## The Correct Architecture

### **What It Is Now (Correct)**

```
User ←→ Assistant Agent (Google ADK) ←→ Tools
         ↑
         System Instructions
         (Conversational, intelligent)
```

**Assistant Agent (Google ADK-based):**
- Uses **Google ADK** (Agent Development Kit) framework
- Has system instructions (personality, workflow)
- Calls tools when needed
- Conversational and context-aware
- Makes intelligent decisions

**Tools:**
- `check_repo_exists_tool` - Check if repo is cloned
- `check_agent_compatibility_tool` - Verify agent has generate_content()
- `copy_config_template_tool` - Create customized eval_config.yaml
- `copy_terraform_module_tool` - Copy infrastructure files
- `validate_config_tool` - Check YAML structure
- `check_infrastructure_tool` - Verify GCP resources

**CLI:**
- Thin client
- Just connects user to assistant
- No logic here!

---

## Why This Is Better

### **Before (Wrong Approach)**

```python
# cli.py had ALL the logic (500 lines):
def setup_command():
    print("Step 1...")
    check_repo()
    print("Step 2...")
    check_compatibility()
    # ... 400 more lines
```

❌ **Problems:**
- Rigid, scripted flow
- No intelligence
- Can't adapt to user
- All logic in CLI

### **After (Correct Approach)**

```python
# assistant_agent.py (Google ADK):
from google.adk import Agent

SYSTEM_INSTRUCTION = """
You are a friendly Setup Assistant.
Help users set up evaluation infrastructure.

Workflow:
1. Check if repo is cloned
2. Verify agent compatibility
3. Configure observability
4. Generate configs
5. Show next steps

Be conversational and adaptive!
"""

# Create ADK agent
agent = Agent(
    model="gemini-2.0-flash",
    system_instruction=SYSTEM_INSTRUCTION,
    tools=tools,
)

# CLI is simple:
def setup_command():
    print("Connecting to assistant...")
    # Assistant handles everything
```

✅ **Benefits:**
- Conversational, not scripted
- Intelligent (ADK model makes decisions)
- Adaptive (responds to user's situation)
- Logic in assistant, not CLI

---

## How the ADK Assistant Works

### **1. System Instruction**

Defines the assistant's personality and workflow:

```python
SYSTEM_INSTRUCTION = """
You are a friendly and helpful Setup Assistant.

Your role:
- Guide users through setup (conversational style)
- Check prerequisites first
- Explain WHY things matter
- Customize based on user preferences
- Give clear next steps

Personality:
- Friendly (use emojis ✓ ⚠️ 💡)
- Explain trade-offs
- Encourage users
- Give examples

Workflow:
1. Greet and explain process
2. Check repo status → use check_repo_exists tool
3. Get project location
4. Check agent compatibility → use check_agent_compatibility tool
5. Get GCP info
6. Ask about observability (explain each service)
7. Ask about dataset collection
8. Generate configs → use copy_config_template tool
9. Copy terraform → use copy_terraform_module tool
10. Show integration code
11. Give next steps

Be adaptive, not robotic!
"""
```

This is the "brain" - tells the assistant:
- What its job is
- How to talk to users
- When to use tools
- What workflow to follow

### **2. Tools**

Functions the assistant can call:

```python
# Tool: Check if repo exists
def check_repo_exists_tool(repo_path: str = None) -> dict:
    # Search for repository
    # Return: exists, path, message

# Tool: Check agent compatibility
def check_agent_compatibility_tool(agent_file_path: str) -> dict:
    # Read agent file
    # Look for generate_content()
    # Return: compatible, is_async, message

# Tool: Copy config template
def copy_config_template_tool(
    repo_path, dest_path,
    enable_logging, enable_tracing, enable_metrics, auto_collect
) -> dict:
    # Read template
    # Customize based on preferences
    # Write to dest_path
    # Return: success, config_path, message
```

The assistant decides WHEN to call tools based on conversation context.

### **3. Conversation Flow**

**User:** "I want to set up evaluation"

**Assistant (uses system instruction):**
"Great! Let's get you set up. This will take about 5-7 minutes. First, have you cloned the repository?"

**User:** "No"

**Assistant:** 
"No problem! Here's how to clone it:..."
*Provides instructions without calling tools*

**User:** "Done, I cloned it"

**Assistant (calls check_repo_exists tool):**
"Let me verify... ✓ Found repository at /path/to/repo. Perfect!"

**Assistant:**
"Where would you like to set up your project?"

**User:** "~/my-agent"

**Assistant:**
"Got it. Do you have an agent file I can check for compatibility?"

**User:** "Yes, my_agent.py"

**Assistant (calls check_agent_compatibility tool):**
"Checking... ✓ Great! Your agent has generate_content(). It's compatible!"

**Assistant:**
"Now, let's configure observability. The SDK provides:
- Logging (track interactions)
- Tracing (monitor performance)  
- Metrics (real-time dashboards)

Would you like all enabled?"

**User:** "Just logging and tracing"

**Assistant:**
"Perfect choice! And about dataset collection - this stores interactions in BigQuery for testing. I recommend keeping it OFF for now. Sound good?"

**User:** "Yes"

**Assistant (calls copy_config_template tool):**
"Generating your customized config... ✓ Created eval_config.yaml with Logging and Tracing enabled!"

**Assistant (calls copy_terraform_module tool):**
"Copying terraform module... ✓ Done! Created terraform/main.tf with your project: my-project-123"

**Assistant:**
"All set! 🎉 Here's how to integrate..."

---

## Why ADK?

### **ADK Gives Us:**

1. **Natural Conversation**
   - Not scripted "Step 1, Step 2"
   - Responds naturally to user
   - Can handle questions mid-flow

2. **Context Awareness**
   - Remembers what user said
   - Makes smart decisions
   - Adapts workflow

3. **Tool Use**
   - Decides WHEN to call tools
   - Not hardcoded "call this now"
   - Based on conversation context

4. **Personality**
   - System instruction defines tone
   - Consistent behavior
   - Friendly and helpful

5. **Flexibility**
   - User can ask questions anytime
   - Flow adapts to user's needs
   - Not rigid script

---

## Comparison: Script vs ADK

### **Scripted (Old):**
```python
print("Step 1: Check repo")
if not check_repo():
    print("Clone it first")
    exit()

print("Step 2: Get project location")
project = input("Project path: ")

print("Step 3: Check compatibility")
# ... rigid, can't deviate
```

User must follow exact order, no flexibility.

### **ADK (New):**
```python
# System instruction guides the conversation
# Assistant can:
- Answer questions anytime
- Skip steps if not needed
- Explain more if user is confused
- Adapt to user's experience level
```

Conversational, adaptive, intelligent!

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│  User                                           │
│  "I want to set up evaluation"                 │
└──────────────────┬──────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────┐
│  ADK Assistant Agent                            │
│  ┌───────────────────────────────────────────┐ │
│  │ System Instruction                        │ │
│  │ - Personality                             │ │
│  │ - Workflow guidance                       │ │
│  │ - When to use tools                       │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │ Gemini Model                              │ │
│  │ - Natural language understanding          │ │
│  │ - Context awareness                       │ │
│  │ - Decision making                         │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  Decides to call tools ↓                       │
└─────────────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────┐
│  Tools (Python Functions)                       │
│  - check_repo_exists()                          │
│  - check_agent_compatibility()                  │
│  - copy_config_template()                       │
│  - copy_terraform_module()                      │
│  - validate_config()                            │
│  - check_infrastructure()                       │
└─────────────────────────────────────────────────┘
```

---

## Why Most Logic Was in CLI (Wrong)

**I made a mistake initially:**

Thought: "CLI should have all the logic"
Result: 500 lines of scripted workflow in CLI

**The problem:**
- Rigid: Can't adapt to user
- No intelligence: Just follows script
- Not conversational: Just prints steps
- Hard to modify: Logic scattered in CLI

**The correct way:**
- CLI is thin: Just connects to assistant
- Assistant has logic: System instruction + tools
- Conversational: ADK handles conversation
- Flexible: Can adapt to any user situation

---

## Summary

**Correct Architecture:**
- ✅ Assistant is ADK-based (conversational agent)
- ✅ System instruction defines personality and workflow
- ✅ Tools handle operations (file copying, checking)
- ✅ CLI is thin client (just connects user to assistant)
- ✅ Logic in assistant, not CLI

**Benefits:**
- 🗣️ Natural conversation
- 🧠 Intelligent decisions
- 🔄 Adaptive workflow
- 💡 Context-aware
- 🎯 Tool use when needed

The assistant is now a true **conversational AI agent**, not a scripted command-line tool!

