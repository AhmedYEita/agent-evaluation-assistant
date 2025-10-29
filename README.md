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

### 2. Enable Evaluation in Your Agent (1 line!)
```python
from google.genai.adk import Agent
from agent_evaluation_sdk import enable_evaluation

agent = Agent(model="gemini-2.0-flash-exp", system_instruction="...")

# Enable evaluation - that's it!
enable_evaluation(agent, "GCP_PROJECT_ID", "my-agent")
```

## ✨ What You Get Automatically

After adding 1 line of code, your agent has:

✅ **Structured Logging** - Every interaction logged to Cloud Logging  
✅ **Performance Tracing** - Latency breakdown in Cloud Trace  
✅ **Real-time Metrics** - Pre-built dashboard in Cloud Monitoring  
✅ **Dataset Collection** - Auto-capture to BigQuery for evaluation  
✅ **Error Tracking** - Automatic error logging and alerts  

## 🔧 Technical Stack

- **Agent Framework**: Google ADK (Agent Development Kit)
- **Deployment Target**: Agent Engine (ready for deployment)
- **Infrastructure**: Terraform for GCP services
- **Monitoring**: Cloud Logging, Trace, Monitoring
- **Dataset Storage**: BigQuery for datasets
- **CI/CD**: GitHub Actions for validation


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
