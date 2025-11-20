# Agent Evaluation SDK

Python SDK for adding production-ready evaluation to AI agents with minimal code changes.

## Installation

```bash
pip install agent-evaluation-sdk
```

## Quick Start

### 1. Create Configuration Files

**Agent Config** (`agent_config.yaml`): Your agent-specific settings
```yaml
project_id: "your-gcp-project-id"
agent_name: "your-agent-name"
model: "gemini-2.5-flash"
```

**SDK Config** (`eval_config.yaml`): SDK behavior (agent-agnostic)
```yaml
logging:
  enabled: true
tracing:
  enabled: true
dataset:
  auto_collect: false
```

### 2. Enable Evaluation

```python
from agent_evaluation_sdk import enable_evaluation

# Create your agent (any agent with a generate_content method)
agent = YourAgent(...)

# Enable evaluation - one line!
wrapper = enable_evaluation(
    agent=agent,
    project_id="your-gcp-project-id",
    agent_name="your-agent-name",
    config_path="eval_config.yaml"
)

# Use your agent normally
response = agent.generate_content("Hello!")
```

## Features

- **Automatic Logging**: All interactions logged to Cloud Logging
- **Performance Tracing**: Cloud Trace integration for latency tracking
- **Metrics**: Cloud Monitoring for dashboards and alerts
- **Dataset Collection**: Auto-capture interactions for evaluation
- **Tool Tracing**: Optional decorator for tracing individual tool calls
- **Flexible Configuration**: Control costs with enabled/disabled flags

## Documentation

See the [main repository](https://github.com/yourusername/agent-evaluation-agent) for full documentation.
