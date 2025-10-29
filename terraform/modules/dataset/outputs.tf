output "dataset_id" {
  description = "BigQuery dataset ID"
  value       = google_bigquery_dataset.agent_evaluation.dataset_id
}

output "dataset_full_id" {
  description = "Full BigQuery dataset ID (project.dataset)"
  value       = "${var.project_id}.${google_bigquery_dataset.agent_evaluation.dataset_id}"
}

output "table_id" {
  description = "Pattern for agent interaction tables"
  value       = "${google_bigquery_dataset.agent_evaluation.dataset_id}.<agent_name>_interactions"
}

