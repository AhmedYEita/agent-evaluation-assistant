# Setup Instructions

Complete guide to setting up your development environment and deploying the agent evaluation infrastructure.

## Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [GCP Setup](#gcp-setup)
3. [Infrastructure Deployment](#infrastructure-deployment)
4. [SDK Installation](#sdk-installation)
5. [Verification](#verification)
6. [Next Steps](#next-steps)

## Local Development Setup

### Install Required Tools

#### 1. Python 3.12+

```bash
# macOS
brew install python@3.12

# Ubuntu/Debian
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip

# Windows
# Download from https://www.python.org/downloads/
```

#### 2. Terraform

```bash
# macOS
brew install terraform

# Ubuntu/Debian
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# Windows
# Download from https://www.terraform.io/downloads
```

#### 3. GCloud CLI

```bash
# macOS
brew install google-cloud-sdk

# Ubuntu/Debian
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Windows
# Download from https://cloud.google.com/sdk/docs/install
```

### Clone Repository

```bash
git clone https://github.com/yourusername/agent-evaluation-agent.git
cd agent-evaluation-agent
```

## GCP Setup

### 1. Create or Select Project

```bash
# List existing projects
gcloud projects list

# Set active project (project already created)
gcloud config set project dt-ahmedyasser-sandbox-dev
```

### 2. Enable Billing

```bash
# Billing is already configured for dt-ahmedyasser-sandbox-dev
# No action needed
```

### 3. Authenticate

```bash
# Authenticate gcloud
gcloud auth login

# Set application default credentials
gcloud auth application-default login
```

### 4. Enable Required APIs

```bash
gcloud services enable \
  logging.googleapis.com \
  monitoring.googleapis.com \
  cloudtrace.googleapis.com \
  bigquery.googleapis.com \
  aiplatform.googleapis.com
```

### 5. Grant Permissions

```bash
# Get your user email
USER_EMAIL=$(gcloud config get-value account)

# Grant required roles (if not already granted)
gcloud projects add-iam-policy-binding dt-ahmedyasser-sandbox-dev \
  --member="user:$USER_EMAIL" \
  --role="roles/editor"

gcloud projects add-iam-policy-binding dt-ahmedyasser-sandbox-dev \
  --member="user:$USER_EMAIL" \
  --role="roles/logging.admin"

gcloud projects add-iam-policy-binding dt-ahmedyasser-sandbox-dev \
  --member="user:$USER_EMAIL" \
  --role="roles/monitoring.admin"
```

## Infrastructure Deployment

### 1. Configure Terraform

```bash
cd terraform

# Create terraform.tfvars
cat > terraform.tfvars <<EOF
project_id = "$(gcloud config get-value project)"
region     = "us-central1"
EOF
```

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Review Plan

```bash
terraform plan
```

### 4. Deploy Infrastructure

```bash
# Deploy (takes 2-3 minutes)
terraform apply

# Type 'yes' when prompted
```

### 5. Save Outputs

```bash
# View outputs
terraform output

# Save to file (optional)
terraform output -json > ../infrastructure-outputs.json
```

## SDK Installation

### Option 1: Development Installation (Recommended)

```bash
cd ../sdk

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### Option 2: Production Installation

```bash
pip install agent-evaluation-sdk
```

## Verification

### 1. Verify Terraform Deployment

```bash
cd terraform

# Check resources were created
gcloud logging buckets list
gcloud monitoring dashboards list
bq ls agent_evaluation
```

### 2. Verify SDK Installation

```bash
# Test import
python -c "from agent_evaluation_sdk import enable_evaluation; print('✅ SDK installed')"

# Check CLI
agent-eval --help
```

### 3. Run Example Agent

```bash
cd ../examples/simple_adk_agent

# Install example dependencies
pip install -r requirements.txt

# Set project ID
export GCP_PROJECT_ID=$(gcloud config get-value project)

# Run example
python agent.py
```

**Try these queries:**
- "What is Python?"
- "Explain machine learning"
- Type 'quit' to exit

### 4. Verify Data Collection

```bash
# Wait 1-2 minutes for data to propagate, then:

# Check logs
gcloud logging read "resource.labels.agent_name=simple-adk-agent" \
  --limit 5 \
  --format json

# Check BigQuery
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) as count FROM `agent_evaluation.simple_adk_agent_interactions`'

# View dashboard
open "https://console.cloud.google.com/monitoring/dashboards?project=$(gcloud config get-value project)"
```

## Next Steps

### 1. Integrate with Your Agent

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
    agent_name="your-agent-name"
)
```

### 2. Configure Sampling (Optional)

Create `eval_config.yaml`:

```yaml
logging:
  level: "INFO"
tracing:
  sample_rate: 0.1  # Trace 10% of requests
dataset:
  sample_rate: 0.05  # Collect 5% for dataset
```

### 3. Set Up CI/CD (Optional)

```bash
# For GitHub Actions
# Add secrets in repository settings:
# - GCP_PROJECT_ID
# - WIF_PROVIDER (Workload Identity Federation)
# - WIF_SERVICE_ACCOUNT

# Workflows are already configured in .github/workflows/
```

### 4. Configure Alerts (Optional)

```bash
# Add notification channels in Cloud Console:
# https://console.cloud.google.com/monitoring/alerting/notifications

# Or via gcloud:
gcloud alpha monitoring channels create \
  --display-name="Email" \
  --type=email \
  --channel-labels=email_address=your-email@example.com
```

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

## Resources

- 📖 [Full Documentation](./docs/README.md)
- 🚀 [Quick Start Guide](./docs/QUICKSTART.md)
- 💬 [GitHub Issues](https://github.com/yourusername/agent-evaluation-agent/issues)
- 🔧 [Contributing Guide](./CONTRIBUTING.md)

## Support

Need help? 

1. Check [Troubleshooting](#troubleshooting) section
2. Search [existing issues](https://github.com/yourusername/agent-evaluation-agent/issues)
3. Open a [new issue](https://github.com/yourusername/agent-evaluation-agent/issues/new)

---

**Ready to go?** Continue to the [Quick Start Guide](./docs/QUICKSTART.md) or [Full Documentation](./docs/README.md).

