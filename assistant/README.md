# Setup Assistant

Interactive ADK-based agent that guides you through setting up agent evaluation infrastructure.

## Quick Start

### Step 1: Clone SDK Repository (Separate from Your Agent)

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

```bash
cd assistant/agent
pip install -r requirements.txt
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
export GOOGLE_CLOUD_REGION="us-central1"
python assistant_agent.py
```

### Step 3: Follow the Interactive Setup

The assistant will ask for your agent project path (e.g., `~/repos/my-agent-project`) and copy the necessary files there.

## What It Does

The assistant **conversationally** guides you through:

1. ✅ Getting your agent project path
2. ✅ Checking agent compatibility (`generate_content()` or `run_async()`)
3. ✅ Configuring observability (logging, tracing, metrics)
4. ✅ Setting up dataset collection
5. ✅ Generating `eval_config.yaml` in your project
6. ✅ Copying terraform to your project
7. ✅ Showing SDK integration code with your values

## Architecture

Built with Google ADK (Agent Development Kit):
- **Model**: Gemini 2.5 Flash
- **Tools**: File operations, config validation, infrastructure checks
- **Conversational**: Adapts to your responses, not a rigid script

## Example Interaction

```
🤖 Assistant: Hi! I'll help you set up agent evaluation. Ready to start?
You: Yes
🤖 Assistant: What's the path to your agent project?
You: ~/my-agent
🤖 Assistant: What's your agent file path (with generate_content method)?
You: ~/my-agent/agent.py
🤖 Assistant: ✓ Agent compatible! Configure observability: all/logging/tracing?
You: all
🤖 Assistant: Enable dataset collection?
You: no
🤖 Assistant: What's your GCP project ID?
You: my-project-123
🤖 Assistant: ✓ Created eval_config.yaml
              ✓ Copied terraform
              
              Integrate SDK:
              wrapper = enable_evaluation(agent, "my-project-123", "my-agent", "eval_config.yaml")
              
              Deploy: cd terraform && terraform apply
```

## Files

```
assistant/agent/
├── assistant_agent.py          # Main ADK agent
├── system_instruction.prompt   # Conversation flow & personality
├── requirements.txt            # Dependencies
└── tools/
    ├── config_operations.py    # Generate configs
    ├── file_operations.py      # Copy files, check compatibility
    ├── config_validator.py     # Validate YAML
    └── infra_checker.py        # Check GCP resources
```

## Tools Available

| Tool | Purpose |
|------|---------|
| `check_agent_compatibility_tool` | Verify agent has required methods |
| `copy_config_template_tool` | Generate customized eval_config.yaml |
| `copy_terraform_module_tool` | Copy terraform to agent project |
| `validate_config_tool` | Check YAML syntax |
| `check_infrastructure_tool` | Verify GCP resources exist |

## Customization

Modify the assistant by editing:
- `system_instruction.prompt` - Conversation flow and personality
- `tools/*.py` - Add new capabilities
- `assistant_agent.py` - Change model or configuration

## FAQ

**Q: Why run locally instead of deploying?**  
A: Needs local file access to check your agent and copy configs.

**Q: Can I skip the assistant?**  
A: Yes, manually create configs and copy terraform (see main [README.md](../README.md)).

**Q: Use for multiple projects?**  
A: Yes, run once per project. Generates separate configs for each.

---

See [main README](../README.md) for complete documentation.
