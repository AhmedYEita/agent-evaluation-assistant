# Log bucket for agent evaluation logs
resource "google_logging_project_bucket_config" "agent_evaluation" {
  project        = var.project_id
  location       = var.region
  retention_days = var.retention_days
  bucket_id      = "agent-evaluation-logs"

  description = "Log bucket for agent evaluation data"
}

