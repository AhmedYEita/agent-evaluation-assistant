# Simple ADK Agent with Evaluation

This example demonstrates how to integrate the agent evaluation SDK with an ADK agent.

## Setup

1. Ensure infrastructure is deployed (see main README)

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up authentication:
```bash
gcloud auth application-default login
```

4. Configure your project:
```bash
export GCP_PROJECT_ID="dt-ahmedyasser-sandbox-dev"
```

5. Run the agent:
```bash
python agent.py
```

## What This Demonstrates

- ✅ One-line integration with `enable_evaluation()`
- ✅ Automatic logging to Cloud Logging
- ✅ Performance tracing in Cloud Trace
- ✅ Metrics in Cloud Monitoring
- ✅ Dataset collection for evaluation

## View Results

After running the agent:

```bash
# View logs
gcloud logging read "resource.labels.agent_name=simple-adk-agent" \
  --limit 10 --project $GCP_PROJECT_ID

# View metrics (open in browser)
echo "https://console.cloud.google.com/monitoring/dashboards?project=$GCP_PROJECT_ID"

# Export dataset
agent-eval export-dataset \
  --project-id $GCP_PROJECT_ID \
  --agent-name simple-adk-agent \
  --output dataset.json
```

