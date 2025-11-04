"""
Cloud Trace integration for agent evaluation.
"""

import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Optional

from google.cloud.trace_v2 import TraceServiceClient
from google.cloud.trace_v2.types import Span, TruncatableString


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

        # Initialize Cloud Trace client
        self.client = TraceServiceClient()
        self.project_name = f"projects/{project_id}"

        # Current trace context
        self.current_trace_id: Optional[str] = None
        self.current_span_id: Optional[str] = None

    def start_trace(self, trace_id: Optional[str] = None) -> str:
        """Start a new trace.

        Args:
            trace_id: Optional trace ID (generated if not provided)

        Returns:
            The trace ID
        """
        self.current_trace_id = trace_id or self._generate_trace_id()
        return self.current_trace_id

    @contextmanager
    def span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ):
        """Context manager for creating a trace span.

        Args:
            name: Name of the span (e.g., "agent.generate", "tool.search")
            attributes: Additional attributes to attach to span
            trace_id: Trace ID (uses current if not provided)

        Yields:
            Span ID
        """
        # Use provided trace_id or current or create new
        trace_id = trace_id or self.current_trace_id or self.start_trace()
        span_id = self._generate_span_id()

        start_time = time.time()

        try:
            yield span_id
        finally:
            end_time = time.time()
            (end_time - start_time) * 1000

            # Create and send span
            self._create_span(
                trace_id=trace_id,
                span_id=span_id,
                name=name,
                start_time=start_time,
                end_time=end_time,
                attributes=attributes or {},
            )

    def _create_span(
        self,
        trace_id: str,
        span_id: str,
        name: str,
        start_time: float,
        end_time: float,
        attributes: Dict[str, Any],
    ) -> None:
        """Create and send a span to Cloud Trace."""
        # Add agent name to attributes
        attributes["agent_name"] = self.agent_name

        # Convert timestamps to protobuf format
        from google.protobuf.timestamp_pb2 import Timestamp

        start_timestamp = Timestamp()
        start_timestamp.FromSeconds(int(start_time))

        end_timestamp = Timestamp()
        end_timestamp.FromSeconds(int(end_time))

        # Create span
        span = Span(
            name=f"{self.project_name}/traces/{trace_id}/spans/{span_id}",
            span_id=span_id,
            display_name=TruncatableString(value=name),
            start_time=start_timestamp,
            end_time=end_timestamp,
            attributes=Span.Attributes(
                attribute_map={k: self._convert_attribute(v) for k, v in attributes.items()}
            ),
        )

        # Send to Cloud Trace (batch for efficiency in production)
        try:
            # The create_span method expects (name, span) parameters
            self.client.create_span(name=span.name, span=span)  # type: ignore[call-arg]
        except Exception as e:
            # Don't fail the agent if tracing fails
            print(f"Warning: Failed to create span: {e}")

    def _convert_attribute(self, value: Any) -> Any:
        """Convert attribute value to Cloud Trace format."""
        from google.cloud.trace_v2.types import AttributeValue, TruncatableString

        if isinstance(value, str):
            return AttributeValue(string_value=TruncatableString(value=value))
        elif isinstance(value, int):
            return AttributeValue(int_value=value)
        elif isinstance(value, bool):
            return AttributeValue(bool_value=value)
        else:
            return AttributeValue(string_value=TruncatableString(value=str(value)))

    def _generate_trace_id(self) -> str:
        """Generate a unique trace ID."""
        return uuid.uuid4().hex

    def _generate_span_id(self) -> str:
        """Generate a unique span ID."""
        return str(int(time.time() * 1000000))[-16:]  # 16-digit span ID
