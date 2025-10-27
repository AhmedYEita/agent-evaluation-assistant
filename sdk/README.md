# Agent Evaluation SDK

Python SDK for seamless integration of evaluation infrastructure into AI agents.

## Installation

```bash
pip install agent-evaluation-sdk
```

## Quick Start

```python
from google.genai.adk import Agent
from agent_evaluation_sdk import enable_evaluation

agent = Agent(
    model="gemini-2.0-flash-exp",
    system_instruction="You are a helpful assistant",
)

enable_evaluation(
    agent=agent,
    project_id="dt-ahmedyasser-sandbox-dev",
    agent_name="my-agent"
)
```

## Features

- **Automatic Logging**: All interactions logged to Cloud Logging
- **Performance Tracing**: Cloud Trace integration for latency tracking
- **Metrics**: Cloud Monitoring for dashboards and alerts
- **Dataset Collection**: Auto-capture interactions for evaluation
- **Zero Configuration**: Works out of the box with sensible defaults

## Documentation

See the [main repository](https://github.com/yourusername/agent-evaluation-agent) for full documentation.

