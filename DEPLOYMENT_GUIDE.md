# Step-by-Step Deployment Guide

This guide walks you through deploying the Agent Evaluation infrastructure to your GCP project **in the correct order** before recording your demo video or running any tests.

## 📋 Prerequisites

Before you begin, ensure you have:

- [ ] Access to `dt-ahmedyasser-sandbox-dev` GCP project
- [ ] Billing enabled on the project
- [ ] Editor or Owner role on the project
- [ ] Tools installed:
  - `gcloud` CLI
  - `terraform` (>= 1.5.0)
  - `python` (>= 3.12)
  - `git`

## 🚀 Deployment Steps

Follow these steps **in order**. Do not skip any steps.

---

### Step 1: Clone and Navigate to Repository

```bash
# If not already cloned
cd ~/Documents/GitHub
git clone <your-repo-url> agent-evaluation-agent
cd agent-evaluation-agent
```

**Verification**: 
```bash
ls -la
# You should see: README.md, SETUP.md, terraform/, sdk/, examples/
```

---

### Step 2: Authenticate with GCP

```bash
# Authenticate your user account
gcloud auth login

# Set application default credentials (for Terraform and SDK)
gcloud auth application-default login

# Set the active project
gcloud config set project dt-ahmedyasser-sandbox-dev

# Verify authentication
gcloud config get-value account
gcloud config get-value project
```

**Expected Output**:
```
Your active configuration is: [default]
Account: your-email@datatonic.com
Project: dt-ahmedyasser-sandbox-dev
```

---

### Step 3: Enable Required GCP APIs

**Why**: Terraform needs these APIs enabled before it can create resources.

```bash
# Enable all required APIs (takes 1-2 minutes)
gcloud services enable \
  logging.googleapis.com \
  monitoring.googleapis.com \
  cloudtrace.googleapis.com \
  bigquery.googleapis.com \
  aiplatform.googleapis.com \
  compute.googleapis.com
```

**Verification**:
```bash
gcloud services list --enabled | grep -E "(logging|monitoring|cloudtrace|bigquery|aiplatform)"
```

You should see all 5 services listed.

---

### Step 4: Grant Required IAM Permissions

**Why**: Ensure you have necessary permissions to deploy infrastructure.

```bash
# Get your email
USER_EMAIL=$(gcloud config get-value account)

# Grant permissions (if not already granted)
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

**Note**: If you already have these permissions, the commands will succeed silently.

---

### Step 5: Deploy Infrastructure with Terraform

**Why**: This creates all GCP resources (logging, monitoring, BigQuery, IAM).

```bash
# Navigate to terraform directory
cd terraform

# Initialize Terraform (downloads providers)
terraform init
```

**Expected Output**:
```
Terraform has been successfully initialized!
```

**Create terraform.tfvars**:
```bash
cat > terraform.tfvars <<EOF
project_id = "dt-ahmedyasser-sandbox-dev"
region     = "us-central1"
EOF
```

**Review the plan**:
```bash
terraform plan
```

Read through the output. You should see:
- BigQuery dataset creation
- Logging bucket configuration
- Monitoring dashboard creation
- Alert policies creation
- Service account creation with IAM bindings

**Deploy** (takes 2-3 minutes):
```bash
terraform apply
```

Type `yes` when prompted.

**Expected Output**:
```
Apply complete! Resources: X added, 0 changed, 0 destroyed.

Outputs:

bigquery_dataset = "dt-ahmedyasser-sandbox-dev.agent_evaluation"
dashboard_url = "https://console.cloud.google.com/monitoring/dashboards?project=dt-ahmedyasser-sandbox-dev"
logs_url = "https://console.cloud.google.com/logs?project=dt-ahmedyasser-sandbox-dev"
...
```

**Verification**:
```bash
# Check BigQuery dataset
bq ls --project_id=dt-ahmedyasser-sandbox-dev | grep agent_evaluation

# Check service account
gcloud iam service-accounts list --project=dt-ahmedyasser-sandbox-dev | grep agent-evaluation
```

---

### Step 6: Install the SDK

**Why**: The SDK needs to be installed before you can use it in agents.

```bash
# Navigate to SDK directory
cd ../sdk

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install SDK in development mode
pip install -e .
```

**Expected Output**:
```
Successfully installed agent-evaluation-sdk
```

**Verification**:
```bash
# Test import
python -c "from agent_evaluation_sdk import enable_evaluation; print('✅ SDK installed successfully')"

# Check CLI
agent-eval --help
```

---

### Step 7: Test with Example Agent

**Why**: Verify end-to-end functionality before recording demo.

```bash
# Navigate to examples
cd ../examples/simple_adk_agent

# Install example dependencies
pip install -r requirements.txt
```

**Set environment variable**:
```bash
export GCP_PROJECT_ID="dt-ahmedyasser-sandbox-dev"
```

**Run the example agent**:
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

**Test with a few queries**:
```
You: What is Python?
Agent: [Response from Gemini]

You: Explain machine learning
Agent: [Response from Gemini]

You: quit
```

---

### Step 8: Verify Data Collection

**Why**: Confirm that all evaluation data is being captured correctly.

Wait 1-2 minutes for data to propagate, then:

#### Check Cloud Logging

```bash
# View recent logs
gcloud logging read "resource.labels.agent_name=simple-adk-agent" \
  --limit 5 \
  --format json \
  --project dt-ahmedyasser-sandbox-dev
