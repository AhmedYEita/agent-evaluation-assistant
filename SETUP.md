# Complete Setup Guide

This guide provides comprehensive instructions for setting up your development environment and deploying the agent evaluation infrastructure to Google Cloud Platform.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [GCP Setup](#gcp-setup)
3. [Infrastructure Deployment](#infrastructure-deployment)
4. [SDK Installation](#sdk-installation)
5. [Running the Example](#running-the-example)
6. [Verification](#verification)
7. [Configuration](#configuration)
8. [Agent Testing & Evaluation](#agent-testing--evaluation)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, ensure you have:

**GCP Requirements:**
- [ ] A GCP project with billing enabled
- [ ] Editor or Owner role on the project

**Local Tools:**
- [ ] **Python 3.12+** ([Download](https://www.python.org/downloads/) or `brew install python@3.12`)
- [ ] **Terraform 1.5+** ([Download](https://www.terraform.io/downloads) or `brew install terraform`)
- [ ] **gcloud CLI** ([Download](https://cloud.google.com/sdk/docs/install) or `brew install google-cloud-sdk`)
- [ ] **Git**

> **Note:** If you use `pyenv`, the `.python-version` file will automatically switch to Python 3.12 when you enter the project directory (if 3.12 is already installed via `pyenv install 3.12.0`).

## Clone Repository

```bash
git clone https://github.com/AhmedYEita/agent-evaluation-agent.git
cd agent-evaluation-agent
```

## GCP Setup

### 1. Create or Select Project

```bash
# List existing projects
gcloud projects list

# Set your project ID (replace with your actual project ID)
export PROJECT_ID="gcp-project-id"

# Set active project
gcloud config set project $PROJECT_ID
```

### 2. Authenticate

```bash
# Authenticate gcloud
gcloud auth login

# Set application default credentials
gcloud auth application-default login
```

### 3. Enable Required APIs

```bash
gcloud services enable \
  logging.googleapis.com \
  monitoring.googleapis.com \
  cloudtrace.googleapis.com \
  bigquery.googleapis.com \
  aiplatform.googleapis.com
```

**Verification**:
```bash
gcloud services list --enabled | grep -E "(logging|monitoring|cloudtrace|bigquery|aiplatform)"
```

### 4. Grant Permissions

```bash
# Get your user email
USER_EMAIL=$(gcloud config get-value account)

# Grant required roles (if not already granted)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:$USER_EMAIL" \
  --role="roles/editor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:$USER_EMAIL" \
  --role="roles/logging.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:$USER_EMAIL" \
  --role="roles/monitoring.admin"
```

## Infrastructure Deployment

### 1. Configure Terraform

```bash
cd terraform

# Create terraform.tfvars with your project settings
cat > terraform.tfvars <<EOF
project_id = "$(gcloud config get-value project)"
region     = "us-central1"
EOF
```

### 2. Initialize Terraform

```bash
terraform init
```

**Expected Output**: `Terraform has been successfully initialized!`

### 3. Review Plan

```bash
terraform plan
```

Review the resources that will be created:
- BigQuery dataset and tables
- Cloud Logging bucket
- Cloud Monitoring dashboard and alerts
- Service account with IAM bindings

### 4. Deploy Infrastructure

```bash
# Deploy (takes 2-3 minutes)
terraform apply

# Type 'yes' when prompted
```

**Expected Output**:
```
Apply complete! Resources: X added, 0 changed, 0 destroyed.

Outputs:
bigquery_dataset = "gcp-project.agent_evaluation"
dashboard_url = "https://console.cloud.google.com/monitoring/..."
...
```

### 5. Verify Deployment

```bash
# Check BigQuery dataset
bq ls --project_id=$(gcloud config get-value project) | grep agent_evaluation

# Check service account
gcloud iam service-accounts list | grep agent-evaluation

# View all outputs
terraform output
```

## SDK Installation

### Development Installation

```bash
cd sdk

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install SDK with development dependencies
pip install -e ".[dev]"
```

**Verification**:
```bash
# Test import
python -c "from agent_evaluation_sdk import enable_evaluation; print('✅ SDK installed successfully')"
```

### Production Installation

```bash
pip install agent-evaluation-sdk
```

## Running the Example

### 1. Install Example Dependencies

```bash
cd ../examples/simple_adk_agent
pip install -r requirements.txt
```

### 2. Set Environment Variable

```bash
# Set your project ID
export GCP_PROJECT_ID=$(gcloud config get-value project)
```

### 3. Run the Example Agent

```bash
python agent.py
```

**Expected Output**:
```
🚀 Creating ADK Agent with Evaluation...

✅ Evaluation enabled for agent: simple-adk-agent
   - Logging: Cloud Logging
   - Tracing: Cloud Trace (sample rate: 1.0)
   - Metrics: Cloud Monitoring
   - Dataset: 100.0% of interactions

======================================================================
Agent is ready! Try asking some questions.
Type 'quit' to exit.
======================================================================

You: 
```

**Try these queries:**
- "What is Python?"
- "Explain machine learning"
- "Write a function to sort a list"
- Type 'quit' to exit

## Verification

Wait 1-2 minutes for data to propagate, then verify all components:

### Check Cloud Logging

```bash
gcloud logging read "resource.labels.agent_name=simple-adk-agent" \
  --limit 5 \
  --format json
```

**Expected**: JSON logs with interaction_id, input, output, duration_ms

### Check Cloud Trace

```bash
# Open Cloud Trace in browser
open "https://console.cloud.google.com/traces?project=$(gcloud config get-value project)"
```

**Expected**: Nested trace spans showing performance breakdown

- `agent.generate_content` - Total interaction time
- `llm.generate` - LLM API call time  
- `processing.extract` - Response processing time
- `logging.write` - Logging overhead

**Attributes**: `interaction_id`, `model`, token counts, `error` (on failures)

**Filtering in Cloud Trace:**
- Errors: `error:true` or `error.type:"ValueError"`
- Model: `model:"gemini-2.0-flash-exp"`
- Token usage: `total_tokens > 1000`
- Link to logs: Use `interaction_id` attribute

---

### Check Cloud Monitoring

```bash
# Open dashboards
open "https://console.cloud.google.com/monitoring/dashboards?project=$(gcloud config get-value project)"
```

**Expected**: "Agent Evaluation Dashboard" with metrics

### Check BigQuery

```bash
# Query collected data
bq query --use_legacy_sql=false \
'SELECT 
  interaction_id,
  agent_name,
  timestamp
FROM `agent_evaluation.simple_adk_agent_interactions`
ORDER BY timestamp DESC
LIMIT 5'
```

**Expected**: Your test interactions in the table

## Configuration

### Integrate with Your Agent

Add evaluation to your existing agent with one line:

```python
from google.genai.adk import Agent
from agent_evaluation_sdk import enable_evaluation

# Your existing agent code
agent = Agent(
    model="gemini-2.0-flash-exp",
    system_instruction="You are a helpful assistant",
)

# Enable evaluation - that's it!
enable_evaluation(
    agent=agent,
    project_id="GCP_PROJECT_ID",
    agent_name="agent-name"
)

# Use your agent normally
response = agent.generate_content("Hello!")
```

### Advanced Configuration (Optional)

Customize services in `eval_config.yaml`:

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
  auto_collect: false # Enable dataset collection
  buffer_size: 10     # Write to BigQuery every N interactions (default: 10)
```

**Service Control:**
- Set `enabled: false` on any service to disable it and reduce costs
- All services are enabled by default except `dataset.auto_collect`

**Buffer Size Guidelines:**
- **Testing/Development**: `1` (immediate writes for debugging)
- **Low-traffic production**: `10` (default, good balance)
- **High-traffic production**: `50-100` (better performance, fewer API calls)

Then load it in your agent:

```python
from agent_evaluation_sdk import enable_evaluation, load_config

config = load_config("eval_config.yaml")
enable_evaluation(agent, "GCP_PROJECT_ID", "my-agent", config=config)
```

### Configure Alerts (Optional)

Alert policies for errors and high latency are automatically created by Terraform. To add email notifications:

```bash
# Create email notification channel
gcloud alpha monitoring channels create \
  --display-name="Team Email" \
  --type=email \
  --channel-labels=email_address=team@example.com

# Or configure in Cloud Console:
# https://console.cloud.google.com/monitoring/alerting/notifications
```

Alert policies are automatically created by Terraform. Update them in `terraform/modules/monitoring/main.tf`.

## Agent Testing & Evaluation

Use Gen AI Evaluation Service to test your agent's quality with automated metrics and model-based criteria.

### Overview

**Recommended Workflow:**
1. **Collect real interactions** - Enable auto_collect to capture agent responses
2. **Review in BigQuery** - Manually review and update reference answers as needed
3. **Run evaluation** - Test directly from BigQuery (no export needed!)

### Workflow

**1. Enable Collection** (`eval_config.yaml`):
```yaml
dataset:
  auto_collect: true
```

**2. Run Agent** - Interactions auto-save to BigQuery:
```python
python agent.py  # All interactions stored in {agent_name}_eval_dataset
```

**3. Review in BigQuery Console** - Update ground truth:
```sql
UPDATE `PROJECT.agent_evaluation.my_agent_eval_dataset`
SET reference = 'Correct answer here', reviewed = TRUE
WHERE interaction_id = 'abc123'
```

**4. Run Evaluation Test**:
```bash
python run_evaluation.py  # Fetches test cases, runs agent, evaluates, saves results
```

### Available Metrics

**Automated**: BLEU, ROUGE (fast, deterministic)  
**Model-Based**: Coherence, Fluency, Safety, Groundedness, Fulfillment, Instruction Following, Verbosity

### Configuration

Configure in `eval_config.yaml`:
```yaml
dataset:
  auto_collect: true

genai_eval:
  metrics: ["bleu", "rouge"]
  criteria: ["coherence", "fluency", "safety", "groundedness"]
```

### Optional: Tool Tracing

To trace individual tool calls within your agent, apply the `@wrapper.tool_trace()` decorator:

```python
# Enable evaluation and get wrapper
wrapper = enable_evaluation(agent, project_id, agent_name, config=config)

# Decorate tools
@wrapper.tool_trace("search")
def search_tool(query: str):
    return search_api(query)

# Register with agent
agent.add_tools([search_tool])
```

Tool spans appear in Cloud Trace as `tool.{name}` under `agent.generate_content`.

### Regression Testing

Run `python run_evaluation.py` to test your current agent against the test dataset.

**BigQuery Tables Created:**

| Table | Contains |
|-------|----------|
| `{agent_name}_eval_dataset` | Test cases: `instruction`, `reference` |
| `{agent_name}_eval_YYYYMMDD_HHMM` | New responses: `instruction`, `reference`, `response` |
| `{agent_name}_eval_YYYYMMDD_HHMM_metrics` | Evaluation scores |

## Troubleshooting

### API Not Enabled

```bash
# Enable all required APIs
gcloud services enable \
  logging.googleapis.com \
  monitoring.googleapis.com \
  cloudtrace.googleapis.com \
  bigquery.googleapis.com \
  aiplatform.googleapis.com
```

### Permission Denied

```bash
# Re-authenticate
gcloud auth application-default login

# Check current user
gcloud config get-value account

# Grant additional roles if needed
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
  --member="user:$(gcloud config get-value account)" \
  --role="roles/editor"
```

### Terraform State Issues

```bash
# If state is corrupted
rm -rf .terraform terraform.tfstate*
terraform init
terraform plan
```

### SDK Import Errors

```bash
# Reinstall SDK
cd sdk
pip uninstall agent-evaluation-sdk
pip install -e ".[dev]"

# Verify installation
pip list | grep agent-evaluation
```

## Cost Estimation

Expected monthly costs for typical usage:

| Service | 10K requests | 100K requests |
|---------|--------------|---------------|
| Cloud Logging | $1-2 | $10-20 |
| Cloud Trace | $0-1 | $2-5 |
| Cloud Monitoring | $0-1 | $1-3 |
| BigQuery | $1-2 | $5-10 |
| **Total** | **~$5-10** | **~$20-40** |

## Additional Resources

- 📖 [README](./README.md) - Project overview
- 🔧 [CONTRIBUTING](./CONTRIBUTING.md) - Development guidelines
- 📂 [Examples](./examples/) - Working code samples
- 🐛 [GitHub Issues](https://github.com/AhmedYEita/agent-evaluation-agent/issues)

---

**Questions?** Check the [Troubleshooting](#troubleshooting) section or open an issue on GitHub.

