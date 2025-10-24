output "dashboard_id" {
  description = "Monitoring dashboard ID"
  value       = google_monitoring_dashboard.agent_evaluation.id
}

output "dashboard_name" {
  description = "Monitoring dashboard name"
  value       = google_monitoring_dashboard.agent_evaluation.dashboard_json
}

