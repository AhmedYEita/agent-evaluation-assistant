variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "retention_days" {
  description = "Number of days to retain logs in Cloud Logging"
  type        = number
  default     = 30
}

