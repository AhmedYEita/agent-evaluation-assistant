# Agent Evaluation Setup Assistant

An **ADK-based conversational agent** that helps users set up agent evaluation infrastructure.

## Quick Start

### Step 1: Clone the SDK Repository Inside Your Agent Project

Clone this repo **outside** your agent project directory:

```bash
# Clone in a separate location (e.g., ~/repos, ~/projects)
cd ~/repos
git clone https://github.com/AhmedYEita/agent-evaluation-assistant
cd agent-evaluation-assistant
pip install -e ./sdk
```

**Important:** Keep the SDK repo **separate** from your agent project:
```
~/repos/
├── agent-evaluation-assistant/     # ← SDK repo (clone here)
└── my-agent-project/           # ← Your agent (existing project)
```

### Step 2: Run the Assistant

**Direct:**
```bash
cd assistant/agent
pip install -r requirements.txt
export GOOGLE_CLOUD_PROJECT="YOUR GCP PROJECT"
export GOOGLE_CLOUD_REGION="us-central1"
python assistant_agent.py
```

**Via CLI:**
```bash
agent-eval-assistant setup
# (Directs you to run the assistant agent)
```

### Step 3: Follow the Interactive Setup

The assistant will ask for your agent project path (e.g., `~/repos/my-agent-project`) and copy the necessary files there.

---

## What the Assistant Does

The assistant **conversationally guides** you through:

1. ✅ Getting your agent project path
2. ✅ Verifying agent compatibility (checks for `generate_content()` method)
3. ✅ Configuring observability services (logging, tracing, metrics)
4. ✅ Setting up dataset collection
5. ✅ Generating customized `eval_config.yaml` in your project
6. ✅ Copying terraform module to your project
7. ✅ Showing integration code with your specific values

---

## Architecture

### **ADK-Based Agent**

```
User ←→ Assistant Agent (Google ADK) ←→ Tools
         ↑
         System Instructions
```

**Built with:**
- Google ADK (Agent Development Kit)
- Gemini 2.0 Flash model
- System instructions for personality and workflow
- Python tools for file operations

**Not a script!** The assistant adapts to your responses and asks intelligent follow-up questions.

See [ADK_ARCHITECTURE.md](./ADK_ARCHITECTURE.md) for detailed explanation.

---

## Files Structure

```
assistant/
├── agent/
│   ├── assistant_agent.py        # ADK agent (140 lines)
│   ├── requirements.txt           # google-adk, pyyaml, bigquery
│   └── tools/
│       ├── file_operations.py    # Copy files, check repo/agent
│       ├── config_validator.py   # Validate YAML
│       └── infra_checker.py      # Check BigQuery/GCP
│
├── ADK_ARCHITECTURE.md           # Detailed architecture explanation
└── README.md                     # This file
```

---

## Example Conversation

