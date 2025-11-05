"""
Core evaluation wrapper for Google ADK agents.

Provides automatic instrumentation for logging, tracing, metrics, and dataset collection.
"""

import functools
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Optional

from agent_evaluation_sdk.config import EvaluationConfig
from agent_evaluation_sdk.dataset import DatasetCollector
from agent_evaluation_sdk.logging import CloudLogger
from agent_evaluation_sdk.metrics import CloudMetrics
from agent_evaluation_sdk.tracing import CloudTracer


class EvaluationWrapper:
    """Wraps an ADK agent with evaluation capabilities."""

    def __init__(self, agent: Any, config: EvaluationConfig):
        """Initialize evaluation wrapper.

        Args:
            agent: The ADK agent to wrap
            config: Evaluation configuration
        """
        self.agent = agent
        self.config = config

        # Initialize logger only if enabled
        self.logger = None
        if config.logging.enabled:
            self.logger = CloudLogger(
                project_id=config.project_id,
                agent_name=config.agent_name,
                log_level=config.logging.level,
            )

        # Initialize tracer only if enabled
        self.tracer = None
        if config.tracing.enabled:
            self.tracer = CloudTracer(
                project_id=config.project_id,
                agent_name=config.agent_name,
            )

        # Initialize metrics only if enabled
        self.metrics = None
        if config.metrics.enabled:
            self.metrics = CloudMetrics(
                project_id=config.project_id,
                agent_name=config.agent_name,
            )

        # Initialize dataset collector only if auto_collect is enabled
        self.dataset_collector = None
        if config.dataset.auto_collect:
            self.dataset_collector = DatasetCollector(
                project_id=config.project_id,
                agent_name=config.agent_name,
                storage_location=config.dataset.storage_location,
                buffer_size=config.dataset.buffer_size,
            )

        # Wrap agent methods
        self._wrap_agent()

        print(f"✅ Evaluation enabled for agent: {config.agent_name}")

        if config.logging.enabled:
            print("   - Logging: Cloud Logging initialized")
        else:
            print("   - Logging: Disabled")

        if config.tracing.enabled:
            print("   - Tracing: Cloud Trace initialized")
        else:
            print("   - Tracing: Disabled")

        if config.metrics.enabled:
            print("   - Metrics: Cloud Monitoring initialized")
        else:
            print("   - Metrics: Disabled")

        if config.dataset.auto_collect:
            print("   - Dataset Collection: Enabled")
        else:
            print("   - Dataset Collection: Disabled")

    def _wrap_agent(self) -> None:
        """Replace the ADK agent's generate_content method with the evaluation wrapped version."""
        if not hasattr(self.agent, "generate_content"):
            raise ValueError(
                "Agent must have a 'generate_content' method. "
                "This SDK currently supports Google ADK agents only."
            )

        original_method = self.agent.generate_content
        self.agent.generate_content = self._wrap_generate_content(original_method)

    def _wrap_generate_content(self, original_method: Callable) -> Callable:
        """Wrap the original method with logging, tracing, metrics, and dataset collection.

        Args:
            original_method: The original agent method to wrap

        Returns:
            Wrapped method that adds logging, tracing, metrics, and dataset collection
        """

        @functools.wraps(original_method)
        def wrapped(*args, **kwargs):
            interaction_id = str(uuid.uuid4())
            input_data = args[0] if args else kwargs.get("prompt", kwargs.get("input", ""))
            start_time = time.time()

            # Start trace and execute agent
            try:
                if self.tracer:
                    trace_id = self.tracer.start_trace()
                    with self.tracer.span(
                        name="agent.generate_content",
                        attributes={"interaction_id": interaction_id},
                        trace_id=trace_id,
                    ):
                        response = original_method(*args, **kwargs)
                else:
                    response = original_method(*args, **kwargs)

                # Extract response data
                duration_ms = (time.time() - start_time) * 1000
                output_data = self._extract_output(response)
                metadata = self._extract_metadata(response)

                # Log successful interaction
                if self.logger and self.config.logging.include_trajectories:
                    self.logger.log_interaction(
                        interaction_id=interaction_id,
                        input_data=input_data,
                        output_data=output_data,
                        duration_ms=duration_ms,
                        metadata=metadata,
                    )

                # Record success metrics
                if self.metrics:
                    self.metrics.record_latency(duration_ms)
                    self.metrics.record_success()
                    if metadata.get("input_tokens") and metadata.get("output_tokens"):
                        self.metrics.record_token_count(
                            input_tokens=metadata["input_tokens"],
                            output_tokens=metadata["output_tokens"],
                        )

                # Collect for test dataset
                if self.dataset_collector:
                    self.dataset_collector.add_interaction(
                        interaction_id=interaction_id,
                        input_data=input_data,
                        output_data=output_data,
                        metadata=metadata,
                    )

                return response

            except Exception as e:
                # Log and record error, then re-raise
                duration_ms = (time.time() - start_time) * 1000

                if self.logger:
                    self.logger.log_error(
                        interaction_id=interaction_id,
                        error=e,
                        context={
                            "input": str(input_data)[:500],
                            "duration_ms": duration_ms,
                        },
                    )

                if self.metrics:
                    self.metrics.record_error(error_type=type(e).__name__)

                raise

        return wrapped

    def _extract_output(self, response: Any) -> Any:
        """Extract output from agent response.

        Args:
            response: Agent response object

        Returns:
            Extracted output (text or structured data)
        """
        # Handle different response types
        if isinstance(response, str):
            return response
        elif hasattr(response, "text"):
            return response.text
        elif hasattr(response, "content"):
            return response.content
        elif hasattr(response, "candidates"):
            # ADK/Gemini response format
            if response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "content"):
                    if hasattr(candidate.content, "parts"):
                        return " ".join(
                            part.text for part in candidate.content.parts if hasattr(part, "text")
                        )

        # Fallback: return string representation
        return str(response)

    def _extract_metadata(self, response: Any) -> dict:
        """Extract metadata from agent response.

        Args:
            response: Agent response object

        Returns:
            Dictionary of metadata (token counts, model info)
        """
        metadata = {}

        # Extract token usage (Gemini/ADK response format)
        if hasattr(response, "usage_metadata"):
            usage = response.usage_metadata
            metadata["input_tokens"] = getattr(usage, "prompt_token_count", None)
            metadata["output_tokens"] = getattr(usage, "candidates_token_count", None)
            metadata["total_tokens"] = getattr(usage, "total_token_count", None)

        # Extract model name
        if hasattr(response, "model"):
            metadata["model"] = response.model

        # Remove None values
        return {k: v for k, v in metadata.items() if v is not None}

    def flush(self) -> None:
        """Flush any buffered data (e.g., dataset samples)."""
        if self.dataset_collector:
            self.dataset_collector.flush()

    def __del__(self):
        """Cleanup when wrapper is destroyed."""
        try:
            self.flush()
        except Exception:  # noqa: S110
            pass


def enable_evaluation(
    agent: Any,
    project_id: str,
    agent_name: str,
    config_path: Optional[str] = None,
) -> EvaluationWrapper:
    """Enable evaluation for an ADK agent with a single function call.

    Args:
        agent: The ADK agent instance to enable evaluation for
        project_id: GCP project ID
        agent_name: Name for your agent (used in logging/metrics)
        config_path: Optional path to YAML config file

    Returns:
        EvaluationWrapper instance (you can ignore this in most cases)
    """
    # Load config
    if config_path:
        config = EvaluationConfig.from_yaml(Path(config_path))
        # Override with provided values
        config.project_id = project_id
        config.agent_name = agent_name
    else:
        config = EvaluationConfig.default(project_id=project_id, agent_name=agent_name)

    # Create and return wrapper
    wrapper = EvaluationWrapper(agent=agent, config=config)

    return wrapper
