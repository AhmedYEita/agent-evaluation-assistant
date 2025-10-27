# Quick Start Guide

Get your agent evaluation infrastructure up and running in 10 minutes.

## Step 1: Prerequisites (2 minutes)

Ensure you have:
- ✅ GCP account with billing enabled
- ✅ `gcloud` CLI installed: `gcloud --version`
- ✅ Terraform installed: `terraform --version`
- ✅ Python 3.10+: `python --version`

```bash
# Authenticate with GCP
gcloud auth login
gcloud auth application-default login

# Set your project
gcloud config set project dt-ahmedyasser-sandbox-dev
```

## Step 2: Deploy Infrastructure (3 minutes)

```bash
# Clone repository
git clone <your-repo-url>
cd agent-evaluation-agent/terraform

# Configure
cat > terraform.tfvars <<EOF
project_id = "$(gcloud config get-value project)"
region     = "us-central1"
EOF

# Deploy (takes ~2-3 minutes)
terraform init
terraform apply -auto-approve
```

**✅ Infrastructure deployed!** You should see output with BigQuery, dashboard, and service account info.

## Step 3: Install SDK (1 minute)

```bash
cd ../sdk
pip install -e .
```

## Step 4: Run Example Agent (2 minutes)

```bash
cd ../examples/simple_adk_agent

# Set project ID
export GCP_PROJECT_ID=$(gcloud config get-value project)

# Run the agent
python agent.py
```

**Try these queries:**
- "What is machine learning?"
- "Explain quantum computing"
- "Write a Python function to sort a list"

## Step 5: View Results (2 minutes)

### View Logs
```bash
gcloud logging read "resource.labels.agent_name=simple-adk-agent" \
  --limit 10 \
  --format json
```

### Open Dashboards
```bash
# Get dashboard URL
cd ../../terraform
terraform output dashboard_url

# Or directly:
open "https://console.cloud.google.com/monitoring/dashboards?project=$(gcloud config get-value project)"
```

### Export Dataset
```bash
agent-eval export-dataset \
  --project-id $(gcloud config get-value project) \
  --agent-name simple-adk-agent \
  --output my-dataset.json \
  --limit 10

# View the dataset
cat my-dataset.json | jq '.'
```

## Step 6: Integrate with Your Agent (1 minute)

```python
from google.genai.adk import Agent
from agent_evaluation_sdk import enable_evaluation

# Your existing agent code
agent = Agent(
    model="gemini-2.0-flash-exp",
    system_instruction="You are a helpful assistant",
)

# Add this ONE line - that's it!
enable_evaluation(
    agent=agent,
    project_id="dt-ahmedyasser-sandbox-dev",
    agent_name="your-agent-name"
)

# Use your agent normally - evaluation happens automatically!
response = agent.generate_content("Hello!")
```

## What You Just Built

🎉 **Congratulations!** You now have:

- ✅ **Production-grade logging** to Cloud Logging
- ✅ **Performance tracing** in Cloud Trace
- ✅ **Real-time metrics** and dashboards
- ✅ **Automated dataset collection** for evaluation
- ✅ **Alert policies** for errors and latency
- ✅ **Infrastructure-as-Code** for reproducibility

## Next Steps

### Explore Advanced Features

```bash
# Custom configuration
cd examples/simple_adk_agent
python agent_with_config.py

# View comprehensive docs
cd ../../docs
cat README.md
```

### Customize Your Setup

1. **Adjust sampling rates** (reduce costs):
   ```yaml
   # eval_config.yaml
   tracing:
     sample_rate: 0.1  # Trace 10% of requests
   dataset:
     sample_rate: 0.05  # Collect 5% for dataset
   ```

2. **Set up notifications**:
   - Add email/Slack to alert policies
   - Configure in Cloud Monitoring console

3. **Create evaluation datasets**:
   ```bash
   # Collect diverse examples
   # Review and curate
   # Use for benchmarking
   ```

### Deploy to Production

1. Update Terraform for prod settings
2. Use service account authentication
3. Configure CI/CD for your agent
4. Set up monitoring dashboards
5. Review costs and optimize sampling

## Troubleshooting

### "Permission Denied"
```bash
# Add required roles
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
  --member="user:$(gcloud config get-value account)" \
  --role="roles/editor"
```

### "Module Not Found"
```bash
# Reinstall SDK
cd sdk
pip install -e .
```

### No Logs Appearing
```bash
# Check authentication
gcloud auth application-default print-access-token

# Verify project
echo $GCP_PROJECT_ID
gcloud config get-value project
```

## Cost Estimate

For **10,000 agent requests/day**:

| Service | Monthly Cost |
|---------|-------------|
| Cloud Logging | $1-5 |
| Cloud Trace | $0-2 |
| Cloud Monitoring | $0-1 |
| BigQuery | $1-5 |
| **Total** | **~$5-15** |

💡 **Tip:** Use sampling to reduce costs in production!

## Resources

- 📖 [Full Documentation](./README.md)
- 🔧 [SDK Reference](./sdk-reference.md)
- 🏗️ [Infrastructure Guide](./infrastructure.md)
- 💬 [GitHub Issues](https://github.com/your-repo/issues)

---

**Questions?** Open an issue or check the docs!

**Ready for more?** Read the [full documentation](./README.md) to learn about advanced features, best practices, and production deployment.

