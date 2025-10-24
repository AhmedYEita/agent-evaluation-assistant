variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "dataset_retention_days" {
  description = "Number of days to retain data"
  type        = number
  default     = 90
}

