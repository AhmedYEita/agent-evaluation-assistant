# Agent Evaluation SDK

Python SDK for adding production-ready evaluation to AI agents with one line of code.

## Installation

```bash
# From local clone
pip install -e ./sdk

# Or from PyPI (when published)
pip install agent-evaluation-sdk
```

## Quick Start

```python
from agent_evaluation_sdk import enable_evaluation

# Your existing agent
agent = YourAgent(...)

# Enable evaluation - one line!
wrapper = enable_evaluation(
    agent=agent,
    project_id="your-gcp-project-id",
    agent_name="my-agent",
    config_path="eval_config.yaml"
)

# Use normally - observability happens automatically
response = agent.generate_content("Hello!")

# Cleanup on exit
wrapper.flush()
wrapper.shutdown()
```

## Configuration

Create `eval_config.yaml`:

```yaml
logging:
  enabled: true
  level: "INFO"
  include_trajectories: true

tracing:
  enabled: true

metrics:
  enabled: true

dataset:
  auto_collect: false  # Enable only when collecting test data
  buffer_size: 10

genai_eval:
  metrics: ["bleu", "rouge"]
  criteria: ["coherence", "fluency", "safety"]

regression:
  test_limit: null
  only_reviewed: true
```

## Features

- **Auto Logging**: All interactions → Cloud Logging
- **Performance Tracing**: Request flow → Cloud Trace
- **Metrics**: Latency, errors, tokens → Cloud Monitoring
- **Dataset Collection**: Interactions → BigQuery (opt-in)
- **Tool Tracing**: Decorate functions with `@wrapper.tool_trace("name")`
- **Zero Latency**: All Cloud API calls in background threads

## Tool Tracing (Optional)

```python
wrapper = enable_evaluation(agent, project_id, agent_name, config)

@wrapper.tool_trace("search")
def search_tool(query: str) -> str:
    return search_api(query)

agent.add_tools([search_tool])
```

Tool spans appear in Cloud Trace as `tool.{name}`.

## Supported Agents

- **ADK agents**: Use the `EvaluationPlugin` for native integration
- **Custom agents**: Use the wrapper (must have `generate_content(prompt)` method)

**Note:** Both approaches are maintained - plugin for ADK, wrapper for custom agents and other frameworks (LangChain, CrewAI, etc.).

## Documentation

See the [main repository](https://github.com/AhmedYEita/agent-evaluation-assistant) for:
- Complete setup guide
- Infrastructure deployment
- Evaluation workflow
- Examples

## API Reference

### `enable_evaluation(agent, project_id, agent_name, config_path=None)`

**Parameters:**
- `agent`: Agent or runner instance
- `project_id`: GCP project ID
- `agent_name`: Name for BigQuery tables and metrics
- `config_path`: Path to eval_config.yaml (optional)

**Returns:** `EvaluationWrapper` instance

**Methods:**
- `wrapper.flush()` - Flush pending data to BigQuery
- `wrapper.shutdown()` - Graceful shutdown (waits for background tasks)
- `wrapper.tool_trace(name)` - Decorator for tool tracing
