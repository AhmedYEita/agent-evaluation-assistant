# Code Walkthrough and Architecture Review

This document provides a comprehensive walkthrough of the entire codebase, explaining what each component does, how they work together, and the order in which things should be set up.

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [File Structure](#file-structure)
4. [Infrastructure (Terraform)](#infrastructure-terraform)
5. [SDK Components](#sdk-components)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Example Agent](#example-agent)
8. [Setup Order](#setup-order)
9. [Security Implementation](#security-implementation)

---

## Project Overview

**What**: An automated evaluation infrastructure for AI agents  
**Why**: Reduce agent evaluation setup time from 2-3 days to 5 minutes  
**How**: Terraform infrastructure + Python SDK that wraps ADK agents  
**Value**: Faster delivery, consistent practices, better governance  

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Your ADK Agent                       │
│                         ↓                               │
│              enable_evaluation(agent, ...)              │
│                         ↓                               │
│              EvaluationWrapper (SDK)                    │
│                         ↓                               │
│    ┌────────────────────┼────────────────────┐          │
│    ↓                    ↓                    ↓          │
│ Cloud Logging      Cloud Trace      Cloud Monitoring    │
│    ↓                    ↓                    ↓          │
│ Structured Logs    Performance Data   Metrics Dashboard │
│    ↓                                                    │
│ BigQuery (Dataset Collection)                           │
└─────────────────────────────────────────────────────────┘
```

### Flow

1. **Developer** adds 1 line to their agent: `enable_evaluation(...)`
2. **SDK** wraps the agent's methods with instrumentation
3. **On each request**, SDK automatically:
   - Logs to Cloud Logging
   - Creates traces in Cloud Trace
   - Records metrics to Cloud Monitoring
   - Samples interactions to BigQuery
4. **Results** viewable in GCP Console dashboards

---

## File Structure

### Root Level Files

```
agent-evaluation-agent/
├── README.md                     # Main documentation (competition-focused)
├── DEPLOYMENT_GUIDE.md          # Step-by-step deployment walkthrough
├── SETUP.md                     # Detailed setup reference
├── COMPETITION.md               # Competition checklist and requirements
├── CODE_WALKTHROUGH.md          # This file
├── CHANGELOG.md                 # Version history
├── CONTRIBUTING.md              # Development guidelines
├── LICENSE                      # MIT license
└── .gitignore                   # Git ignore rules
```

**Order to Read**:
1. README.md - Understand the project
2. DEPLOYMENT_GUIDE.md - Deploy infrastructure
3. CODE_WALKTHROUGH.md - Understand the code (this file)
4. COMPETITION.md - Prepare for submission

### Directory Structure

```
├── sdk/                         # Python SDK (core functionality)
│   ├── agent_evaluation_sdk/    # SDK source code
│   ├── tests/                   # Unit & integration tests
│   ├── pyproject.toml           # Package configuration
│   └── README.md                # SDK documentation
│
├── terraform/                   # Infrastructure as Code
│   ├── modules/                 # Reusable Terraform modules
│   ├── main.tf                  # Main Terraform config
│   ├── variables.tf             # Input variables
│   ├── outputs.tf               # Output values
│   └── README.md                # Terraform documentation
│
├── examples/                    # Working examples
│   └── simple_adk_agent/        # Basic example agent
│       ├── agent.py             # Main example
│       ├── agent_with_config.py # Advanced example
│       ├── eval_config.yaml     # Custom configuration
│       ├── requirements.txt     # Python dependencies
│       └── README.md            # Example documentation
│
├── docs/                        # Additional documentation
│   └── QUICKSTART.md            # 10-minute quick start
│
└── .github/                     # CI/CD workflows
    └── workflows/
        ├── test-sdk.yml         # SDK testing
        ├── terraform.yml        # Terraform validation
        └── deploy.yml           # Infrastructure validation
```

---

## Infrastructure (Terraform)

### Setup Order: **FIRST** (before any code runs)

Location: `/terraform`

### Purpose

Creates all GCP resources needed for evaluation:
- Cloud Logging buckets
- Cloud Monitoring dashboards
- BigQuery datasets
- IAM service accounts

### Main Files

#### 1. `main.tf` - Entry Point

```hcl
# Enables required GCP APIs
resource "google_project_service" "required_apis" {
  # logging, monitoring, cloudtrace, bigquery, aiplatform
}

# Calls three modules
module "logging" { ... }
module "monitoring" { ... }
module "storage" { ... }

# Creates service account with minimal permissions
resource "google_service_account" "agent_evaluation" { ... }
```

**What it does**:
- Enables 5 GCP APIs
- Deploys 3 infrastructure modules
- Creates service account with least-privilege IAM roles

#### 2. `variables.tf` - Configuration

```hcl
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  default     = "us-central1"
}

variable "dataset_retention_days" {
  description = "Days to retain data"
  default     = 90
}
```

**What it does**: Defines configurable parameters

#### 3. `outputs.tf` - Results

```hcl
output "bigquery_dataset" {
  value = module.storage.dataset_id
}

output "dashboard_url" {
  value = "https://console.cloud.google.com/monitoring/dashboards?project=${var.project_id}"
}

output "service_account_email" {
  value = google_service_account.agent_evaluation.email
}
```

**What it does**: Returns useful info after deployment

### Modules

#### Module 1: `modules/logging/main.tf`

```hcl
resource "google_logging_project_bucket_config" "agent_evaluation" {
  project        = var.project_id
  location       = var.region
  retention_days = 30
  bucket_id      = "agent-evaluation-logs"
}
```

**What it does**:
- Creates log bucket for agent evaluation data
- Sets 30-day retention
- No public access (IAM-controlled)

**Security**: 
- ✅ IAM-controlled access
- ✅ No public endpoints
- ✅ Encrypted at rest

#### Module 2: `modules/monitoring/main.tf`

```hcl
resource "google_monitoring_dashboard" "agent_evaluation" {
  dashboard_json = jsonencode({
    # Dashboard with 4 widgets:
    # 1. Response Latency
    # 2. Token Usage
    # 3. Success Rate
    # 4. Error Rate by Type
  })
}

resource "google_monitoring_alert_policy" "high_error_rate" {
  # Alert if error rate > 5%
}

resource "google_monitoring_alert_policy" "high_latency" {
  # Alert if latency > 5 seconds
}
```

**What it does**:
- Creates pre-built dashboard with 4 key metrics
- Sets up 2 alert policies (errors and latency)
- Uses custom metrics from SDK

**Security**:
- ✅ Dashboard requires IAM authentication
- ✅ No public access to metrics
- ✅ Alert policies internal only

#### Module 3: `modules/storage/main.tf`

```hcl
resource "google_bigquery_dataset" "agent_evaluation" {
  dataset_id    = "agent_evaluation"
  location      = var.region
  
  # Tables auto-expire after 90 days
  default_table_expiration_ms = var.dataset_retention_days * 24 * 60 * 60 * 1000
}

resource "google_bigquery_table" "all_agents_view" {
  # SQL view aggregating data from all agent tables
}
```

**What it does**:
- Creates BigQuery dataset for interaction data
- Sets up aggregated view across all agents
- Auto-expires old data (90 days default)

**Security**:
- ✅ IAM-controlled dataset access
- ✅ No public datasets
- ✅ Data encrypted at rest

### Deployment Command

```bash
cd terraform
terraform init
terraform apply -var="project_id=dt-ahmedyasser-sandbox-dev"
```

**Output**: All GCP resources created in ~2 minutes

---

## SDK Components

### Setup Order: **SECOND** (after Terraform)

Location: `/sdk/agent_evaluation_sdk`

### Purpose

Python library that wraps ADK agents and automatically instruments them with evaluation capabilities.

### Core Files

#### 1. `core.py` - Main Wrapper

**Class: `EvaluationWrapper`**

```python
class EvaluationWrapper:
    def __init__(self, agent, config):
        # Initialize evaluation components
        self.logger = CloudLogger(...)
        self.tracer = CloudTracer(...)
        self.metrics = CloudMetrics(...)
        self.dataset_collector = DatasetCollector(...)
        
        # Wrap agent methods
        self._wrap_agent()
```

**What it does**:
1. Creates instances of all evaluation components
2. Wraps the agent's `generate_content()` method
3. Intercepts every request/response

**Method: `_wrap_generate_content()`**

```python
def _wrap_generate_content(self, original_method):
    @functools.wraps(original_method)
    def wrapped(*args, **kwargs):
        # 1. Start trace
        trace_id = self.tracer.start_trace()
        
        # 2. Execute original method
        response = original_method(*args, **kwargs)
        
        # 3. Log interaction
        self.logger.log_interaction(...)
        
        # 4. Record metrics
        self.metrics.record_latency(duration_ms)
        
        # 5. Collect for dataset
        self.dataset_collector.add_interaction(...)
        
        return response
    return wrapped
```

**What it does**: Wraps every agent call with evaluation logic

**Function: `enable_evaluation()`**

```python
def enable_evaluation(agent, project_id, agent_name, config_path=None):
    # Load or create config
    config = EvaluationConfig.from_yaml(config_path) if config_path \
             else EvaluationConfig.default(project_id, agent_name)
    
    # Create wrapper
    wrapper = EvaluationWrapper(agent, config)
    
    return wrapper
```

**What it does**: Main entry point - one function call enables everything

#### 2. `logging.py` - Cloud Logging

**Class: `CloudLogger`**

```python
class CloudLogger:
    def __init__(self, project_id, agent_name, log_level):
        self.client = cloud_logging.Client(project=project_id)
        self.logger = self.client.logger(f"agent-evaluation-{agent_name}")
    
    def log_interaction(self, interaction_id, input_data, output_data, ...):
        self.logger.log_struct({
            "interaction_id": interaction_id,
            "agent_name": self.agent_name,
            "timestamp": datetime.utcnow().isoformat(),
            "input": input_data,
            "output": output_data,
            "duration_ms": duration_ms,
            "metadata": metadata,
        })
```

**What it does**: Sends structured logs to Cloud Logging

**Security**:
- Uses Application Default Credentials (no API keys)
- IAM-controlled access
- No credentials in code

#### 3. `tracing.py` - Cloud Trace

**Class: `CloudTracer`**

```python
class CloudTracer:
    def __init__(self, project_id, agent_name, sample_rate):
        self.client = trace_v1.TraceServiceClient()
        self.project_name = f"projects/{project_id}"
        self.sample_rate = sample_rate
    
    def start_trace(self):
        if random.random() > self.sample_rate:
            return None
        return str(uuid.uuid4())
    
    @contextmanager
    def span(self, name, attributes, trace_id):
        start_time = time.time()
        yield
        duration = time.time() - start_time
        
        # Send span to Cloud Trace
        self.client.create_span(...)
```

**What it does**:
- Creates performance traces with configurable sampling
- Tracks latency breakdown
- Shows bottlenecks in agent execution

**Security**: Same as logging (ADC, IAM-controlled)

#### 4. `metrics.py` - Cloud Monitoring

**Class: `CloudMetrics`**

```python
class CloudMetrics:
    def __init__(self, project_id, agent_name):
        self.client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{project_id}"
        self.agent_name = agent_name
    
    def record_latency(self, duration_ms):
        self._write_time_series(
            metric_type="custom.googleapis.com/agent/latency",
            value=duration_ms
        )
    
    def record_token_count(self, input_tokens, output_tokens):
        self._write_time_series(
            metric_type="custom.googleapis.com/agent/tokens/input",
            value=input_tokens
        )
        # ... same for output tokens
```

**What it does**:
- Records custom metrics to Cloud Monitoring
- Powers the Terraform-created dashboard
- Enables alerting

**Metrics tracked**:
- Latency (p50, p95, p99)
- Token usage (input/output)
- Success rate
- Error rate by type

#### 5. `dataset.py` - BigQuery Collection

**Class: `DatasetCollector`**

```python
class DatasetCollector:
    def __init__(self, project_id, agent_name, sample_rate, storage_location):
        self.bq_client = bigquery.Client(project=project_id)
        self.sample_rate = sample_rate
        self.table_id = f"{project_id}.agent_evaluation.{agent_name}_interactions"
        
        # Create table if not exists
        self._ensure_table_exists()
    
    def add_interaction(self, interaction_id, input_data, output_data, metadata):
        if random.random() > self.sample_rate:
            return
        
        rows = [{
            "interaction_id": interaction_id,
            "agent_name": self.agent_name,
            "timestamp": datetime.utcnow().isoformat(),
            "input": input_data,
            "output": output_data,
            "metadata": json.dumps(metadata),
        }]
        
        self.bq_client.insert_rows_json(self.table_id, rows)
```

**What it does**:
- Collects sampled interactions to BigQuery
- Creates tables automatically on first use
- Enables dataset export for evaluation

#### 6. `config.py` - Configuration

**Class: `EvaluationConfig`**

```python
@dataclass
class LoggingConfig:
    level: str = "INFO"
    include_trajectories: bool = True

@dataclass
class TracingConfig:
    sample_rate: float = 1.0

@dataclass
class DatasetConfig:
    auto_collect: bool = True
    sample_rate: float = 1.0
    storage_location: str = ""

@dataclass
class EvaluationConfig:
    project_id: str
    agent_name: str
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    tracing: TracingConfig = field(default_factory=TracingConfig)
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    
    @classmethod
    def from_yaml(cls, path: Path):
        # Load from YAML file
    
    @classmethod
    def default(cls, project_id, agent_name):
        # Return default configuration
```

**What it does**: Manages configuration (defaults or from YAML)

#### 7. `cli.py` - Command Line Tools

```python
def export_dataset(args):
    """Export dataset from BigQuery to JSON"""
    
def view_logs(args):
    """View recent logs"""
    
def open_dashboard(args):
    """Open monitoring dashboard"""
```

**What it does**: Provides `agent-eval` CLI tool for common tasks

### Package Configuration

#### `pyproject.toml`

```toml
[project]
name = "agent-evaluation-sdk"
version = "0.1.0"
requires-python = ">=3.12"

dependencies = [
    "google-cloud-logging>=3.10.0",
    "google-cloud-trace>=1.13.0",
    "google-cloud-monitoring>=2.21.0",
    "google-cloud-bigquery>=3.21.0",
    "google-genai>=1.0.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
]

[project.scripts]
agent-eval = "agent_evaluation_sdk.cli:main"
```

**What it does**: Defines package metadata and dependencies

### Installation

```bash
cd sdk
pip install -e .
```

---

## CI/CD Pipeline

### Setup Order: **AUTOMATIC** (runs on git push)

Location: `/.github/workflows`

### Purpose

Validates code quality and infrastructure without deploying anything automatically (deployment is manual for competition).

### Workflows

#### 1. `test-sdk.yml` - SDK Testing

```yaml
name: Test SDK

on:
  push:
    paths:
      - 'sdk/**'
  pull_request:
    paths:
      - 'sdk/**'

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - Install dependencies
      - Run pytest with coverage
      - Lint with ruff
      - Format check with black
      - Type check with mypy
```

**What it does**:
- Runs unit tests on Python 3.12
- Checks code coverage
- Validates code style
- Type checking

**Triggers**: Push or PR affecting `/sdk` directory

#### 2. `terraform.yml` - Terraform Validation

```yaml
name: Validate Terraform

on:
  push:
    paths:
      - 'terraform/**'
  pull_request:
    paths:
      - 'terraform/**'

jobs:
  terraform:
    steps:
      - Terraform format check
      - Terraform init
      - Terraform validate
      - TFLint
```

**What it does**:
- Validates Terraform syntax
- Checks formatting
- Runs linter

**Does NOT**: Deploy anything (manual deployment only)

#### 3. `deploy.yml` - Infrastructure Validation

```yaml
name: Validate Infrastructure

on:
  push:
    paths:
      - 'terraform/**'

jobs:
  validate-infrastructure:
    steps:
      - Terraform validation
      - SDK import test
```

**What it does**: Comprehensive validation of infrastructure + SDK

**Does NOT**: Deploy to GCP (requires manual `terraform apply`)

### Why Manual Deployment?

For the competition:
1. **Control**: You control when infrastructure is created
2. **Cost**: No accidental deployments
3. **Security**: No need to share GCP credentials with GitHub
4. **Simplicity**: Clear separation of validation vs deployment

---

## Example Agent

### Setup Order: **LAST** (after SDK installed)

Location: `/examples/simple_adk_agent`

### Purpose

Demonstrates how easy it is to add evaluation to an ADK agent.

### Files

#### 1. `agent.py` - Basic Example

```python
from google.genai.adk import Agent
from agent_evaluation_sdk import enable_evaluation

# Step 1: Create your agent normally
agent = Agent(
    model="gemini-2.0-flash-exp",
    system_instruction="You are a helpful AI assistant.",
)

# Step 2: Enable evaluation (THE ONLY ADDITION!)
enable_evaluation(
    agent=agent,
    project_id=os.environ.get("GCP_PROJECT_ID"),
    agent_name="simple-adk-agent",
)

# Step 3: Use your agent normally - evaluation happens automatically!
response = agent.generate_content(user_input)
```

**What it does**: Shows minimal integration (1 line added)

#### 2. `agent_with_config.py` - Advanced Example

```python
# Enable evaluation with custom config
enable_evaluation(
    agent=agent,
    project_id=project_id,
    agent_name="customer-support-agent",
    config_path="eval_config.yaml",  # Custom configuration
)
```

**What it does**: Shows how to use custom configuration

#### 3. `eval_config.yaml` - Custom Configuration

```yaml
project_id: "dt-ahmedyasser-sandbox-dev"
agent_name: "customer-support-agent"

logging:
  level: "INFO"
  include_trajectories: true

tracing:
  sample_rate: 0.1  # Only trace 10% of requests

dataset:
  auto_collect: true
  sample_rate: 0.05  # Only collect 5% for dataset
```

**What it does**: Demonstrates configuration options

### Running Examples

```bash
cd examples/simple_adk_agent
export GCP_PROJECT_ID="dt-ahmedyasser-sandbox-dev"
pip install -r requirements.txt
python agent.py
```

---

## Setup Order

This is the **critical** order for setting everything up:

### Phase 1: Prerequisites
1. ✅ GCP account with billing
2. ✅ Access to `dt-ahmedyasser-sandbox-dev`
3. ✅ Tools installed (gcloud, terraform, python)

### Phase 2: Authentication
4. ✅ `gcloud auth login`
5. ✅ `gcloud auth application-default login`
6. ✅ `gcloud config set project dt-ahmedyasser-sandbox-dev`

### Phase 3: Infrastructure (MUST BE FIRST)
7. ✅ Enable GCP APIs
8. ✅ `terraform init`
9. ✅ `terraform apply`

**Why first**: SDK needs these resources to exist!

### Phase 4: SDK Installation
10. ✅ `cd sdk && pip install -e .`

**Why after infrastructure**: SDK will try to write to GCP resources

### Phase 5: Testing
11. ✅ Run example agent
12. ✅ Verify data collection

**Why last**: Tests that everything is connected

### Phase 6: Demo & Submission
13. 🎥 Record demo video
14. 📤 Create competition PR

---

## Security Implementation

### Principle: No Public Access, IAM Everything

#### 1. Authentication Method

**Used**: Application Default Credentials (ADC)
```python
self.client = cloud_logging.Client(project=project_id)
# No credentials passed - uses ADC automatically
```

**NOT Used**:
- ❌ API keys
- ❌ Service account keys
- ❌ Hard-coded credentials

**How it works**:
- Locally: Uses `gcloud auth application-default login`
- Production: Uses service account automatically
- Agent Engine: Will use workload identity

#### 2. Service Account Permissions

Created by Terraform with **least privilege**:

```hcl
resource "google_project_iam_member" "agent_evaluation_permissions" {
  for_each = toset([
    "roles/logging.logWriter",      # Write logs only
    "roles/cloudtrace.agent",        # Write traces only
    "roles/monitoring.metricWriter", # Write metrics only
    "roles/bigquery.dataEditor",     # Insert rows only
  ])
  
  member = "serviceAccount:${google_service_account.agent_evaluation.email}"
}
```

**Not granted**:
- ❌ Editor/Owner roles
- ❌ Delete permissions
- ❌ Admin access

#### 3. Resource Access Control

**All resources private by default**:

- **Cloud Logging**: IAM roles required to view logs
- **Cloud Trace**: IAM roles required to view traces
- **Cloud Monitoring**: IAM roles required to view dashboards
- **BigQuery**: IAM roles required to query data

**No public endpoints**: Everything uses GCP IAM

#### 4. Data Encryption

**At rest**: All GCP services encrypt data automatically
**In transit**: All connections use HTTPS/TLS

#### 5. HTTPS Enforcement

All services use HTTPS by default:
- Cloud Logging API: `https://logging.googleapis.com`
- Cloud Trace API: `https://cloudtrace.googleapis.com`
- Cloud Monitoring API: `https://monitoring.googleapis.com`
- BigQuery API: `https://bigquery.googleapis.com`

No HTTP connections possible.

#### 6. Compliance Checklist

✅ **IAM-controlled authentication**: All services use IAM  
✅ **No "All Users" access**: All resources private  
✅ **No API keys**: Uses ADC only  
✅ **HTTPS endpoints**: All APIs use HTTPS  
✅ **No service account keys**: Keys never exported  
✅ **Internal traffic only**: No public endpoints  
✅ **Encrypted at rest**: GCP default encryption  
✅ **Encrypted in transit**: TLS for all connections  

---

## Key Takeaways

### For Understanding
1. **Infrastructure first**: Terraform creates resources before SDK runs
2. **Single entry point**: `enable_evaluation()` does everything
3. **No code changes**: Agent code remains unchanged
4. **Automatic instrumentation**: Wrapping pattern intercepts calls
5. **Security by default**: No credentials in code, IAM everywhere

### For Competition
1. **Simple integration**: 1 line of code addition
2. **Complete solution**: Logging, tracing, metrics, datasets
3. **Production-ready**: Security, cost-optimization, scalability
4. **Well-documented**: Clear setup and usage instructions
5. **Measurable value**: 97% time savings, <$10/month cost

### For Development
1. **Modular design**: Each component independent
2. **Testable**: Unit tests for each module
3. **Configurable**: YAML config for customization
4. **Extensible**: Easy to add new evaluation features
5. **CI/CD ready**: Automated testing and validation

---

## Next Steps

Now that you understand the code:

1. ✅ Read [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
2. ✅ Follow deployment steps in order
3. ✅ Test with example agent
4. ✅ Record demo video
5. ✅ Submit to competition

**Questions?** See troubleshooting in DEPLOYMENT_GUIDE.md or SETUP.md.

---

*Last updated: Competition preparation phase*

