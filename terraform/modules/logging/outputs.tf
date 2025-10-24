output "log_bucket_id" {
  description = "ID of the log bucket for agent evaluation"
  value       = google_logging_project_bucket_config.agent_evaluation.id
}

