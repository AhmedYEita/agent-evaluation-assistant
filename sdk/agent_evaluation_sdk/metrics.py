"""
Cloud Monitoring integration for agent evaluation.
"""

import time
from typing import Any, Dict, Optional

from google.api import metric_pb2 as ga_metric
from google.cloud import monitoring_v3


class CloudMetrics:
    """Wrapper for Cloud Monitoring to track agent metrics."""

    def __init__(self, project_id: str, agent_name: str):
        """Initialize Cloud Metrics.

        Args:
            project_id: GCP project ID
            agent_name: Name of the agent
        """
        self.project_id = project_id
        self.agent_name = agent_name

        # Initialize Cloud Monitoring client
        self.client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{project_id}"

        # Metric type prefix
        self.metric_prefix = "custom.googleapis.com/agent"

    def record_latency(self, duration_ms: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record agent response latency.

        Args:
            duration_ms: Duration in milliseconds
            labels: Additional labels for the metric
        """
        self._write_metric(
            metric_type=f"{self.metric_prefix}/latency",
            value=duration_ms,
            labels=labels or {},
            value_type=ga_metric.MetricDescriptor.ValueType.DOUBLE,
            metric_kind=ga_metric.MetricDescriptor.MetricKind.GAUGE,
        )

    def record_token_count(
        self, input_tokens: int, output_tokens: int, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record token usage for the interaction.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            labels: Additional labels for the metric
        """
        base_labels = labels or {}

        # Record input tokens
        self._write_metric(
            metric_type=f"{self.metric_prefix}/tokens/input",
            value=input_tokens,
            labels={**base_labels, "type": "input"},
            value_type=ga_metric.MetricDescriptor.ValueType.INT64,
            metric_kind=ga_metric.MetricDescriptor.MetricKind.GAUGE,
        )

        # Record output tokens
        self._write_metric(
            metric_type=f"{self.metric_prefix}/tokens/output",
            value=output_tokens,
            labels={**base_labels, "type": "output"},
            value_type=ga_metric.MetricDescriptor.ValueType.INT64,
            metric_kind=ga_metric.MetricDescriptor.MetricKind.GAUGE,
        )

    def record_error(self, error_type: str, labels: Optional[Dict[str, str]] = None) -> None:
        """Record an error occurrence.

        Args:
            error_type: Type/category of error
            labels: Additional labels for the metric
        """
        self._write_metric(
            metric_type=f"{self.metric_prefix}/errors",
            value=1,
            labels={**(labels or {}), "error_type": error_type},
            value_type=ga_metric.MetricDescriptor.ValueType.INT64,
            metric_kind=ga_metric.MetricDescriptor.MetricKind.GAUGE,
        )

    def record_success(self, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a successful interaction.

        Args:
            labels: Additional labels for the metric
        """
        self._write_metric(
            metric_type=f"{self.metric_prefix}/success",
            value=1,
            labels=labels or {},
            value_type=ga_metric.MetricDescriptor.ValueType.INT64,
            metric_kind=ga_metric.MetricDescriptor.MetricKind.GAUGE,
        )

    def record_custom_metric(
        self,
        metric_name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a custom metric.

        Args:
            metric_name: Name of the custom metric
            value: Metric value
            labels: Additional labels for the metric
        """
        self._write_metric(
            metric_type=f"{self.metric_prefix}/custom/{metric_name}",
            value=value,
            labels=labels or {},
            value_type=ga_metric.MetricDescriptor.ValueType.DOUBLE,
            metric_kind=ga_metric.MetricDescriptor.MetricKind.GAUGE,
        )

    def _write_metric(
        self,
        metric_type: str,
        value: Any,
        labels: Dict[str, str],
        value_type: ga_metric.MetricDescriptor.ValueType,
        metric_kind: ga_metric.MetricDescriptor.MetricKind,
    ) -> None:
        """Write a metric to Cloud Monitoring.

        Args:
            metric_type: Full metric type name
            value: Metric value
            labels: Metric labels
            value_type: Type of value (INT64, DOUBLE, etc.)
            metric_kind: Kind of metric (GAUGE, CUMULATIVE, etc.)
        """
        # Add agent name to labels
        labels["agent_name"] = self.agent_name

        # Create time series
        series = monitoring_v3.TimeSeries()
        series.metric.type = metric_type
        series.metric.labels.update(labels)

        # Set resource
        series.resource.type = "global"
        series.resource.labels["project_id"] = self.project_id

        # Create point
        now = time.time()
        seconds = int(now)
        nanos = int((now - seconds) * 10**9)

        interval = monitoring_v3.TimeInterval({"end_time": {"seconds": seconds, "nanos": nanos}})

        point = monitoring_v3.Point(
            {
                "interval": interval,
                "value": (
                    {"double_value": float(value)}
                    if value_type == ga_metric.MetricDescriptor.ValueType.DOUBLE
                    else {"int64_value": int(value)}
                ),
            }
        )

        series.points = [point]

        # Write time series
        try:
            self.client.create_time_series(name=self.project_name, time_series=[series])
        except Exception as e:
            # Don't fail the agent if metrics fail
            print(f"Warning: Failed to write metric: {e}")
