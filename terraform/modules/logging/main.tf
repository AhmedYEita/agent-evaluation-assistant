# Cloud Logging configuration for agent evaluation

# Log bucket for agent evaluation logs
resource "google_logging_project_bucket_config" "agent_evaluation" {
  project        = var.project_id
  location       = var.region
  retention_days = 30
  bucket_id      = "agent-evaluation-logs"
  
  description = "Log bucket for agent evaluation data"
}

# Log sink to route agent logs to BigQuery (optional - for advanced analytics)
# This can be enabled later if needed

