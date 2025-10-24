# Agent Evaluation Infrastructure - Documentation

Complete guide to deploying and using the agent evaluation infrastructure.

## Table of Contents

- [Getting Started](#getting-started)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage Guide](#usage-guide)
- [Configuration](#configuration)
- [Viewing Results](#viewing-results)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

1. **GCP Project** with billing enabled
2. **GCP CLI** (`gcloud`) installed and authenticated
3. **Terraform** >= 1.5.0
4. **Python** >= 3.10
5. **Permissions**: Project Editor or equivalent roles

### Quick Start (5 minutes)

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd agent-evaluation-agent

# 2. Deploy infrastructure
cd terraform
terraform init
terraform apply -var="project_id=your-project-id"

# 3. Install SDK
cd ../sdk
pip install -e .

# 4. Try the example
cd ../examples/simple_adk_agent
export GCP_PROJECT_ID="your-project-id"
python agent.py
```

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│              Your ADK Agent                              │
│  + agent_evaluation_sdk.enable_evaluation()             │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Automatic Instrumentation
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────┐          ┌──────────────┐
│ Cloud Logging│          │ Cloud Trace  │
│  - Structured│          │  - Latency   │
│  - Searchable│          │  - Tool calls│
└──────────────┘          └──────────────┘
        │                         │
        ▼                         ▼
┌──────────────┐          ┌──────────────┐
│   BigQuery   │          │ Monitoring   │
│  - Datasets  │          │  - Dashboards│
│  - Analytics │          │  - Alerts    │
└──────────────┘          └──────────────┘
```

### Components

1. **Python SDK** (`agent_evaluation_sdk`)
   - Core wrapper for agent instrumentation
   - Automatic logging, tracing, metrics
   - Dataset collection
   - CLI tools

2. **Terraform Infrastructure**
   - Cloud Logging configuration
   - Cloud Monitoring dashboards & alerts
   - BigQuery datasets for storage
   - IAM and service accounts

3. **CI/CD Pipeline**
   - Automated testing
   - Infrastructure validation
   - Deployment automation

## Installation

### 1. Deploy Infrastructure

```bash
cd terraform

# Create terraform.tfvars
cat > terraform.tfvars <<EOF
project_id = "your-gcp-project-id"
region     = "us-central1"
EOF

# Initialize and apply
terraform init
terraform apply
```

**Expected Output:**
- BigQuery dataset created
- Monitoring dashboard deployed
- Service account configured
- Alert policies active

### 2. Install SDK

#### Option A: From Source (Development)
```bash
cd sdk
pip install -e ".[dev]"
```

#### Option B: From PyPI (When Published)
```bash
pip install agent-evaluation-sdk
```

### 3. Configure Authentication

```bash
# For local development
gcloud auth application-default login

# For production (use service account)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

## Usage Guide

### Basic Integration (ADK Agent)

```python
from google.genai.adk import Agent
from agent_evaluation_sdk import enable_evaluation

# Create your agent
agent = Agent(
    model="gemini-2.0-flash-exp",
    system_instruction="You are a helpful assistant",
)

# Enable evaluation (one line!)
enable_evaluation(
    agent=agent,
    project_id="your-gcp-project",
    agent_name="my-agent"
)

# Use agent normally - evaluation happens automatically
response = agent.generate_content("Hello!")
```

### With Custom Configuration

```python
# eval_config.yaml
evaluation:
  logging:
    level: INFO
    include_trajectories: true
  dataset:
    auto_collect: true
    sample_rate: 0.1

# Python code
enable_evaluation(
    agent=agent,
    project_id="your-gcp-project",
    agent_name="my-agent",
    config_path="eval_config.yaml"
)
```

### What Gets Logged Automatically

For each agent interaction:
- ✅ **Input**: User prompt/query
- ✅ **Output**: Agent response
- ✅ **Latency**: Response time in milliseconds
- ✅ **Tokens**: Input/output token counts
- ✅ **Model**: Model name used
- ✅ **Safety Ratings**: Content safety scores
- ✅ **Errors**: Any exceptions with context
- ✅ **Tool Calls**: If using function calling
- ✅ **Metadata**: Custom fields

## Configuration

### Configuration Options

```yaml
# eval_config.yaml

project_id: "your-project-id"
agent_name: "my-agent"

logging:
  level: "INFO"                    # DEBUG, INFO, WARNING, ERROR
  include_trajectories: true       # Log intermediate steps
  include_metadata: true           # Log additional context

tracing:
  enabled: true
  sample_rate: 1.0                 # 0.0 to 1.0 (100% traced)

metrics:
  enabled: true
  custom_metrics: []               # Add custom metric names

dataset:
  auto_collect: true
  sample_rate: 0.1                 # Collect 10% of interactions
  storage_location: null           # null = auto (recommended)
```

### Environment Variables

```bash
# GCP Project
export GCP_PROJECT_ID="your-project-id"

# Authentication
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/sa-key.json"

# Optional: Override defaults
export AGENT_EVAL_LOG_LEVEL="DEBUG"
export AGENT_EVAL_SAMPLE_RATE="0.5"
```

## Viewing Results

### Cloud Logging

```bash
# View recent logs
gcloud logging read "resource.labels.agent_name=my-agent" \
  --limit 50 \
  --project your-project-id \
  --format json

# Filter by time
gcloud logging read "resource.labels.agent_name=my-agent AND timestamp>=\"2025-10-24T00:00:00Z\"" \
  --limit 100 \
  --project your-project-id
```

**Console:** https://console.cloud.google.com/logs

### Cloud Trace

View performance traces:
```bash
# Open in browser
open "https://console.cloud.google.com/traces?project=your-project-id"
```

**What to look for:**
- Overall request latency
- LLM call duration
- Tool execution time
- Bottlenecks

### Cloud Monitoring

**Dashboards:** https://console.cloud.google.com/monitoring/dashboards

Pre-built dashboard includes:
- Response latency (p50, p95, p99)
- Token usage over time
- Success/error rates
- Error breakdown by type

### BigQuery (Datasets)

```bash
# Export dataset
agent-eval export-dataset \
  --project-id your-project-id \
  --agent-name my-agent \
  --output dataset.json \
  --limit 1000

# Query in BigQuery
bq query --use_legacy_sql=false '
SELECT 
  timestamp,
  input,
  output,
  JSON_VALUE(metadata, "$.duration_ms") as duration_ms
FROM `your-project-id.agent_evaluation.my_agent_interactions`
ORDER BY timestamp DESC
LIMIT 10
'
```

## Best Practices

### 1. Sampling Strategy

**Development:**
```python
# Trace and log everything
config.tracing.sample_rate = 1.0
config.dataset.sample_rate = 1.0
```

**Production:**
```python
# Reduce costs while maintaining visibility
config.tracing.sample_rate = 0.1     # 10% traced
config.dataset.sample_rate = 0.05    # 5% collected
```

### 2. Dataset Collection

- Start with **high sampling** during development
- Collect diverse examples (success, failure, edge cases)
- Review and curate collected data
- Use for creating evaluation benchmarks

### 3. Monitoring & Alerts

- Set up alert policies for:
  - High error rates (>5%)
  - High latency (>5s)
  - Token usage spikes
- Review dashboards weekly
- Investigate anomalies promptly

### 4. Cost Optimization

**Estimated costs for 10,000 requests/day:**

| Service | Cost/Month |
|---------|-----------|
| Cloud Logging | $1-5 |
| Cloud Trace | $0-2 (with sampling) |
| Cloud Monitoring | $0-1 |
| BigQuery | $1-5 (depends on queries) |
| **Total** | **~$5-15/month** |

**Tips:**
- Use sampling in production
- Set data retention limits
- Archive old datasets to Cloud Storage

### 5. Security

```python
# Never log sensitive data
# The SDK automatically truncates long strings

# For extra security, sanitize inputs:
def sanitize(text):
    # Remove PII, secrets, etc.
    return text

sanitized_input = sanitize(user_input)
response = agent.generate_content(sanitized_input)
```

## Troubleshooting

### Common Issues

#### 1. "Permission Denied" Errors

**Cause:** Missing IAM permissions

**Fix:**
```bash
# Grant required roles to your user/service account
gcloud projects add-iam-policy-binding your-project-id \
  --member="user:your-email@example.com" \
  --role="roles/logging.logWriter"

gcloud projects add-iam-policy-binding your-project-id \
  --member="user:your-email@example.com" \
  --role="roles/cloudtrace.agent"
```

#### 2. "Dataset/Table Not Found"

**Cause:** BigQuery table not created yet

**Fix:** Tables are created automatically on first use. If issues persist:
```bash
# Create table manually
bq mk --table \
  your-project-id:agent_evaluation.my_agent_interactions \
  interaction_id:STRING,agent_name:STRING,timestamp:TIMESTAMP,input:STRING,output:STRING,metadata:JSON,trajectory:JSON
```

#### 3. No Data Appearing in Logs

**Check:**
1. Confirm project ID is correct
2. Verify authentication (`gcloud auth list`)
3. Check SDK is imported: `from agent_evaluation_sdk import enable_evaluation`
4. Look for error messages in console

#### 4. High Costs

**Reduce:**
1. Lower sampling rates
2. Set data retention limits
3. Use log exclusion filters for verbose logs
4. Archive old data to Cloud Storage

### Getting Help

1. Check [GitHub Issues](https://github.com/your-repo/issues)
2. Review [Examples](../examples/)
3. Read [API Reference](./sdk-reference.md)

## Next Steps

- 📖 Read [SDK Reference](./sdk-reference.md)
- 🏗️ See [Infrastructure Guide](./infrastructure.md)
- 🔧 Try [Advanced Examples](../examples/)
- 🚀 Deploy to production

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development setup and guidelines.

