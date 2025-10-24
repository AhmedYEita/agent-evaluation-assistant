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

variable "enable_trace_sampling" {
  description = "Enable sampling for Cloud Trace (reduces costs)"
  type        = bool
  default     = true
}

variable "trace_sample_rate" {
  description = "Sampling rate for traces (0.0 to 1.0)"
  type        = number
  default     = 1.0
}

