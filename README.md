# Agent Evaluation Infrastructure

**Production-ready evaluation infrastructure for AI agents with plug-and-play integration.**

Turn on comprehensive evaluation for your ADK agents with just 3 lines of code. Get automatic logging, tracing, metrics, and dataset collection powered by GCP services.

## 🎯 What This Provides

- **One-line integration** for ADK agents (extensible to LangChain, LangGraph)
- **Automatic instrumentation**: Cloud Logging, Cloud Trace, Cloud Monitoring
- **Dataset collection**: Auto-capture production interactions for evaluation
- **Infrastructure-as-Code**: Terraform modules for complete GCP evaluation stack
- **Production-native**: All evaluation happens in your production environment

## 🚀 Quick Start

### 1. Deploy Infrastructure (One-time setup)

```bash
cd terraform
terraform init
terraform apply
```

### 2. Install SDK in Your Agent Project

```bash
pip install -e ./sdk  # Will be published to PyPI
```

### 3. Enable Evaluation (3 lines of code)

```python
from google.genai.adk import Agent
from agent_evaluation_sdk import enable_evaluation

agent = Agent(
    model="gemini-2.0-flash-exp",
    system_instruction="You are a helpful assistant",
)

# 🎯 Enable evaluation
enable_evaluation(
    agent=agent,
    project_id="your-gcp-project",
    agent_name="my-agent"
)
```

That's it! Your agent now has:
- ✅ Structured logging to Cloud Logging
- ✅ Performance tracing in Cloud Trace
- ✅ Metrics in Cloud Monitoring
- ✅ Automatic dataset collection
- ✅ Pre-built dashboards

## 📊 View Results

```bash
# Open monitoring dashboard
gcloud monitoring dashboards list --filter="displayName:my-agent"

# View recent logs
gcloud logging read "resource.labels.agent_name=my-agent" --limit 10

# Export dataset for evaluation
agent-eval export-dataset --agent my-agent --output dataset.json
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│  Your Agent (ADK)                       │
│  + agent_evaluation_sdk (3 lines)      │
└─────────────┬───────────────────────────┘
              │
              ├──► Cloud Logging (structured logs)
              ├──► Cloud Trace (performance traces)
              ├──► Cloud Monitoring (metrics & dashboards)
              ├──► BigQuery (dataset storage)
              └──► Gen AI Evaluation Service
```

## 📁 Repository Structure

```
.
├── sdk/                          # Python SDK (pip installable)
│   ├── agent_evaluation_sdk/
│   │   ├── core.py              # Main wrapper
│   │   ├── logging.py           # Cloud Logging integration
│   │   ├── tracing.py           # Cloud Trace integration
│   │   ├── metrics.py           # Cloud Monitoring
│   │   └── dataset.py           # Dataset collection
│   └── pyproject.toml
│
├── terraform/                    # Infrastructure-as-Code
│   ├── modules/
│   │   ├── logging/             # Cloud Logging setup
│   │   ├── monitoring/          # Dashboards & alerts
│   │   ├── tracing/             # Cloud Trace config
│   │   └── storage/             # BigQuery for datasets
│   └── main.tf
│
├── examples/                     # Example integrations
│   └── simple_adk_agent/        # Basic ADK agent with evaluation
│
├── .github/
│   └── workflows/               # CI/CD pipelines
│
└── docs/                        # Documentation
```

## 🔧 Configuration (Optional)

Create `eval_config.yaml` for custom settings:

```yaml
evaluation:
  metrics:
    - accuracy
    - safety
    - latency
  
  logging:
    level: INFO
    include_trajectories: true
  
  dataset:
    auto_collect: true
    sample_rate: 0.1  # Log 10% of interactions
```

## 🎓 What You'll Learn

This project demonstrates:
- **ADK**: Building production agents
- **GCP Services**: Cloud Logging, Trace, Monitoring, BigQuery
- **Terraform**: Infrastructure-as-Code for evaluation stack
- **CI/CD**: Automated testing and deployment
- **SDK Design**: Creating developer-friendly libraries
- **MCP** (future): Agent-to-agent communication

## 📚 Documentation

- [Full Documentation](./docs/README.md)
- [SDK Reference](./docs/sdk-reference.md)
- [Infrastructure Guide](./docs/infrastructure.md)
- [Examples](./examples/)

## 🚧 Roadmap

- [x] Core SDK with ADK integration
- [x] Terraform infrastructure modules
- [ ] CLI tools for dataset management
- [ ] LangChain adapter
- [ ] LangGraph adapter
- [ ] Management Agent (ADK) for advanced features
- [ ] MCP server for external evaluation

## 📄 License

MIT License - see [LICENSE](./LICENSE)

## 🤝 Contributing

This project is currently private. Once stable, it will be made public for community contributions.

