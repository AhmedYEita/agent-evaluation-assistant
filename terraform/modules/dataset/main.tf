# BigQuery dataset for agent evaluation data
resource "google_bigquery_dataset" "agent_evaluation" {
  dataset_id    = "agent_evaluation"
  friendly_name = "Agent Evaluation Testing Data"
  description   = "Storage for agent testing datasets"
  location      = var.region

  labels = {
    purpose = "agent-evaluation"
  }
}

