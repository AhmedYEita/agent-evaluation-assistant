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
        self, name: str, attributes: Optional[Dict[str, Any]] = None, trace_id: Optional[str] = None
    ):
        """Create a trace span that measures execution time.

        Args:
            name: Span name (e.g., "agent.generate_content")
            attributes: Additional metadata to attach
            trace_id: Trace ID (generated if not provided)

        Yields:
            Span ID
        """
        trace_id = trace_id or self.start_trace()
        span_id = str(int(time.time() * 1000000))[-16:]  # 16-digit (Google Cloud Trace requirement)
        start_time = time.time()

        try:
            yield span_id
        finally:
            self._send_span(trace_id, span_id, name, start_time, time.time(), attributes or {})

    def _send_span(
        self,
        trace_id: str,
        span_id: str,
        name: str,
        start_time: float,
        end_time: float,
        attributes: Dict[str, Any],
    ) -> None:
        """Send span to Cloud Trace."""
        try:
            # Add agent name to attributes
            attributes["agent_name"] = self.agent_name

            # Convert timestamps
            start_ts = Timestamp()
            start_ts.FromSeconds(int(start_time))
            end_ts = Timestamp()
            end_ts.FromSeconds(int(end_time))

            # Create and send span
            span = Span(
                name=f"{self.project_name}/traces/{trace_id}/spans/{span_id}",
                span_id=span_id,
                display_name=TruncatableString(value=name),
                start_time=start_ts,
                end_time=end_ts,
                attributes=Span.Attributes(
                    attribute_map={k: self._to_attribute(v) for k, v in attributes.items()}
                ),
            )

            self.client.create_span(name=span.name, span=span)  # type: ignore[call-arg]

        except Exception as e:
            # Don't fail the agent if tracing fails
            print(f"Warning: Failed to send trace span: {e}")

    def _to_attribute(self, value: Any) -> AttributeValue:
        """Convert Python value to Cloud Trace attribute format."""
        if isinstance(value, bool):
            return AttributeValue(bool_value=value)
        elif isinstance(value, int):
            return AttributeValue(int_value=value)
        else:
            return AttributeValue(string_value=TruncatableString(value=str(value)))
