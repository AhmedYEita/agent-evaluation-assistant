# Agent Evaluation SDK

Python SDK for adding production-ready evaluation to AI agents with minimal code changes.

## Installation

```bash
pip install agent-evaluation-sdk
```

## Quick Start

### 1. Create Configuration Template

```python
from agent_evaluation_sdk import create_config_template

# Creates eval_config.yaml in current directory
create_config_template()

# Or specify a custom path
create_config_template("config/my_eval.yaml")
```

### 2. Edit Configuration

Edit the generated `eval_config.yaml` with your settings:

```yaml
project_id: "your-gcp-project-id"
agent_name: "your-agent-name"

tracing:
  enabled: true
  
dataset:
  auto_collect: false  # Enable to collect test data
```

### 3. Enable Evaluation

```python
from google.genai.adk import Agent
from agent_evaluation_sdk import enable_evaluation, EvaluationConfig
from pathlib import Path

# Load config
config = EvaluationConfig.from_yaml(Path("eval_config.yaml"))

# Create your agent
agent = Agent(
    model=config.agent.model,
    system_instruction="You are a helpful assistant"
)

# Enable evaluation - that's it!
enable_evaluation(
    agent=agent,
    project_id=config.project_id,
    agent_name=config.agent_name,
    config=config
)

# Use your agent normally
response = agent.generate_content("Hello!")
```

## Features

- **Automatic Logging**: All interactions logged to Cloud Logging
- **Performance Tracing**: Cloud Trace integration for latency tracking
- **Metrics**: Cloud Monitoring for dashboards and alerts
- **Dataset Collection**: Auto-capture interactions for evaluation
- **Flexible Configuration**: Control costs with enabled/disabled flags

## Documentation

See the [main repository](https://github.com/yourusername/agent-evaluation-agent) for full documentation.
