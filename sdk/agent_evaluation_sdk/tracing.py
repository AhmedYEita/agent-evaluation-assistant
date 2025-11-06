"""
Cloud Trace integration for agent evaluation.
"""

import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Optional

from google.cloud.trace_v2 import TraceServiceClient
from google.cloud.trace_v2.types import AttributeValue, Span, TruncatableString
from google.protobuf.timestamp_pb2 import Timestamp


class CloudTracer:
    """Wrapper for Cloud Trace to track agent performance."""

    def __init__(self, project_id: str, agent_name: str):
        """Initialize Cloud Tracer.

        Args:
            project_id: GCP project ID
            agent_name: Name of the agent
        """
        self.project_id = project_id
        self.agent_name = agent_name
        self.client = TraceServiceClient()
        self.project_name = f"projects/{project_id}"

    def start_trace(self) -> str:
        """Generate and return a new trace ID."""
        return uuid.uuid4().hex

    @contextmanager
    def span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ):
        """Create a trace span that measures execution time.

        Args:
            name: Span name (e.g., "agent.generate_content")
            attributes: Additional metadata to attach
            trace_id: Trace ID (generated if not provided)
            parent_span_id: Parent span ID for nested spans

        Yields:
            Tuple of (trace_id, span_id) for creating child spans
        """
        trace_id = trace_id or self.start_trace()
        span_id = uuid.uuid4().hex[:16]  # 16-character (Google Cloud Trace requirement)
        start_time = time.time()
        error_info = None

        try:
            yield (trace_id, span_id)
        except Exception as e:
            # Capture error info to add to span
            error_info = {
                "error": True,
                "error.type": type(e).__name__,
                "error.message": str(e)[:256],
            }
            raise
        finally:
            # Merge error info into attributes if present
            final_attributes = {**(attributes or {}), **(error_info or {})}
            self._send_span(
                trace_id, span_id, name, start_time, time.time(), final_attributes, parent_span_id
            )

    def _send_span(
        self,
        trace_id: str,
        span_id: str,
        name: str,
        start_time: float,
        end_time: float,
        attributes: Dict[str, Any],
        parent_span_id: Optional[str] = None,
    ) -> None:
        """Send span to Cloud Trace.

        Args:
            trace_id: Trace ID
            span_id: Span ID
            name: Span display name
            start_time: Start timestamp
            end_time: End timestamp
            attributes: Span attributes
            parent_span_id: Parent span ID for nested spans
        """
        try:
            # Add agent name to attributes
            attributes["agent_name"] = self.agent_name

            # Convert timestamps
            start_ts = self._to_timestamp(start_time)
            end_ts = self._to_timestamp(end_time)

            # Create span configuration
            span_config = {
                "name": f"{self.project_name}/traces/{trace_id}/spans/{span_id}",
                "span_id": span_id,
                "display_name": TruncatableString(value=name),
                "start_time": start_ts,
                "end_time": end_ts,
                "attributes": Span.Attributes(
                    attribute_map={k: self._to_attribute(v) for k, v in attributes.items()}
                ),
            }

            # Add parent span ID if provided (for nested spans)
            if parent_span_id:
                span_config["parent_span_id"] = parent_span_id

            # Create and send span
            span = Span(**span_config)
            self.client.create_span(name=span.name, span=span)  # type: ignore[call-arg]

        except Exception as e:
            # Don't fail the agent if tracing fails
            print(f"Warning: Failed to send trace span: {e}")

    def _to_timestamp(self, time_float: float) -> Timestamp:
        """Convert float timestamp to Protobuf Timestamp with nanosecond precision."""
        ts = Timestamp()
        ts.seconds = int(time_float)
        ts.nanos = int((time_float % 1) * 1e9)
        return ts

    def _to_attribute(self, value: Any) -> AttributeValue:
        """Convert Python value to Cloud Trace attribute format."""
        if isinstance(value, bool):
            return AttributeValue(bool_value=value)
        elif isinstance(value, int):
            return AttributeValue(int_value=value)
        else:
            return AttributeValue(string_value=TruncatableString(value=str(value)))
