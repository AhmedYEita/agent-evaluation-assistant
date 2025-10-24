output "bigquery_dataset_id" {
  description = "BigQuery dataset ID for agent evaluation data"
  value       = module.storage.dataset_id
}

output "bigquery_table_id" {
  description = "BigQuery table ID for agent interactions"
  value       = module.storage.table_id
}

output "service_account_email" {
  description = "Service account email for agent evaluation"
  value       = google_service_account.agent_evaluation.email
}

output "dashboard_url" {
  description = "URL to Cloud Monitoring dashboards"
  value       = "https://console.cloud.google.com/monitoring/dashboards?project=${var.project_id}"
}

output "logging_url" {
  description = "URL to Cloud Logging"
  value       = "https://console.cloud.google.com/logs?project=${var.project_id}"
}

output "trace_url" {
  description = "URL to Cloud Trace"
  value       = "https://console.cloud.google.com/traces?project=${var.project_id}"
}

output "setup_complete" {
  description = "Setup instructions"
  value       = <<-EOT
  
  ✅ Agent Evaluation Infrastructure deployed successfully!
  
  Next steps:
  
  1. Install the SDK in your agent project:
     pip install -e /path/to/sdk
  
  2. Add to your agent code:
     from agent_evaluation_sdk import enable_evaluation
     
     enable_evaluation(
         agent=your_agent,
         project_id="${var.project_id}",
         agent_name="your-agent-name"
     )
  
  3. View results:
     - Logs: ${self.logging_url}
     - Traces: ${self.trace_url}
     - Dashboards: ${self.dashboard_url}
  
  Service Account: ${google_service_account.agent_evaluation.email}
  Dataset: ${module.storage.dataset_id}
  
  EOT
}

