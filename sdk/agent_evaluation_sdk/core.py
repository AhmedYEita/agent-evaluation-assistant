"""
Core evaluation wrapper for AI agents.

This module provides the main integration point for enabling evaluation
on ADK agents with automatic instrumentation.
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

        # Initialize evaluation components
        self.logger = CloudLogger(
            project_id=config.project_id,
            agent_name=config.agent_name,
            log_level=config.logging.level,
        )

        self.tracer = CloudTracer(
            project_id=config.project_id,
            agent_name=config.agent_name,
            sample_rate=config.tracing.sample_rate,
        )

        self.metrics = CloudMetrics(
            project_id=config.project_id,
            agent_name=config.agent_name,
        )

        self.dataset_collector = DatasetCollector(
            project_id=config.project_id,
            agent_name=config.agent_name,
            sample_rate=config.dataset.sample_rate,
            storage_location=config.dataset.storage_location,
        )

        # Wrap agent methods
        self._wrap_agent()

        print(f"✅ Evaluation enabled for agent: {config.agent_name}")
        print("   - Logging: Cloud Logging")
        print(f"   - Tracing: Cloud Trace (sample rate: {config.tracing.sample_rate})")
        print("   - Metrics: Cloud Monitoring")
        print(f"   - Dataset: {config.dataset.sample_rate * 100}% of interactions")

    def _wrap_agent(self) -> None:
        """Wrap agent methods with evaluation instrumentation."""
        # Store original method
        if hasattr(self.agent, "generate_content"):
            original_method = self.agent.generate_content
            self.agent.generate_content = self._wrap_generate_content(original_method)
        elif hasattr(self.agent, "__call__"):
            original_method = self.agent.__call__
            self.agent.__call__ = self._wrap_generate_content(original_method)
        else:
            print("Warning: Could not find generate_content or __call__ method to wrap")

    def _wrap_generate_content(self, original_method: Callable) -> Callable:
        """Wrap the agent's generate_content method.

        Args:
            original_method: The original method to wrap

        Returns:
            Wrapped method with evaluation instrumentation
        """

        @functools.wraps(original_method)
        def wrapped(*args, **kwargs):
            # Generate interaction ID
            interaction_id = str(uuid.uuid4())

            # Start trace
            trace_id = self.tracer.start_trace()

            # Extract input
            input_data = args[0] if args else kwargs.get("prompt", kwargs.get("input", ""))

            try:
                # Execute with tracing
                with self.tracer.span(
                    name="agent.generate_content",
                    attributes={"interaction_id": interaction_id},
                    trace_id=trace_id,
                ):
                    start_time = time.time()

                    # Call original method
                    response = original_method(*args, **kwargs)

                    # Calculate duration
                    duration_ms = (time.time() - start_time) * 1000

                    # Extract output and metadata
                    output_data = self._extract_output(response)
                    metadata = self._extract_metadata(response)

                    # Log interaction
                    if self.config.logging.include_trajectories:
                        self.logger.log_interaction(
                            interaction_id=interaction_id,
                            input_data=input_data,
                            output_data=output_data,
                            duration_ms=duration_ms,
                            metadata=metadata,
                        )

                    # Record metrics
                    self.metrics.record_latency(duration_ms)
                    self.metrics.record_success()

                    # Extract and record token counts if available
                    if metadata.get("input_tokens") and metadata.get("output_tokens"):
                        self.metrics.record_token_count(
                            input_tokens=metadata["input_tokens"],
                            output_tokens=metadata["output_tokens"],
                        )

                    # Collect for dataset
                    if self.config.dataset.auto_collect:
                        self.dataset_collector.add_interaction(
                            interaction_id=interaction_id,
                            input_data=input_data,
                            output_data=output_data,
                            metadata=metadata,
                        )

                    return response

            except Exception as e:
                # Log error
                duration_ms = (time.time() - start_time) * 1000

                self.logger.log_error(
                    interaction_id=interaction_id,
                    error=e,
                    context={
                        "input": str(input_data)[:500],  # Truncate for logging
                        "duration_ms": duration_ms,
                    },
                )

                # Record error metric
                self.metrics.record_error(
                    error_type=type(e).__name__,
                )

                # Re-raise the exception
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
            Dictionary of metadata
        """
        metadata = {}

        # Try to extract token usage
        if hasattr(response, "usage_metadata"):
            usage = response.usage_metadata
            if hasattr(usage, "prompt_token_count"):
                metadata["input_tokens"] = usage.prompt_token_count
            if hasattr(usage, "candidates_token_count"):
                metadata["output_tokens"] = usage.candidates_token_count
            if hasattr(usage, "total_token_count"):
                metadata["total_tokens"] = usage.total_token_count

        # Try to extract model info
        if hasattr(response, "model"):
            metadata["model"] = response.model

        # Try to extract safety ratings
        if hasattr(response, "candidates"):
            if response.candidates and hasattr(response.candidates[0], "safety_ratings"):
                metadata["safety_ratings"] = [
                    {
                        "category": (
                            rating.category.name
                            if hasattr(rating.category, "name")
                            else str(rating.category)
                        ),
                        "probability": (
                            rating.probability.name
                            if hasattr(rating.probability, "name")
                            else str(rating.probability)
                        ),
                    }
                    for rating in response.candidates[0].safety_ratings
                ]

        return metadata

    def flush(self) -> None:
        """Flush any buffered data (e.g., dataset samples)."""
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

    This is the main entry point for integrating evaluation into your agent.

    Args:
        agent: The ADK agent instance to enable evaluation for
        project_id: GCP project ID
        agent_name: Name for your agent (used in logging/metrics)
        config_path: Optional path to YAML config file

    Returns:
        EvaluationWrapper instance (you can ignore this in most cases)

    Example:
        ```python
        from google.genai.adk import Agent
        from agent_evaluation_sdk import enable_evaluation

        agent = Agent(
            model="gemini-2.0-flash-exp",
            system_instruction="You are a helpful assistant",
        )

        enable_evaluation(
            agent=agent,
            project_id="my-gcp-project",
            agent_name="customer-support-agent"
        )

        # Now use your agent normally - evaluation happens automatically!
        response = agent.generate_content("Hello!")
        ```
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
