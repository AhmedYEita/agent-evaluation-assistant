# Agent Evaluation Agent

**Production-ready evaluation infrastructure for AI agents with automated monitoring and testing dataset collection.**

## Overview

A lightweight Python SDK and Terraform infrastructure that enables comprehensive evaluation for Google ADK agents with minimal code changes. Get structured logging, performance tracing, metrics dashboards, and dataset collection by adding just one line of code to your agent.

### Key Features

- **One-Line Integration**: Enable full evaluation with a single function call
- **Automated Data Collection**: Logs, traces, metrics, and datasets captured automatically
- **Production-Ready**: Built on GCP services (Cloud Logging, Trace, Monitoring, BigQuery)
- **Cost-Optimized**: Configurable sampling rates, ~$10/month for 10K requests
- **Infrastructure as Code**: Reproducible Terraform deployment

## 🚀 Quick Start

### 1. Deploy Infrastructure (2 minutes)
```bash
cd terraform
terraform init
terraform apply -var="project_id=GCP_PROJECT_ID"
```

### 2. Configure Your Agent (eval_config.yaml)
```yaml
project_id: "GCP_PROJECT_ID"
agent_name: "my-agent"

agent:
  model: "gemini-2.0-flash-exp"

dataset:
  auto_collect: true  # Enable dataset collection
```

### 3. Enable Evaluation (3 lines!)
```python
from google.genai.adk import Agent
from agent_evaluation_sdk import enable_evaluation
from agent_evaluation_sdk.config import EvaluationConfig

config = EvaluationConfig.from_yaml(Path("eval_config.yaml"))
agent = Agent(model=config.agent.model, system_instruction=config.agent.system_instruction)
enable_evaluation(agent, config.project_id, config.agent_name, config=config)
```

## ✨ What You Get Automatically

After configuration, your agent has:

✅ **Structured Logging** - Every interaction logged to Cloud Logging  
✅ **Performance Tracing** - Latency breakdown in Cloud Trace  
✅ **Real-time Metrics** - Pre-built dashboard in Cloud Monitoring  
✅ **Dataset Collection** - Auto-capture to BigQuery for evaluation  
✅ **Gen AI Evaluation** - Test agent quality with automated metrics and model-based criteria  
✅ **Error Tracking** - Automatic error logging and alerts  

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
python agent.py

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
├── examples/                    # Working examples
│   └── simple_adk_agent/        # Demo agent
└── .github/workflows/           # CI/CD pipelines
```

## 📚 Documentation

- **[SETUP.md](./SETUP.md)** - Complete setup and deployment guide
- **[CONTRIBUTING.md](./CONTRIBUTING.md)** - Development and contribution guidelines
- **[examples/](./examples/)** - Working code samples

## 📄 License

MIT License
