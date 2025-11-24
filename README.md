# Agent Evaluation Assistant

**Production-ready evaluation infrastructure for AI agents with automated monitoring, testing, and quality evaluation.**

## Overview

A lightweight Python SDK and Terraform infrastructure that enables comprehensive evaluation for Google ADK agents with minimal code changes. Get structured logging, performance tracing, metrics dashboards, dataset collection, and quality testing by adding just one line of code to your agent.

### Key Features

- **One-Line Integration**: Enable full evaluation with a single function call
- **Setup Assistant**: Interactive CLI tool to guide you through setup
- **Zero-Latency Observability**: All Cloud API calls run in background threads
- **Automated Data Collection**: Logs, traces, metrics, and datasets captured automatically
- **Production-Ready**: Built on GCP services (Cloud Logging, Trace, Monitoring, BigQuery)
- **Quality Evaluation**: Vertex AI Gen AI Evaluation Service for automated and model-based metrics
- **Infrastructure as Code**: Reproducible Terraform deployment
- **Flexible Configuration**: Enable/disable services and tune performance per environment

## 🚀 Quick Start

### 1. Clone & Install SDK (Separate from Your Agent)

Clone this repo **outside** your agent project:

```bash
# Clone in a separate location (e.g., ~/repos, ~/projects)
cd ~/repos
git clone https://github.com/yourorg/agent-evaluation-assistant
cd agent-evaluation-assistant
pip install -e ./sdk
```

**Directory structure:**
```
~/repos/
├── agent-evaluation-assistant/     # ← SDK repo (clone here)
└── my-agent-project/           # ← Your agent (existing project)
```

### 2. Run Setup Assistant

```bash
cd agent-evaluation-assistant/assistant/agent
python assistant_agent.py
```

The assistant will guide you through:
- ✅ Getting your agent project path
- ✅ Verifying agent compatibility
- ✅ Generating configuration files **in your project**
- ✅ Setting up Terraform infrastructure **in your project**
- ✅ Showing integration code

**Or manually configure** by creating these files in your project:

**Agent Config** (`agent_config.yaml`):
```yaml
project_id: "GCP_PROJECT_ID"
agent_name: "my-agent"
  model: "gemini-2.5-flash"
```

**SDK Config** (`eval_config.yaml`):
```yaml
logging:
  enabled: true
tracing:
  enabled: true
dataset:
  auto_collect: false  # Set to true to collect data, then back to false
```

### 3. Enable Evaluation (1 line!)
```python
from agent_evaluation_sdk import enable_evaluation

agent = YourAgent(...)
wrapper = enable_evaluation(agent, "PROJECT_ID", "agent-name", "eval_config.yaml")
```

## ✨ What You Get

### Real-time Monitoring (Automatic)
After `enable_evaluation()`, every agent interaction automatically gets:

✅ **Structured Logging** - Every interaction logged to Cloud Logging  
✅ **Performance Tracing** - Nested spans show LLM call, processing, and logging time  
✅ **Real-time Metrics** - Pre-built dashboard in Cloud Monitoring  
✅ **Error Tracking** - Automatic error capture in traces and logs  
✅ **Dataset Collection** - Optional auto-capture to BigQuery

### Quality Testing (Manual)
Run `python run_evaluation.py` to test your agent:

🧪 **Regression Testing** - Test against historical dataset  
📊 **Quality Metrics** - BLEU, ROUGE, coherence, fluency, safety  
📈 **Performance Tracking** - Compare test runs over time  

## 🔧 Technical Stack

- **Agent Framework**: Google ADK (Agent Development Kit)
- **Deployment Target**: Agent Engine (ready for deployment)
- **Infrastructure**: Terraform for GCP services
- **Monitoring**: Cloud Logging, Trace, Monitoring
- **Dataset Storage**: BigQuery for datasets
- **Evaluation**: Vertex AI Gen AI Evaluation Service
- **CI/CD**: GitHub Actions for validation

## 🧪 Agent Testing & Evaluation

```bash
# 1. Enable dataset collection in eval_config.yaml
# 2. Run agent - interactions auto-collect to BigQuery
python custom_agent.py --test

# 3. Review in BigQuery - update 'reference' field, set 'reviewed = TRUE'
# 4. Run evaluation test
python run_evaluation.py
```

**Workflow:**
1. **Collect** - Set `auto_collect: true`, run agent with `--test`, then set back to `false`
2. **Review** - Update ground truth in BigQuery (`{agent_name}_eval_dataset` table)
3. **Evaluate** - Run evaluation script (appends to `{agent_name}_eval_run` and `{agent_name}_eval_metrics` tables)

**Available Metrics:**
- **Automated**: BLEU, ROUGE
- **Model-based**: Coherence, Fluency, Safety, Groundedness, Fulfillment, Instruction Following, Verbosity

See [SETUP.md](./SETUP.md#agent-testing--evaluation) for details.


## 📁 Repository Structure

```
├── README.md                    # This file
├── SETUP.md                     # Complete setup and deployment guide
├── CONTRIBUTING.md              # Contributing guidelines
├── sdk/                         # Python SDK
│   ├── agent_evaluation_sdk/    # Core SDK code
│   └── tests/                   # Unit & integration tests
├── assistant/                   # Setup Assistant (NEW!)
│   └── agent/                   # ADK assistant agent (run locally)
├── terraform/                   # Infrastructure as Code
│   └── modules/                 # GCP services modules
├── example_agents/              # Working examples
│   ├── custom_agent.py          # Custom agent example
│   ├── adk_agent.py             # ADK agent example
│   ├── agent_config.yaml        # Agent-specific config
│   └── eval_config.yaml         # SDK config
└── .github/workflows/           # CI/CD pipelines
```

## 📚 Documentation

- **[SETUP.md](./SETUP.md)** - Complete setup and deployment guide
- **[CONTRIBUTING.md](./CONTRIBUTING.md)** - Development and contribution guidelines
- **[assistant/](./assistant/)** - Setup Assistant documentation
- **[example_agents/](./example_agents/)** - Working code samples

## 🛠️ CLI Commands

```bash
# Interactive setup
agent-eval-assistant setup

# Validate existing setup
agent-eval-assistant validate --project /path/to/project
```

## 📄 License

MIT License
