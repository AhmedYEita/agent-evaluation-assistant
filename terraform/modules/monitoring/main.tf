# Create a monitoring dashboard for agent metrics
resource "google_monitoring_dashboard" "agent_evaluation" {
  dashboard_json = jsonencode({
    displayName = "Agent Evaluation Dashboard"
    mosaicLayout = {
      columns = 12
      tiles = [
        {
          width  = 6
          height = 4
          widget = {
            title = "Agent Response Latency"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"custom.googleapis.com/agent/latency\""
                    aggregation = {
                      alignmentPeriod  = var.metric_alignment_period
                      perSeriesAligner = "ALIGN_MEAN"
                    }
                  }
                }
                plotType = "LINE"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Latency (ms)"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          width  = 6
          height = 4
          xPos   = 6
          widget = {
            title = "Token Usage"
            xyChart = {
              dataSets = [
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "metric.type=\"custom.googleapis.com/agent/tokens/input\""
                      aggregation = {
                        alignmentPeriod  = var.metric_alignment_period
                        perSeriesAligner = "ALIGN_MEAN"
                      }
                    }
                  }
                  plotType   = "LINE"
                  targetAxis = "Y1"
                },
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "metric.type=\"custom.googleapis.com/agent/tokens/output\""
                      aggregation = {
                        alignmentPeriod  = var.metric_alignment_period
                        perSeriesAligner = "ALIGN_MEAN"
                      }
                    }
                  }
                  plotType   = "LINE"
                  targetAxis = "Y1"
                }
              ]
              yAxis = {
                label = "Tokens"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          width  = 6
          height = 4
          yPos   = 4
          widget = {
            title = "Success Rate"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"custom.googleapis.com/agent/success\""
                    aggregation = {
                      alignmentPeriod    = var.metric_alignment_period
                      perSeriesAligner   = "ALIGN_RATE"
                      crossSeriesReducer = "REDUCE_SUM"
                    }
                  }
                }
                plotType = "LINE"
              }]
            }
          }
        },
        {
          width  = 6
          height = 4
          xPos   = 6
          yPos   = 4
          widget = {
            title = "Error Rate by Type"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"custom.googleapis.com/agent/errors\""
                    aggregation = {
                      alignmentPeriod    = var.metric_alignment_period
                      perSeriesAligner   = "ALIGN_RATE"
                      crossSeriesReducer = "REDUCE_SUM"
                      groupByFields      = ["metric.label.error_type"]
                    }
                  }
                }
                plotType = "STACKED_AREA"
              }]
            }
          }
        }
      ]
    }
  })
}

# Alert policies commented out - metrics must exist before creating alerts
# Uncomment and re-apply after running the agent at least once to create the custom metrics

# # Alert policy for high error rates
# resource "google_monitoring_alert_policy" "high_error_rate" {
#   display_name = "Agent Evaluation - High Error Rate"
#   combiner     = "OR"
#
#   conditions {
#     display_name = "Error rate above 5%"
#
#     condition_threshold {
#       filter          = "metric.type=\"custom.googleapis.com/agent/errors\" resource.type=\"global\""
#       duration        = var.alert_duration
#       comparison      = "COMPARISON_GT"
#       threshold_value = var.error_rate_threshold
#
#       aggregations {
#         alignment_period   = var.metric_alignment_period
#         per_series_aligner = "ALIGN_RATE"
#       }
#     }
#   }
#
#   documentation {
#     content   = "Agent error rate has exceeded 5%. Check Cloud Logging for details."
#     mime_type = "text/markdown"
#   }
#
#   notification_channels = []
#
#   alert_strategy {
#     auto_close = var.alert_auto_close
#   }
# }
#
# # Alert policy for high latency
# resource "google_monitoring_alert_policy" "high_latency" {
#   display_name = "Agent Evaluation - High Latency"
#   combiner     = "OR"
#
#   conditions {
#     display_name = "Latency above 5 seconds"
#
#     condition_threshold {
#       filter          = "metric.type=\"custom.googleapis.com/agent/latency\" resource.type=\"global\""
#       duration        = var.alert_duration
#       comparison      = "COMPARISON_GT"
#       threshold_value = var.latency_threshold_ms
#
#       aggregations {
#         alignment_period   = var.metric_alignment_period
#         per_series_aligner = "ALIGN_MEAN"
#       }
#     }
#   }
#
#   documentation {
#     content   = "Agent response latency has exceeded 5 seconds. Check Cloud Trace for performance bottlenecks."
#     mime_type = "text/markdown"
#   }
#
#   notification_channels = []
#
#   alert_strategy {
#     auto_close = var.alert_auto_close
#   }
# }
