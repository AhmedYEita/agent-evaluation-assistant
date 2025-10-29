# Terraform Configuration for Agent Evaluation Infrastructure

This directory contains Infrastructure-as-Code (IaC) for deploying the complete GCP evaluation stack.

## What Gets Deployed

- **Cloud Logging**: Structured logging with custom log sinks
- **Cloud Monitoring**: Dashboards, alerts, and custom metrics
- **Cloud Trace**: Performance tracing configuration
- **BigQuery**: Dataset storage for agent interactions
- **IAM**: Service accounts and permissions

## Prerequisites

1. GCP Project with billing enabled
2. Terraform >= 1.5.0
3. GCP CLI (`gcloud`) authenticated
4. Required APIs enabled (done automatically by Terraform)

## Quick Start

```bash
# 1. Initialize Terraform
terraform init

# 2. Create terraform.tfvars with your settings
cat > terraform.tfvars <<EOF
project_id = "gcp-project-id"
region     = "us-central1"
EOF

# 3. Review the plan
terraform plan

# 4. Deploy
terraform apply
```

## Configuration

### Required Variables

- `project_id`: Your GCP project ID
- `region`: GCP region (default: us-central1)

### Optional Variables

See `variables.tf` for all available options.

## Outputs

After deployment, Terraform will output:

- BigQuery dataset and table names
- Dashboard URLs
- Service account emails

## Usage

Once deployed, agents using the SDK will automatically connect to this infrastructure.

## Cleanup

```bash
terraform destroy
```

**Note**: This will delete all evaluation data. Export datasets before destroying!

