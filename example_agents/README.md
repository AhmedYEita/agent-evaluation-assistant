# Example Agents with Evaluation

This folder contains example agents demonstrating how to integrate the evaluation SDK.

## What's Included

**Files:**
- `agent_config.yaml` - Agent-specific configuration (project, model, tools)
- `eval_config.yaml` - SDK configuration (logging, tracing, metrics)
- `custom_agent.py` - Custom agent with evaluation enabled
- `adk_agent.py` - ADK agent with evaluation enabled
- `run_evaluation_custom.py` - Evaluation script specifically for custom agent
- `run_evaluation_adk.py` - Evaluation script specifically for ADK agent
- `requirements.txt` - Python dependencies

**Features:**
- ✅ Easy integration (just one line of code)
- ✅ Zero-latency observability (background processing)
- ✅ Automatic logging, tracing, and metrics
- ✅ Tool tracing with decorator
- ✅ Dataset collection for testing
- ✅ Evaluation with Gen AI Evaluation Service

## Quick Start

### 1. Configure Your Agent

Edit `agent_config.yaml` with your agent-specific settings:

```yaml
# GCP Settings
project_id: "your-gcp-project-id"
location: "us-central1"

# Agent Settings
agent_name: "my-agent"
model: "gemini-2.5-flash"
```

Edit `eval_config.yaml` to control SDK behavior:

```yaml
# Enable/disable features as needed
logging:
  enabled: true  # Set to false to disable

dataset:
  auto_collect: true  # Enable collecting interactions to construct a testing dataset

genai_eval:
  # Configure metrics for run_evaluation.py
  metrics: ["bleu", "rouge"]
  criteria: ["coherence", "fluency", "safety"]
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Authentication

```bash
gcloud auth application-default login
```

### 4. Run

```bash
# Interactive mode - chat with your agent
python custom_agent.py
python adk_agent.py

# Test mode - generate evaluation dataset
python custom_agent.py --test
python adk_agent.py --test

# Evaluation mode - test agent on dataset
python run_evaluation_custom.py  # For custom agent
python run_evaluation_adk.py     # For ADK agent
```

## View Results

### Cloud Console

```bash
# Logs
echo "https://console.cloud.google.com/logs?project=$GCP_PROJECT_ID"

# Traces
echo "https://console.cloud.google.com/traces?project=$GCP_PROJECT_ID"

# Dashboards
echo "https://console.cloud.google.com/monitoring/dashboards?project=$GCP_PROJECT_ID"

# BigQuery
echo "https://console.cloud.google.com/bigquery?project=$GCP_PROJECT_ID"
```

### Command Line

```bash
# View logs
gcloud logging read "resource.labels.agent_name=my-agent" \
  --limit 10 --project $GCP_PROJECT_ID

# Query collected dataset
bq query --use_legacy_sql=false \
  'SELECT * FROM `agent_evaluation.my_agent_eval_dataset` LIMIT 10'

# View test results (using new append-only tables)
bq query --use_legacy_sql=false \
  'SELECT test_run_name, test_timestamp, dataset_size FROM `agent_evaluation.my_agent_eval_metrics` ORDER BY test_timestamp DESC LIMIT 5'

# View specific test run responses
bq query --use_legacy_sql=false \
  'SELECT * FROM `agent_evaluation.my_agent_eval_run` WHERE test_run_name = "test_20250124_1430" LIMIT 10'
```

## Configuration Files

- **`agent_config.yaml`**: Agent-specific settings (project ID, location, agent name, model)
- **`eval_config.yaml`**: SDK behavior (logging, tracing, metrics, dataset collection)

This separation keeps the SDK agent-agnostic. Tools and system instructions are defined directly in the agent scripts for flexibility.

## Workflow

1. **Collect Data**: Run agents with `--test` flag and `auto_collect: true` in `eval_config.yaml`
2. **Review in BigQuery**: Update `reference` field with correct answers, set `reviewed = TRUE`
3. **Run Tests**: Use the appropriate evaluation script for your agent:
   - `python run_evaluation_custom.py` for custom agents
   - `python run_evaluation_adk.py` for ADK agents

**Tables**: 
- Test dataset: `{agent_name}_eval_dataset`
- Test runs: `{agent_name}_eval_run` (all runs appended)
- Metrics: `{agent_name}_eval_metrics` (all metrics appended)

See [SETUP.md](../SETUP.md) for more details.
