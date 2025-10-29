# BigQuery dataset and tables for agent evaluation data

resource "google_bigquery_dataset" "agent_evaluation" {
  dataset_id    = "agent_evaluation"
  friendly_name = "Agent Evaluation Testing Data"
  description   = "Storage for agent testing datasets"
  location      = var.region

  labels = {
    purpose = "agent-evaluation"
  }
}

# Note: Individual agent tables will be created automatically by the SDK
# when enable_evaluation() is called. This provides flexibility for
# multiple agents without pre-defining all tables.

# Create a view for aggregated metrics across all agents (optional)
resource "google_bigquery_table" "all_agents_view" {
  dataset_id = google_bigquery_dataset.agent_evaluation.dataset_id
  table_id   = "all_agents_interactions"

  view {
    query = <<-SQL
      SELECT 
        interaction_id,
        agent_name,
        timestamp,
        input,
        output,
        metadata,
        trajectory
      FROM `${var.project_id}.${google_bigquery_dataset.agent_evaluation.dataset_id}.*`
      WHERE _TABLE_SUFFIX != 'all_agents_interactions'
      ORDER BY timestamp DESC
    SQL

    use_legacy_sql = false
  }
}

