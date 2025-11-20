# Agent Evaluation Agent

**Production-ready evaluation infrastructure for AI agents with automated monitoring, testing, and quality evaluation.**

## Overview

A lightweight Python SDK and Terraform infrastructure that enables comprehensive evaluation for Google ADK agents with minimal code changes. Get structured logging, performance tracing, metrics dashboards, dataset collection, and quality testing by adding just one line of code to your agent.

### Key Features

- **One-Line Integration**: Enable full evaluation with a single function call
- **Zero-Latency Observability**: All Cloud API calls run in background threads
- **Automated Data Collection**: Logs, traces, metrics, and datasets captured automatically
- **Production-Ready**: Built on GCP services (Cloud Logging, Trace, Monitoring, BigQuery)
- **Quality Evaluation**: Vertex AI Gen AI Evaluation Service for automated and model-based metrics
- **Infrastructure as Code**: Reproducible Terraform deployment
- **Flexible Configuration**: Enable/disable services and tune performance per environment

## 🚀 Quick Start

### 1. Deploy Infrastructure (2 minutes)
```bash
cd terraform
terraform init
terraform apply -var="project_id=GCP_PROJECT_ID"
```

### 2. Configure Your Setup

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
  auto_collect: false
```

### 3. Enable Evaluation (1 line!)
```python
from agent_evaluation_sdk import enable_evaluation

# Your agent setup
agent = YourAgent(...)

# Enable evaluation
wrapper = enable_evaluation(agent, "GCP_PROJECT_ID", "my-agent", "eval_config.yaml")
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
1. **Collect** - Agent responses stored in test dataset table
2. **Review** - Update ground truth in BigQuery
3. **Evaluate** - Run agent on test cases, compare responses vs ground truth

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
- **[example_agents/](./example_agents/)** - Working code samples

## 📄 License

MIT License