```

**Expected**: JSON logs with interaction_id, input, output, duration_ms

#### Check Cloud Trace

```bash
# Open in browser
open "https://console.cloud.google.com/traces?project=dt-ahmedyasser-sandbox-dev"
```

**Expected**: Trace entries showing agent.generate_content spans

#### Check Cloud Monitoring

```bash
# Open dashboard
open "https://console.cloud.google.com/monitoring/dashboards?project=dt-ahmedyasser-sandbox-dev"
```

**Expected**: "Agent Evaluation Dashboard" with latency, token usage, success rate charts

#### Check BigQuery

```bash
# Query collected data
bq query --use_legacy_sql=false --project_id=dt-ahmedyasser-sandbox-dev \
'SELECT 
  interaction_id,
  agent_name,
  timestamp,
  JSON_VALUE(metadata, "$.duration_ms") as duration_ms
FROM `agent_evaluation.simple_adk_agent_interactions`
ORDER BY timestamp DESC
LIMIT 5'
```

**Expected**: Table showing your test interactions

---

### Step 9: Export Dataset (Optional)

```bash
# Export dataset to JSON file
agent-eval export-dataset \
  --project-id dt-ahmedyasser-sandbox-dev \
  --agent-name simple-adk-agent \
  --output dataset.json \
  --limit 100

# View the file
head dataset.json
```

---

## ✅ Post-Deployment Checklist

After completing all steps, verify:

- [ ] Terraform apply succeeded without errors
- [ ] SDK installed and imports successfully
- [ ] Example agent runs without errors
- [ ] Logs appear in Cloud Logging
- [ ] Traces appear in Cloud Trace
- [ ] Dashboard shows metrics in Cloud Monitoring
- [ ] Data collected in BigQuery
- [ ] Dataset export works

## 🎥 Ready for Demo Video

Once all checks pass, you're ready to record your demo video!

### Demo Recording Tips

1. **Clean up your terminal**: Clear history, set a clean prompt
2. **Close unnecessary windows**: Only show relevant tabs
3. **Use a clean project state**: Consider running `terraform destroy` then `terraform apply` for a fresh demo
4. **Prepare test queries**: Have 2-3 interesting questions ready for the agent
5. **Open GCP Console tabs**: Pre-open Cloud Logging, Trace, Monitoring, BigQuery in separate tabs
6. **Test run**: Do a complete dry run before recording

### Demo Script

Follow this sequence:

1. **Introduction** (30s): Explain the problem and solution
2. **Deploy Infrastructure** (1min): Show `terraform apply` output
3. **Show Code** (1min): Display the 1-line integration
4. **Run Agent** (1min): Execute example with 2-3 queries
5. **Show Results** (2min): Navigate through Logging, Trace, Monitoring, BigQuery
6. **Conclusion** (30s): Summarize value and time savings

---

## 🔧 Troubleshooting

### Issue: "Permission Denied" errors

**Solution**:
```bash
# Re-authenticate
gcloud auth application-default login

# Check permissions
gcloud projects get-iam-policy dt-ahmedyasser-sandbox-dev \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:$(gcloud config get-value account)"
```

### Issue: "API not enabled" errors

**Solution**:
```bash
# Re-run API enablement
gcloud services enable \
  logging.googleapis.com \
  monitoring.googleapis.com \
  cloudtrace.googleapis.com \
  bigquery.googleapis.com \
  aiplatform.googleapis.com
```

### Issue: SDK import fails

**Solution**:
```bash
# Reinstall SDK
cd sdk
pip uninstall agent-evaluation-sdk -y
pip install -e .
```

### Issue: No data in BigQuery

**Solution**:
- Wait 2-3 minutes for data to propagate
- Check that agent ran successfully
- Verify dataset.sample_rate > 0 in config
- Check Cloud Logging for any errors

### Issue: Terraform state conflicts

**Solution**:
```bash
cd terraform
# If safe to do so:
rm -rf .terraform terraform.tfstate*
terraform init
terraform plan
```

---

## 🧹 Cleanup (After Competition)

To remove all resources and stop charges:

```bash
cd terraform
terraform destroy -var="project_id=dt-ahmedyasser-sandbox-dev"
```

Type `yes` when prompted.

**Note**: This will delete all evaluation data. Export any datasets you want to keep first!

---

## 📊 Cost Monitoring

Monitor costs during deployment:

```bash
# View current costs
gcloud billing projects describe dt-ahmedyasser-sandbox-dev

# Set up budget alert (optional)
open "https://console.cloud.google.com/billing/budgets?project=dt-ahmedyasser-sandbox-dev"
```

**Expected costs**: ~$10/month for typical usage (well under £100/month budget).

---

## 🎯 Next Steps

1. ✅ Complete all deployment steps above
2. ✅ Verify everything works end-to-end
3. 🎥 Record demo video (3-5 minutes)
4. 📤 Upload video to approved platform
5. 📝 Add video link to README.md
6. 🚀 Create PR to competition repository

---

## 📞 Support

- **Documentation**: See [SETUP.md](./SETUP.md) for detailed setup info
- **Troubleshooting**: See above section or SETUP.md
- **Competition Questions**: Contact competition organizers
- **GCP Issues**: Check project permissions and quotas

---

**Good luck with your deployment and demo!** 🚀

