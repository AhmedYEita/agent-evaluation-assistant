# Complete Setup Guide

This guide provides comprehensive instructions for setting up your development environment and deploying the agent evaluation infrastructure to Google Cloud Platform.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [GCP Setup](#gcp-setup)
3. [Infrastructure Deployment](#infrastructure-deployment)
4. [SDK Installation](#sdk-installation)
5. [Manual Setup (Alternative)](#manual-setup-alternative)
6. [Running the Example](#running-the-example)
7. [Verification](#verification)
8. [Configuration](#configuration)
9. [Agent Testing & Evaluation](#agent-testing--evaluation)
10. [Troubleshooting](#troubleshooting)

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

Clone anywhere - works **inside or outside** your agent project:

```bash
# Option A: Clone inside your agent project
cd /path/to/your-agent-project
git clone https://github.com/AhmedYEita/agent-evaluation-assistant
cd agent-evaluation-assistant

# Option B: Clone separately
git clone https://github.com/AhmedYEita/agent-evaluation-assistant.git
cd agent-evaluation-assistant
```

## GCP Setup

### 1. Create or Select Project

```bash
# List existing projects
gcloud projects list

# Set your project ID (replace with your actual project ID)
export PROJECT_ID="your-gcp-project-id"

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
cd ../sdk

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

## Manual Setup (Alternative)

If you prefer not to use the interactive assistant, follow these steps to manually configure your project.

### 1. Create Configuration Files

In your agent project directory, create the following configuration files:

**`agent_config.yaml`**:
```yaml
project_id: "your-gcp-project-id"
location: "us-central1"
agent_name: "my-agent"
model: "gemini-2.5-flash"
```

**`eval_config.yaml`**:
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
  storage_location: null  # Auto-generated: project.agent_evaluation.{agent_name}_eval_dataset

genai_eval:
  metrics: ["bleu", "rouge"]
  criteria: ["coherence", "fluency", "safety", "groundedness"]
  thresholds:
    bleu: 0.5
    rouge: 0.5
    coherence: 0.7
    fluency: 0.7
    safety: 0.9
    groundedness: 0.7

regression:
  test_limit: null  # null = all tests, or specify a number
  only_reviewed: true  # Only run tests with reviewed=TRUE
  dataset_table: null  # Custom BigQuery table (null = use default)
```

### 2. Copy Terraform Configuration

Copy the entire `terraform/` directory from this repository to your agent project:

```bash
# From the agent-evaluation-assistant directory
cp -r terraform /path/to/your/agent-project/
```

### 3. Deploy Infrastructure

```bash
cd /path/to/your/agent-project/terraform

# Initialize Terraform
terraform init

# Review the plan
terraform plan -var="project_id=your-gcp-project-id"

# Deploy infrastructure
terraform apply -var="project_id=your-gcp-project-id"
```

The infrastructure includes:
- BigQuery dataset and tables for dataset collection
- Cloud Logging log sinks
- Cloud Monitoring dashboards
- IAM roles and permissions

### 4. Integrate SDK with Your Agent

Add the SDK to your agent code:

```python
from agent_evaluation_sdk import enable_evaluation

# Your existing agent
agent = YourAgent(...)

# Enable evaluation - one line!
wrapper = enable_evaluation(
    agent=agent,
    project_id="your-gcp-project-id",
    agent_name="my-agent",
    config_path="eval_config.yaml"  # Path to your eval_config.yaml
)

# Use your agent normally - evaluation happens automatically
response = agent.generate_content("Hello!")

# Optional: Flush pending data and shutdown gracefully
wrapper.flush()
wrapper.shutdown()
```

**For ADK agents with tool tracing**:
```python
from agent_evaluation_sdk import enable_evaluation

# Create your ADK agent
agent = Agent(name="my_agent", model="gemini-2.5-flash")

# Enable evaluation
wrapper = enable_evaluation(agent, project_id, agent_name, "eval_config.yaml")

# Add tool tracing to your tools
@wrapper.tool_trace("search")
def search_tool(query: str) -> str:
    return search_api(query)

# Add tools to agent
agent.tools = [search_tool]
```

### 5. Verify Setup

Run a simple test to verify everything works:

```python
# test_evaluation.py
from agent_evaluation_sdk import enable_evaluation

# Create a simple test agent
class TestAgent:
    def generate_content(self, prompt):
        return f"Echo: {prompt}"

agent = TestAgent()
wrapper = enable_evaluation(agent, "your-project-id", "test-agent", "eval_config.yaml")

# Test
response = agent.generate_content("Hello!")
print(response)

# Cleanup
wrapper.flush()
wrapper.shutdown()
```

Check GCP Console to verify:
- **Cloud Logging**: Search for `jsonPayload.agent_name="test-agent"`
- **Cloud Trace**: Look for traces with name `agent.generate_content`
- **Cloud Monitoring**: Check the auto-created dashboard

## Running the Example

### 1. Install Example Dependencies

```bash
cd ../example_agents
pip install -r requirements.txt
```

### 2. Configure Agent

Edit `agent_config.yaml` with your agent settings:

```yaml
project_id: "your-gcp-project-id"
location: "us-central1"
agent_name: "my-agent"
model: "gemini-2.5-flash"
```

Edit `eval_config.yaml` to control SDK behavior:

```yaml
logging:
  enabled: true
dataset:
  auto_collect: true
```

### 3. Run the Example Agent

```bash
# Interactive mode
python custom_agent.py
# or
python adk_agent.py

# Test mode (runs predefined test queries)
python custom_agent.py --test
python adk_agent.py --test
```

**Expected Output (Interactive Mode)**:
```
Agent is ready! Type 'quit' to exit.

You: 
```

**Expected Output (Test Mode)**:
```
======================================================================
Running Test Queries
======================================================================

Total queries: 5
This will generate a dataset for evaluation.

[1/5] Query: What does HTTP stand for?
Response: HTTP stands for...
⏱️  1234ms
...
```

**Try these queries (Interactive Mode):**
- "What is Python?"
- "Calculate 25 * 48"
- "Search for the latest Python releases"
- Type 'quit' to exit

## Verification

Wait 1-2 minutes for data to propagate, then verify all components:

### Check Cloud Logging

```bash
gcloud logging read "resource.labels.agent_name=my-agent" \
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
- Model: `model:"gemini-2.5-flash"`
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
FROM `agent_evaluation.my_agent_interactions`
ORDER BY timestamp DESC
LIMIT 5'
```

**Expected**: Your test interactions in the table

## Configuration

### Integrate with Your Agent

Add evaluation to your existing agent with one line:

```python
from agent_evaluation_sdk import enable_evaluation

# Your existing agent code
agent = YourAgent(...)

# Enable evaluation - that's it!
wrapper = enable_evaluation(
    agent=agent,
    project_id="your-gcp-project-id",
    agent_name="agent-name",
    config_path="eval_config.yaml"
)

# Use your agent normally
response = agent.generate_content("Hello!")
```

### Configuration Files

**Agent Config** (`agent_config.yaml`): Agent-specific settings
```yaml
project_id: "your-gcp-project-id"
agent_name: "my-agent"
model: "gemini-2.5-flash"
```

**SDK Config** (`eval_config.yaml`): SDK behavior (agent-agnostic)

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
  storage_location: null  # BigQuery table for storing collected interactions (null = auto-created table)
  buffer_size: 10     # Write to BigQuery every N interactions (default: 10)

regression:
  test_limit: null  # Max test cases (null = no limit)
  only_reviewed: true  # Only use reviewed test cases
  dataset_table: null  # Custom BigQuery source table (null = use default: {project_id}.agent_evaluation.{agent_name}_eval_dataset)
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
from agent_evaluation_sdk import enable_evaluation

wrapper = enable_evaluation(agent, "your-gcp-project-id", "my-agent", "eval_config.yaml")
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

**1. Enable Collection** (in `eval_config.yaml`):
```yaml
dataset:
  auto_collect: true  # Enable to collect data
```

**2. Run Agent** - Interactions auto-save to BigQuery:
```bash
python custom_agent.py --test  # All interactions stored in {agent_name}_eval_dataset
```

**3. Disable Collection** (in `eval_config.yaml`):
```yaml
dataset:
  auto_collect: false  # IMPORTANT: Set back to false to avoid duplicates
```

**4. Review in BigQuery Console** - Update ground truth:
```sql
UPDATE `PROJECT.agent_evaluation.my_agent_eval_dataset`
SET reference = 'Correct answer here', reviewed = TRUE
WHERE interaction_id = 'abc123'
```

**5. Run Evaluation Test** (with `auto_collect: false`):
```bash
python run_evaluation.py  # Fetches test cases, runs agent, evaluates, saves results
```

> ⚠️ **Note**: Keep `auto_collect: false` during evaluation to prevent duplicate data collection.

### Available Metrics

**Computational Metrics**: BLEU, ROUGE (fast, deterministic)  
**LLM-as-Judge Criteria**: Coherence, Fluency, Safety, Groundedness, Fulfillment, Instruction Following, Verbosity  
**Trajectory Analysis**: Tool usage stats, performance, error rates (when `include_trajectories: true`)

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

Run the appropriate evaluation script to test your agent against the test dataset:
- `python run_evaluation_custom.py` for custom agents
- `python run_evaluation_adk.py` for ADK agents  

**Configuration Options:**
- `test_limit`: Max test cases (null = no limit)
- `only_reviewed`: Use only reviewed cases (default: true)
- `dataset_table`: Custom BigQuery source (null = use default table)

**BigQuery Tables:**

| Table | Contains | Notes |
|-------|----------|-------|
| `{agent_name}_eval_dataset` | Test cases: `instruction`, `reference`, `context`, `trajectory` | Source data for testing |
| `{agent_name}_eval_run` | All test runs: `instruction`, `reference`, `response`, `test_run_name` | Appends on each run |
| `{agent_name}_eval_metrics` | All evaluation scores: `metrics`, `criteria_scores`, `trajectory_stats` | Appends on each run |

---

## Cost Estimation

Expected monthly costs for typical usage:

| Service | 10K requests | 100K requests |
|---------|--------------|---------------|
| Cloud Logging | $1-2 | $10-20 |
| Cloud Trace | $0-1 | $2-5 |
| Cloud Monitoring | $0-1 | $1-3 |
| BigQuery | $1-2 | $5-10 |
| **Total** | **~$5-10** | **~$20-40** |


---

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
