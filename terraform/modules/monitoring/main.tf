# Cloud Monitoring configuration for agent evaluation

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
                      alignmentPeriod  = "60s"
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
                        alignmentPeriod  = "60s"
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
                        alignmentPeriod  = "60s"
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
                      alignmentPeriod    = "60s"
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
                      alignmentPeriod    = "60s"
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

# Alert policy for high error rates
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "Agent Evaluation - High Error Rate"
  combiner     = "OR"
  
  conditions {
    display_name = "Error rate above 5%"
    
    condition_threshold {
      filter          = "metric.type=\"custom.googleapis.com/agent/errors\" resource.type=\"global\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  documentation {
    content   = "Agent error rate has exceeded 5%. Check Cloud Logging for details."
    mime_type = "text/markdown"
  }
  
  notification_channels = []
  
  alert_strategy {
    auto_close = "1800s"
  }
}

# Alert policy for high latency
resource "google_monitoring_alert_policy" "high_latency" {
  display_name = "Agent Evaluation - High Latency"
  combiner     = "OR"
  
  conditions {
    display_name = "Latency above 5 seconds"
    
    condition_threshold {
      filter          = "metric.type=\"custom.googleapis.com/agent/latency\" resource.type=\"global\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5000  # 5 seconds in milliseconds
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  documentation {
    content   = "Agent response latency has exceeded 5 seconds. Check Cloud Trace for performance bottlenecks."
    mime_type = "text/markdown"
  }
  
  notification_channels = []
  
  alert_strategy {
    auto_close = "1800s"
  }
}