```
🤖 Assistant: Hi! 👋 I'm here to help you set up agent evaluation infrastructure.
              This will take about 5-7 minutes. Ready to get started?

You: Yes

🤖 Assistant: Great! What's the path to your agent project where you
              want to set up evaluation? (e.g., ~/my-agent-project)

You: ~/my-chatbot

🤖 Assistant: Got it! Can you provide the path to your agent file that has the
              generate_content() method? (e.g., ~/my-chatbot/agent.py)

You: ~/my-chatbot/chatbot_agent.py

🤖 Assistant: Let me check if your agent is compatible...
              ✓ Agent looks good! Found generate_content() method.
              
              Now, let's configure observability services. I'll explain each one:
              
              📊 **Logging**: Captures all agent interactions and errors
              📈 **Tracing**: Tracks request flow and latency
              📉 **Metrics**: Monitors performance over time
              
              Which services would you like to enable? (all/logging/tracing/metrics)

You: all

🤖 Assistant: Excellent choice! ✓ Enabling all observability services.
              
              💡 One more thing: **Dataset Collection**
              
              This automatically saves agent interactions to BigQuery for evaluation.
              I recommend keeping it OFF by default (you can enable it later for
              specific test runs).
              
              Enable dataset collection? (yes/no)

You: no

🤖 Assistant: ✓ Smart! Dataset collection will be disabled by default.
              
              What's your GCP Project ID?

You: my-gcp-project

🤖 Assistant: And what would you like to name your agent? (e.g., chatbot-agent)

You: my-chatbot

🤖 Assistant: Perfect! Let me generate your configuration...
              
              ✓ Created eval_config.yaml in ~/my-chatbot/
              ✓ Copied terraform module to ~/my-chatbot/terraform/
              
              📝 **Next Steps:**
              
              1. **Integrate the SDK into your agent:**
              
              ```python
              from agent_evaluation_sdk import enable_evaluation
              
              # Wrap your agent
              wrapped_agent = enable_evaluation(
                  your_agent,
                  "eval_config.yaml"
              )
              
              # Use it
              response = wrapped_agent.generate_content("Hello!")
              ```
              
              2. **Deploy infrastructure:**
              
              ```bash
              cd ~/my-chatbot/terraform
              terraform init
              terraform apply
              ```
              
              3. **Test it:**
              
              ```bash
              python your_agent.py
              ```
              
              Check Cloud Logging and BigQuery for your data! 🎉
              
              Need help with anything else?

You: No, thanks!

🤖 Assistant: You're all set! 🚀 Happy building!
```

---

## CLI Validation

Quick check if your setup is correct:

```bash
agent-eval-assistant validate --project ~/my-chatbot
```

Output:

```
🔍 Setup Validation
============================================================
Checking: /Users/you/my-chatbot

✓ eval_config.yaml found
✓ Valid YAML syntax
✓ Terraform module found

✓ Everything looks good! 🎉
```

---

## Key Features

### 🧠 Conversational Intelligence

- Adapts to user responses
- Explains WHY things matter
- Provides trade-offs and recommendations
- Friendly, not robotic

### 🔧 Automated Setup

- Validates agent compatibility
- Generates customized configs
- Copies necessary files
- Shows integration code with real values

### ✅ Smart Defaults

- Observability services: All enabled
- Dataset collection: Disabled by default
- Region: us-central1
- Model: gemini-2.0-flash

### 🛡️ Error Handling

- Validates agent file structure
- Verifies YAML syntax
- Provides helpful error messages

---

## Tools Used by the Agent

The ADK agent uses these Python functions as tools:

| Tool | Purpose |
|------|---------|
| `check_agent_compatibility_tool` | Check for `generate_content()` |
| `validate_config_tool` | Validate YAML syntax |
| `check_infrastructure_tool` | Check GCP resources exist |
| `copy_config_template_tool` | Generate `eval_config.yaml` |
| `copy_terraform_module_tool` | Copy terraform files |

See [agent/tools/](./agent/tools/) for implementation details.

---

## Customization

You can modify the assistant's behavior by editing:

- **System Instruction** in `assistant_agent.py` - Change personality, workflow
- **Tools** in `agent/tools/` - Add new capabilities
- **Model** in `assistant_agent.py` - Use different Gemini version

---

## FAQ

### Q: Why run locally instead of deploying?

**A:** The assistant needs to access your local files to check your agent, copy configs, and set up terraform. Running locally ensures full functionality.

### Q: Can I use this for multiple projects?

**A:** Yes! Run the assistant once for each project. It will generate separate configs and terraform for each.

### Q: What if I don't use terraform?

**A:** The assistant still generates the terraform module for reference. You can deploy GCP resources manually using the module as a guide.

### Q: Can I skip certain steps?

**A:** Yes! The assistant is conversational. Just let it know what you want to skip.

---

## Next Steps

1. **Run the assistant** to set up your first agent
2. **Deploy infrastructure** with terraform
3. **Test your agent** and check Cloud Console
4. **Run evaluation** with `run_evaluation.py`

See the main [README.md](../README.md) for full documentation.
