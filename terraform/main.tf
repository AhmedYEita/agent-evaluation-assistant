terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "cloudtrace.googleapis.com",
    "bigquery.googleapis.com",
    "aiplatform.googleapis.com",
  ])

  service            = each.key
  disable_on_destroy = false
}

# Cloud Logging setup
module "logging" {
  source = "./modules/logging"

  project_id = var.project_id
  region     = var.region

  depends_on = [google_project_service.required_apis]
}

# Cloud Monitoring setup (dashboards and metrics)
module "monitoring" {
  source = "./modules/monitoring"

  depends_on = [google_project_service.required_apis]
}

# BigQuery dataset for evaluation data
module "dataset" {
  source = "./modules/dataset"

  project_id = var.project_id
  region     = var.region

  depends_on = [google_project_service.required_apis]
}

# IAM and Service Accounts
resource "google_service_account" "agent_evaluation" {
  account_id   = "agent-evaluation-sa"
  display_name = "Agent Evaluation Service Account"
  description  = "Service account for agents using the evaluation SDK"
}

# Grant necessary permissions
resource "google_project_iam_member" "agent_evaluation_permissions" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/cloudtrace.agent",
    "roles/monitoring.metricWriter",
    "roles/bigquery.dataEditor",
    "roles/aiplatform.user",
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.agent_evaluation.email}"
}

