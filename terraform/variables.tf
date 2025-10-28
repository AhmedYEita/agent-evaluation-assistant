variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "dataset_retention_days" {
  description = "Number of days to retain interaction data in BigQuery"
  type        = number
  default     = 90
}

