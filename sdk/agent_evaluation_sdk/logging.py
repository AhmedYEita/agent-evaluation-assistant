"""
Cloud Logging integration for agent evaluation.
"""

import time
from typing import Any, Dict, Optional

from google.cloud import logging as cloud_logging
from google.cloud.logging_v2 import Resource


class CloudLogger:
    """Wrapper for Cloud Logging with structured logging for agents."""

    def __init__(self, project_id: str, agent_name: str, log_level: str = "INFO"):
        """Initialize Cloud Logger.

        Args:
            project_id: GCP project ID
            agent_name: Name of the agent for log filtering
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.project_id = project_id
        self.agent_name = agent_name
        self.log_level = log_level

        # Initialize Cloud Logging client
        self.client = cloud_logging.Client(project=project_id)
        self.logger = self.client.logger(f"agent-evaluation-{agent_name}")

        # Resource for structured logging
        self.resource = Resource(
            type="generic_task",
            labels={
                "project_id": project_id,
                "agent_name": agent_name,
            }
        )

    def log_interaction(
        self,
        interaction_id: str,
        input_data: Any,
        output_data: Any,
        duration_ms: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a complete agent interaction.

        Args:
            interaction_id: Unique ID for this interaction
            input_data: User input/prompt
            output_data: Agent response
            duration_ms: Time taken in milliseconds
            metadata: Additional metadata (model, tokens, etc.)
        """
        log_entry = {
            "interaction_id": interaction_id,
            "agent_name": self.agent_name,
            "timestamp": time.time(),
            "input": self._serialize(input_data),
            "output": self._serialize(output_data),
            "duration_ms": duration_ms,
            "metadata": metadata or {},
        }

        self.logger.log_struct(
            log_entry,
            resource=self.resource,
            severity="INFO",
        )

    def log_tool_call(
        self,
        interaction_id: str,
        tool_name: str,
        tool_input: Any,
        tool_output: Any,
        duration_ms: float,
    ) -> None:
        """Log a tool/function call within an interaction.

        Args:
            interaction_id: Parent interaction ID
            tool_name: Name of the tool called
            tool_input: Tool input parameters
            tool_output: Tool output/result
            duration_ms: Time taken in milliseconds
        """
        log_entry = {
            "interaction_id": interaction_id,
            "agent_name": self.agent_name,
            "type": "tool_call",
            "timestamp": time.time(),
            "tool_name": tool_name,
            "tool_input": self._serialize(tool_input),
            "tool_output": self._serialize(tool_output),
            "duration_ms": duration_ms,
        }

        self.logger.log_struct(
            log_entry,
            resource=self.resource,
            severity="DEBUG",
        )

    def log_error(
        self,
        interaction_id: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an error that occurred during agent execution.

        Args:
            interaction_id: Interaction ID where error occurred
            error: The exception that was raised
            context: Additional context about the error
        """
        log_entry = {
            "interaction_id": interaction_id,
            "agent_name": self.agent_name,
            "type": "error",
            "timestamp": time.time(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
        }

        self.logger.log_struct(
            log_entry,
            resource=self.resource,
            severity="ERROR",
        )

    def _serialize(self, data: Any) -> Any:
        """Serialize data for logging (handle non-JSON types)."""
        if isinstance(data, (str, int, float, bool, type(None))):
            return data
        elif isinstance(data, (list, tuple)):
            return [self._serialize(item) for item in data]
        elif isinstance(data, dict):
            return {k: self._serialize(v) for k, v in data.items()}
        else:
            # For complex objects, convert to string
            return str(data)

