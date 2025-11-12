# Simple ADK Agent with Evaluation

This example demonstrates how to integrate the agent evaluation SDK with an ADK agent.

## What's Included

**Files:**
- `eval_config.yaml` - Configuration for evaluation parameters
- `agent.py` - Agent with evaluation enabled and tool tracing
- `run_evaluation.py` - Evaluation testing script
- `requirements.txt` - Python dependencies

**Features:**
- ✅ Easy integration (just a few lines of code)
- ✅ Zero-latency observability (background processing)
- ✅ Automatic logging, tracing, and metrics
- ✅ Tool tracing with decorator
- ✅ Dataset collection for testing
- ✅ Evaluation with Gen AI Evaluation Service

## Quick Start

### 1. Configure Your Agent

Edit `eval_config.yaml` with your settings:

```yaml
project_id: "your-gcp-project-id"
agent_name: "my-agent"

agent:
  model: "gemini-2.5-flash"

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
python agent.py

# Test suite - generate evaluation dataset
python test_queries.py

# Evaluation mode - test agent on dataset
python run_evaluation.py
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

# View test results
bq query --use_legacy_sql=false \
  'SELECT * FROM `agent_evaluation.my_agent_eval_*_metrics` ORDER BY test_timestamp DESC LIMIT 5'
```

## Workflow

1. **Collect Data**: Run `python agent.py` with `auto_collect: true` to collect interactions
2. **Review in BigQuery**: Update `reference` field with correct answers, set `reviewed = TRUE`
3. **Run Tests**: Use `python run_evaluation.py` to evaluate agent (each run gets unique timestamp)

**Tables**: Test dataset → Test run responses → Metrics (see [SETUP.md](../../SETUP.md))
