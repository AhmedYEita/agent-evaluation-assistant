# Example Agents

Working examples demonstrating SDK integration with custom and ADK agents.

## Files

- `agent_config.yaml` - Agent settings (project, model)
- `eval_config.yaml` - SDK settings (logging, tracing, metrics)
- `custom_agent.py` - Custom agent example
- `adk_agent.py` - ADK agent example
- `run_evaluation_custom.py` - Evaluation for custom agent
- `run_evaluation_adk.py` - Evaluation for ADK agent

## Quick Start

### 1. Configure

Edit `agent_config.yaml`:
```yaml
project_id: "your-gcp-project-id"
location: "us-central1"
model: "gemini-2.5-flash"
```

Edit `eval_config.yaml` (enable/disable services):
```yaml
logging:
  enabled: true
tracing:
  enabled: true
dataset:
  auto_collect: false  # Enable only for data collection
```

### 2. Install & Authenticate

```bash
pip install -r requirements.txt
gcloud auth application-default login
```

### 3. Run

```bash
# Interactive mode
python custom_agent.py
python adk_agent.py

# Test mode (collects dataset)
python custom_agent.py --test
python adk_agent.py --test

# Evaluation mode
python run_evaluation_custom.py
python run_evaluation_adk.py
```

## View Results

### Cloud Console
```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"

# Open consoles
echo "Logs: https://console.cloud.google.com/logs?project=$PROJECT_ID"
echo "Traces: https://console.cloud.google.com/traces?project=$PROJECT_ID"
echo "Dashboards: https://console.cloud.google.com/monitoring/dashboards?project=$PROJECT_ID"
echo "BigQuery: https://console.cloud.google.com/bigquery?project=$PROJECT_ID"
```

### Command Line
```bash
# View logs
gcloud logging read "resource.labels.agent_name=my-agent" --limit 10

# Query dataset
bq query --use_legacy_sql=false \
  'SELECT * FROM `agent_evaluation.my_agent_eval_dataset` LIMIT 10'

# View test results
bq query --use_legacy_sql=false \
  'SELECT test_run_name, test_timestamp FROM `agent_evaluation.my_agent_eval_metrics` ORDER BY test_timestamp DESC LIMIT 5'
```

## Evaluation Workflow

1. **Collect**: Set `auto_collect: true` → run with `--test` → set back to `false`
2. **Review**: Update `reference` field in BigQuery, set `reviewed = TRUE`
3. **Evaluate**: Run `python run_evaluation_*.py`

**BigQuery Tables:**
- `{agent_name}_eval_dataset` - Test cases
- `{agent_name}_eval_run` - Test responses (appends)
- `{agent_name}_eval_metrics` - Evaluation scores (appends)

## Config Files Explained

- **`agent_config.yaml`**: Agent-specific (project, location, model)
- **`eval_config.yaml`**: SDK behavior (what services to enable)

This separation keeps the SDK reusable across different agents.

---

See [SETUP.md](../SETUP.md) for detailed configuration and troubleshooting.
