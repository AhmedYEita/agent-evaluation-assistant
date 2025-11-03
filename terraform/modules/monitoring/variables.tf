variable "error_rate_threshold" {
  description = "Error rate threshold (0-1) that triggers an alert"
  type        = number
  default     = 0.05 # 5%
}

variable "latency_threshold_ms" {
  description = "Latency threshold in milliseconds that triggers an alert"
  type        = number
  default     = 5000 # 5 seconds
}

variable "alert_duration" {
  description = "Duration the condition must be true before alerting"
  type        = string
  default     = "300s" # 5 minutes
}

variable "alert_auto_close" {
  description = "Duration after which alerts auto-close if condition resolves"
  type        = string
  default     = "1800s" # 30 minutes
}

variable "metric_alignment_period" {
  description = "Time period for aggregating metric data"
  type        = string
  default     = "60s" # 1 minute
}

