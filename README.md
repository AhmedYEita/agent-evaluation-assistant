# Agent Evaluation Assistant

**Production-ready evaluation infrastructure for AI agents with one-line integration.**

## Overview

A Python SDK and Terraform infrastructure for comprehensive agent evaluation with minimal code changes. Get structured logging, performance tracing, metrics dashboards, dataset collection, and quality testing by adding a single line of code.

### Key Features

- **One-Line Integration**: `enable_evaluation(agent, project_id, agent_name, config)`
- **Setup Assistant**: Interactive ADK agent guides you through setup
- **Zero-Latency**: All Cloud API calls run in background threads
- **Automated Observability**: Logs, traces, metrics, and datasets captured automatically
- **Production-Ready**: Built on GCP services (Cloud Logging, Trace, Monitoring, BigQuery)
- **Quality Evaluation**: Vertex AI Gen AI Evaluation Service for automated and model-based metrics
- **Infrastructure as Code**: Reproducible Terraform deployment
- **Flexible Configuration**: Enable/disable services and tune performance
## 🚀 Quick Start

### 1. Clone & Install SDK (Separate from Your Agent)

Clone this repo **outside** your agent project directory:

```bash
cd ~/repos  # or wherever you keep repositories
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

### 2. Run Setup Assistant (Recommended)

```bash
cd assistant/agent
pip install -r requirements.txt

# Set your GCP project (required for the assistant)
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
export GOOGLE_CLOUD_REGION="us-central1"

python assistant_agent.py
```

The assistant will guide you through:
- ✅ Getting your agent project path
- ✅ Verifying agent compatibility
- ✅ Generating configuration files **in your project**
- ✅ Setting up Terraform infrastructure **in your project**
- ✅ Showing integration code

### 3. Enable Evaluation

```python
from agent_evaluation_sdk import enable_evaluation

agent = YourAgent(...)
wrapper = enable_evaluation(agent, "your-gcp-project-id", "agent-name", "eval_config.yaml")
```

That's it! Your agent now has full observability.

## What You Get

### Automatic Monitoring
- ✅ **Cloud Logging** - Every interaction logged with interaction_id, input, output, duration
- ✅ **Cloud Trace** - Nested spans show LLM calls, processing time, tool usage
- ✅ **Cloud Monitoring** - Pre-built dashboard with latency, errors, token usage
- ✅ **Dataset Collection** - Optional auto-capture to BigQuery for testing

### Quality Testing
- 🧪 **Regression Testing** - Test against historical dataset
- 📊 **Automated Metrics** - BLEU, ROUGE scores
- 🎯 **Model-Based Criteria** - Coherence, fluency, safety, groundedness
- 📈 **Performance Tracking** - Compare test runs over time

## Repository Structure

```
├── sdk/                    # Python SDK (pip install -e ./sdk)
├── assistant/              # Interactive setup assistant
├── terraform/              # GCP infrastructure (BigQuery, Logging, Monitoring)
├── example_agents/         # Working examples (custom + ADK agents)
├── README.md              # This file - Overview & quick start
├── SETUP.md               # Detailed setup & deployment guide
└── CONTRIBUTING.md        # Development guidelines
```

## Documentation

Each file has a specific focus:

- **[SETUP.md](./SETUP.md)** - Complete setup guide (GCP, Terraform, configuration, troubleshooting)
- **[ROADMAP.md](./ROADMAP.md)** - Future enhancements (ADK plugin, A2A, PyPI distribution)
- **[assistant/README.md](./assistant/README.md)** - Setup assistant usage and architecture
- **[example_agents/README.md](./example_agents/README.md)** - Running example agents
- **[sdk/README.md](./sdk/README.md)** - SDK API reference
- **[CONTRIBUTING.md](./CONTRIBUTING.md)** - Development workflow

## Architecture Decisions

**Local Assistant:** Runs locally to automate file operations, validate code, and configure infrastructure (requires filesystem access).

**Wrapper Approach:** The SDK provides an evaluation wrapper that intercepts agent calls to capture observability data while running in background threads for zero-latency performance. Works universally with ADK agents, custom agents, and can extend to other frameworks.

**Compatibility Detection:** Discovers and scans all Python files in the agent directory (up to 4 levels deep) to detect ADK or Custom agent patterns, regardless of how code is organized across files.

**Manual Setup:** Prefer not to use the assistant? See [SETUP.md](./SETUP.md#manual-setup-alternative) for step-by-step manual configuration.

## Evaluation Workflow

```bash
# 1. Enable dataset collection
# Set auto_collect: true in eval_config.yaml

# 2. Run agent to collect data
python your_agent.py --test

# 3. Review & update reference answers in BigQuery
# Set reviewed=TRUE after verification

# 4. Disable collection
# Set auto_collect: false in eval_config.yaml

# 5. Run evaluation
python run_evaluation.py
```

## Technical Stack

- **Framework**: Google ADK (Agent Development Kit)
- **Infrastructure**: Terraform + GCP (Logging, Trace, Monitoring, BigQuery, Vertex AI)
- **Language**: Python 3.12+
- **CI/CD**: GitHub Actions
